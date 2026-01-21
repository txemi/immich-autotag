#!/usr/bin/env python3
"""Check source files for tuple usage in returns and class members.

This script scans Python files under the given target directory and reports:
 - functions that explicitly `return` a tuple literal (e.g. `return a, b` or `return (a, b)`).
 - functions whose return annotation uses `Tuple`/`tuple` (typing.Tuple or tuple).
 - class-level attributes assigned tuple literals or annotated as Tuple/tuple.
 - `self.attr = (..)` assignments inside `__init__` that set tuple literals on instances.

The goal is to disallow tuple/dupla usage as per the project's style policy.
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple


class TupleUsageVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.issues: List[Tuple[int, str]] = []
        self._in_class = False
        self._current_class_name = None
        self._in_init = False

    def visit_ClassDef(self, node: ast.ClassDef):
        prev_class = self._in_class
        prev_name = self._current_class_name
        self._in_class = True
        self._current_class_name = node.name
        # Check class body for assigns/annassign
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                # e.g., attr: Tuple[int, int]
                if self._is_tuple_annotation(stmt.annotation):
                    self.issues.append((stmt.lineno, f"Class attribute annotation uses Tuple/tuple in class '{node.name}'"))
            elif isinstance(stmt, ast.Assign):
                # e.g., attr = (1, 2)
                if isinstance(stmt.value, ast.Tuple):
                    self.issues.append((stmt.lineno, f"Class attribute assigned a tuple literal in class '{node.name}'"))
        # Visit methods to check __init__ self.attr = tuple
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                self._in_init = True
                self.visit(stmt)
                self._in_init = False
            else:
                # for other methods, still traverse to find returns
                self.visit(stmt)

        self._in_class = prev_class
        self._current_class_name = prev_name

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check return annotation
        if node.returns and self._is_tuple_annotation(node.returns):
            self.issues.append((node.lineno, f"Function '{node.name}' has a Tuple/tuple return annotation"))

        # Walk the body to find Return nodes and assignments
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Tuple):
                    self.issues.append((stmt.lineno, f"Function '{node.name}' returns a tuple literal"))
            elif isinstance(stmt, ast.Assign):
                # detect self.attr = (..)
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        if isinstance(stmt.value, ast.Tuple):
                            self.issues.append((stmt.lineno, f"Instance attribute '{target.attr}' assigned a tuple literal in __init__"))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # same checks as regular functions
        self.visit_FunctionDef(node)  # type: ignore[arg-type]

    def _is_tuple_annotation(self, ann: ast.AST) -> bool:
        # Check patterns like Tuple[...] or tuple or typing.Tuple
        if isinstance(ann, ast.Subscript):
            # e.g., Tuple[int, int]
            value = ann.value
            if isinstance(value, ast.Name) and value.id in ("Tuple", "tuple"):
                return True
            if isinstance(value, ast.Attribute) and getattr(value, "attr", None) in ("Tuple",):
                return True
        elif isinstance(ann, ast.Name) and ann.id in ("Tuple", "tuple"):
            return True
        elif isinstance(ann, ast.Attribute) and getattr(ann, "attr", None) in ("Tuple",):
            return True
        return False


def check_file(path: Path) -> List[Tuple[int, str]]:
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return [(0, f"Could not read file {path}")]
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return [(e.lineno or 0, f"SyntaxError when parsing {path}: {e}")]

    visitor = TupleUsageVisitor(str(path))
    visitor.visit(tree)
    return visitor.issues


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: check_no_tuples.py <target_dir> [--exclude dir1,dir2]")
        return 2
    target = Path(argv[1])
    if not target.exists():
        print(f"Target {target} does not exist")
        return 2

    excludes = set()
    if "--exclude" in argv:
        try:
            i = argv.index("--exclude")
            excludes.update(x.strip() for x in argv[i + 1].split(",") if x.strip())
        except Exception:
            pass

    py_files = list(target.rglob("*.py"))
    issues_found = 0
    for p in py_files:
        if any(part in excludes for part in p.parts):
            continue
        issues = check_file(p)
        for lineno, msg in issues:
            print(f"{p}:{lineno}: {msg}")
            issues_found += 1

    if issues_found > 0:
        print(f"Found {issues_found} tuple-related style issues. Please replace tuples with typed classes/dataclasses or explicit types.")
        return 1
    print("No tuple return/type or class-member tuple issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
