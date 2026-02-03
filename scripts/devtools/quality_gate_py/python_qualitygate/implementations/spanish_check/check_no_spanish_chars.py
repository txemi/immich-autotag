

from typing import List
from python_qualitygate.cli.args import QualityGateArgs
from git import Repo, InvalidGitRepositoryError
from pathlib import Path
from python_qualitygate.core.base import Check
from python_qualitygate.core.result import CheckResult, Finding
import attr
from langdetect import detect, LangDetectException

@attr.define(auto_attribs=True, slots=True)

class CheckNoSpanishChars(Check):
    name = 'check_no_spanish_chars'

    def check(self, args: QualityGateArgs) -> CheckResult:
        findings: List[Finding] = []
        repo, repo_root = self._get_repo_and_root(findings)
        if repo is None or repo_root is None:
            return CheckResult(findings=findings)

        words_path, spanish_words = self._get_spanish_words(repo_root, findings)
        forbidden_bytes = self._get_forbidden_bytes()
        files_to_check = self._get_files_to_check(repo, repo_root)

        for file_path in files_to_check:
            findings.extend(self._analyze_file_wordlist(file_path, forbidden_bytes, spanish_words))
            # Only use langdetect in TARGET mode (compare using enum)
            from python_qualitygate.cli.args import QualityGateLevel
            if args.level == QualityGateLevel.TARGET:
                findings.extend(self._analyze_file_langdetect(file_path))
        return CheckResult(findings=findings)


    def apply(self, args: QualityGateArgs) -> CheckResult:
        return self.check(args)

    def _get_repo_and_root(self, findings: List[Finding]):
        try:
            repo = Repo(Path.cwd(), search_parent_directories=True)
            repo_root = Path(repo.working_tree_dir)
            return repo, repo_root
        except InvalidGitRepositoryError:
            findings.append(Finding(file_path=Path.cwd(), line_number=0, message="No se encontró un repositorio git en el árbol de directorios actual.", code="git-error"))
            return None, None

    def _get_spanish_words(self, repo_root: Path, findings: List[Finding]):
        # Buscar en varias rutas posibles
        candidate_paths = [
            repo_root / 'scripts' / 'spanish_words.txt',
            repo_root / 'scripts' / 'devtools' / 'spanish_words.txt',
        ]
        words_path = None
        spanish_words = []
        for path in candidate_paths:
            if path.exists():
                words_path = path
                break
        if words_path:
            with words_path.open(encoding='utf-8') as f:
                spanish_words = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            findings.append(Finding(file_path=candidate_paths[-1], line_number=0, message="spanish_words.txt not found. Only accents will be checked.", code="warn"))
        return words_path, spanish_words

    def _get_forbidden_bytes(self) -> List[bytes]:
        return [
            b'\xc3\xa1', b'\xc3\xa9', b'\xc3\xad', b'\xc3\xb3', b'\xc3\xba', # á é í ó ú
            b'\xc3\x81', b'\xc3\x89', b'\xc3\x8d', b'\xc3\x93', b'\xc3\x9a', # Á É Í Ó Ú
            b'\xc3\xb1', b'\xc3\x91', # ñ Ñ
            b'\xc3\xbc', b'\xc3\x9c', # ü Ü
            b'\xc2\xbf', b'\xc2\xa1'  # ¿ ¡
        ]

    def _get_files_to_check(self, repo, repo_root: Path) -> List[Path]:
        files = [repo_root / Path(f) for f in repo.git.ls_files().splitlines()]
        # Solo excluir el propio check y spanish_words.txt
        return [f for f in files if not str(f).endswith('spanish_words.txt') and not str(f).endswith('check_no_spanish_chars.py')]


    def _analyze_file_wordlist(self, file_path: Path, forbidden_bytes: List[bytes], spanish_words: List[str]) -> List[Finding]:
        """
        Detect Spanish by forbidden bytes and wordlist (legacy method).
        """
        findings: List[Finding] = []
        EXCLUDE_PATTERNS = [
            'SPANISH_PATTERN=',
        ]
        EXCLUDE_FILES = [
            'check_no_spanish_chars.py',
        ]
        try:
            with file_path.open('rb') as f:
                for i, line in enumerate(f, 1):
                    try:
                        decoded_line = line.decode('utf-8', errors='ignore')
                    except Exception:
                        decoded_line = ''
                    if any(pat in decoded_line for pat in EXCLUDE_PATTERNS):
                        continue
                    if any(str(file_path).endswith(f) for f in EXCLUDE_FILES):
                        continue
                    findings.extend(self._find_spanish_chars(file_path, i, line, forbidden_bytes))
                    findings.extend(self._find_spanish_words(file_path, i, line, spanish_words))
        except Exception as e:
            findings.append(Finding(file_path=file_path, line_number=0, message=f"Could not analyze: {e}", code="file-error"))
        return findings

    def _analyze_file_langdetect(self, file_path: Path) -> List[Finding]:
        """
        Detect Spanish using langdetect library (modern method).
        """
        findings: List[Finding] = []
        try:
            with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    text = line.strip()
                    if text:
                        try:
                            lang = detect(text)
                            if lang == 'es':
                                findings.append(Finding(file_path=file_path, line_number=i, message=f"Detected Spanish (langdetect): {text}", code="spanish-langdetect"))
                        except LangDetectException:
                            continue
        except Exception as e:
            findings.append(Finding(file_path=file_path, line_number=0, message=f"Could not analyze (langdetect): {e}", code="file-error"))
        return findings

    def _find_spanish_chars(self, file_path: Path, line_number: int, line: bytes, forbidden_bytes: List[bytes]) -> List[Finding]:
        findings = []
        # Marca cualquier línea que contenga al menos un byte prohibido (carácter acentuado, ñ, etc.)
        if any(b in line for b in forbidden_bytes):
            try:
                decoded = line.decode('utf-8', errors='ignore').strip()
            except Exception:
                decoded = str(line)
            findings.append(Finding(file_path=file_path, line_number=line_number, message=decoded, code="spanish-char"))
        return findings

    def _find_spanish_words(self, file_path: Path, line_number: int, line: bytes, spanish_words: List[str]) -> List[Finding]:
        import re
        findings = []
        if spanish_words:
            try:
                decoded_line = line.decode('utf-8', errors='ignore')
            except Exception:
                return findings
            for word in spanish_words:
                if word:
                    # Solo marcar si es palabra completa (no subcadena)
                    pattern = r'\b' + re.escape(word) + r'\b'
                    if re.search(pattern, decoded_line, re.IGNORECASE):
                        findings.append(Finding(file_path=file_path, line_number=line_number, message=f"{decoded_line.strip()} (palabra prohibida: {word})", code="spanish-word"))
        return findings
