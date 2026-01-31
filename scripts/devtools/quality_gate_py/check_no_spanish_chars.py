import subprocess
import re
from pathlib import Path
from scripts.devtools.quality_gate_py.base import Check

class CheckNoSpanishChars(Check):
    def __init__(self):
        super().__init__('check_no_spanish_chars')

    def check(self, args):
        # Loads forbidden words from the external file (one per line)
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        words_path = os.path.join(script_dir, '../spanish_words.txt')
        with open(words_path, encoding='utf-8') as f:
            SPANISH_WORDS = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        SPANISH_PATTERN = re.compile(r"[áéíóúÁÉÍÓÚñÑüÜ¿¡]|\\b(" + '|'.join(map(re.escape, SPANISH_WORDS)) + ")\\b", re.IGNORECASE)
        failed = False
        for pyfile in Path(args.target_dir).rglob('*.py'):
            # Exclude the spanish_words.txt file from the check
            if os.path.abspath(pyfile) == os.path.abspath(words_path):
                continue
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if SPANISH_PATTERN.search(line):
                        print(f"[ERROR] {pyfile}:{i}: {line.strip()}")
                        failed = True
        return 1 if failed else 0

    def apply(self, args):
        # No modifica nada
        return self.check(args)
