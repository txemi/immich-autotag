import re
from pathlib import Path
from typing import Any
import attr
from python_qualitygate.core.base import Check

@attr.define(auto_attribs=True, slots=True)
class CheckNoSpanishChars(Check):
    name: str = 'check_no_spanish_chars'

    def check(self, args: Any) -> int:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        words_path = os.path.join(script_dir, '../spanish_words.txt')
        with open(words_path, encoding='utf-8') as f:
            SPANISH_WORDS = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        SPANISH_PATTERN = re.compile(
            r"[\u00e1\u00e9\u00ed\u00f3\u00fa\u00c1\u00c9\u00cd\u00d3\u00da\u00f1\u00d1\u00fc\u00dc\u00bf\u00a1]"
            r"|\\b(" + '|'.join(map(re.escape, SPANISH_WORDS)) + ")\\b",
            re.IGNORECASE
        )
        failed = False
        for pyfile in Path(args.target_dir).rglob('*.py'):
            if os.path.abspath(pyfile) == os.path.abspath(words_path):
                continue
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if SPANISH_PATTERN.search(line):
                        print(f"[ERROR] {pyfile}:{i}: {line.strip()}")
                        failed = True
        return 1 if failed else 0

    def apply(self, args: Any) -> int:
        return self.check(args)
