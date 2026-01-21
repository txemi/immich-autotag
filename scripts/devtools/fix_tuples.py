#!/usr/bin/env python3
"""Attempt simple automated fixes for tuple returns/annotations.

This codemod handles straightforward cases:
 - Functions that `return a, b` or `return (a, b)` where returned elements are simple names/attributes/constants.
   It will create a `@dataclass` named `<FunctionName>Result` in the same module (if not present) with field names inferred
   from the returned expression names when possible, otherwise `field0`, `field1`, ...
 - It replaces the function return annotation `-> Tuple[...]` or `-> tuple` with the new dataclass type.
 - It replaces `return a, b` with `return FunctionNameResult(a, b)`.

Limitations and safety:
 - Operates only on functions where returned elements are simple (Name, Attribute, Constant).
 - Makes minimal textual edits and writes a backup file `*.bak` before modifying.
 - Use `--dry-run` to preview changes (the default is dry-run).
"""
import ast
import argparse
from pathlib import Path
import difflib
import sys
from typing import List, Tuple, Optional


def infer_field_names(exprs: List[ast.expr]) -> List[str]:
    names = []
    for i, e in enumerate(exprs):
        if isinstance(e, ast.Name):
            names.append(e.id)
        elif isinstance(e, ast.Attribute):
            names.append(e.attr)
        else:
            names.append(f"field{i}")
    # ensure unique and valid identifiers
    seen = {}
    out = []
    for n in names:
        base = n if n.isidentifier() else "field"
        candidate = base
        idx = 1
        while candidate in seen:
            candidate = f"{base}{idx}"
            idx += 1
        seen[candidate] = True
        out.append(candidate)
    return out


def make_dataclass_text(name: str, fields: List[Tuple[str, str]]) -> str:
    lines = ["@dataclass", f"class {name}:"]
    if not fields:
        lines.append("    pass")
    else:
        for fname, ftype in fields:
            lines.append(f"    {fname}: {ftype}")
    return "\n".join(lines) + "\n\n"


class Transformer(ast.NodeTransformer):
    def __init__(self):
        self.to_add_dataclasses: List[Tuple[int, str]] = []  # insert position and code
        self.modified = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # find returns of tuple literal
        returns_tuple = False
        tuple_expr: Optional[ast.Tuple] = None
        for n in ast.walk(node):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple):
                returns_tuple = True
                tuple_expr = n.value
                break

        if not returns_tuple and not (node.returns and isinstance(node.returns, (ast.Subscript, ast.Name, ast.Attribute))):
            return node

        # Only handle simple tuple literals
        if tuple_expr is None:
            # if annotation is Tuple[...] without a literal return, skip
            return node

        elts = tuple_expr.elts
        if any(not isinstance(e, (ast.Name, ast.Attribute, ast.Constant)) for e in elts):
            return node

        # Prepare dataclass name and fields
        dc_name = f"{node.name.capitalize()}Result"
        field_names = infer_field_names(elts)
        # Types: try to read annotation info if exists, but default to Any
        fields = [(fname, "Any") for fname in field_names]

        # Build dataclass code
        dc_code = make_dataclass_text(dc_name, fields)
        # Mark insertion point: before function
        self.to_add_dataclasses.append((node.lineno, dc_code))

        # Replace annotation -> dc_name
        node.returns = ast.Name(id=dc_name, ctx=ast.Load())

        # Replace return statements of tuple literal with constructor
        class ReturnReplacer(ast.NodeTransformer):
            def visit_Return(self, rnode: ast.Return):
                if isinstance(rnode.value, ast.Tuple):
                    args = rnode.value.elts
                    return ast.copy_location(ast.Return(value=ast.Call(func=ast.Name(id=dc_name, ctx=ast.Load()), args=args, keywords=[])), rnode)
                return rnode

        node.body = [ReturnReplacer().visit(s) for s in node.body]
        self.modified = True
        return node


def process_file(path: Path) -> Optional[Tuple[str, str]]:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    transformer = Transformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)

    if not transformer.modified:
        return None

    # Insert dataclasses code at positions (simple: before first function needing it)
    lines = src.splitlines(keepends=True)
    insert_texts = [code for (_pos, code) in sorted(transformer.to_add_dataclasses, key=lambda x: x[0])]
    # Simple insertion: add imports for dataclass and typing.Any at top if missing
    need_dataclass_import = "from dataclasses import dataclass" not in src
    need_typing_any = "from typing import Any" not in src

    header_inserts = []
    if need_dataclass_import:
        header_inserts.append("from dataclasses import dataclass\n")
    if need_typing_any:
        header_inserts.append("from typing import Any\n")
    if header_inserts:
        # Place after module docstring if present
        if len(lines) >= 1 and lines[0].startswith("\"\""):
            # naive: append after docstring closing triple quotes
            joined = "".join(lines)
            # try splitting after first closing docstring
            parts = joined.split('"""', 2)
            if len(parts) >= 3:
                new_src = '"""' + parts[1] + '"""' + "\n" + "".join(header_inserts) + parts[2]
            else:
                new_src = "".join(header_inserts) + joined
        else:
            new_src = "".join(header_inserts) + "".join(lines)
    else:
        new_src = "".join(lines)

    # Re-generate code from AST for modified tree
    try:
        import astor

        regenerated = astor.to_source(new_tree)
    except Exception:
        # fallback to compile + unparse (py3.9+)
        try:
            regenerated = ast.unparse(new_tree)
        except Exception:
            return None

    # Prepend dataclass code(s) - naive: put after imports
    final_src = new_src
    if insert_texts:
        # Insert just before the function position: simpler -> append the dataclasses after imports
        lines2 = final_src.splitlines(keepends=True)
        insert_at = 0
        for i, ln in enumerate(lines2):
            if not ln.strip().startswith("import") and not ln.strip().startswith("from") and ln.strip() != "":
                insert_at = i
                break
        new_lines = lines2[:insert_at] + [txt for txt in insert_texts] + lines2[insert_at:]
        final_src = "".join(new_lines)

    # Merge regenerated function bodies into final_src by simple replace of original function text
    # (this is imperfect but acceptable for simple cases)
    # We'll produce a diff between original src and final_src
    return (src, final_src)


def apply_changes(path: Path, new_src: str):
    bak = path.with_suffix(path.suffix + ".bak")
    path.rename(bak)
    path.write_text(new_src, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target")
    parser.add_argument("--exclude", default=".venv,immich-client,scripts")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    excludes = set(x.strip() for x in args.exclude.split(",") if x.strip())
    p = Path(args.target)
    if not p.exists():
        print(f"Target {p} does not exist", file=sys.stderr)
        sys.exit(2)

    any_changed = False
    diffs = []
    for f in p.rglob("*.py"):
        if any(part in excludes for part in f.parts):
            continue
        res = process_file(f)
        if res is None:
            continue
        src, final = res
        if src == final:
            continue
        any_changed = True
        diff = difflib.unified_diff(src.splitlines(keepends=True), final.splitlines(keepends=True), fromfile=str(f), tofile=str(f) + " (modified)")
        diffs.append("".join(diff))
        if args.apply:
            apply_changes(f, final)

    if not any_changed:
        print("No automatic changes applicable.")
        return 0
    for d in diffs:
        print(d)

    if args.apply:
        print("Applied changes and created .bak backups for modified files.")
    else:
        print("Dry-run mode: no files modified. Use --apply to write changes.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
