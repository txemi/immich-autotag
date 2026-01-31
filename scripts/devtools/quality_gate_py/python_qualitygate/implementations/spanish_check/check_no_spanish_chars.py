"""
Check para detectar caracteres y palabras españolas en archivos rastreados por git.
"""
from python_qualitygate.core.check import Check

class CheckNoSpanishChars(Check):
    def check(self, args: object) -> int:
        import os
        from git import Repo, InvalidGitRepositoryError
        # Detecta la raíz del repo git desde cualquier subcarpeta
        repo = None
        repo_root = None
        try:
            repo = Repo(os.getcwd(), search_parent_directories=True)
            repo_root = repo.working_tree_dir
        except InvalidGitRepositoryError:
            print("[ERROR] No se encontró un repositorio git en el árbol de directorios actual.")
            return 1

        words_path = os.path.join(repo_root, 'scripts', 'spanish_words.txt')
        SPANISH_WORDS = []
        if os.path.exists(words_path):
            with open(words_path, encoding='utf-8') as f:
                SPANISH_WORDS = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            print(f"[WARN] spanish_words.txt not found at {words_path}. Only accents will be checked.")

        # Lista de bytes de acentos/caracteres españoles
        forbidden_bytes = [
            b'\xc3\xa1', b'\xc3\xa9', b'\xc3\xad', b'\xc3\xb3', b'\xc3\xba', # á é í ó ú
            b'\xc3\x81', b'\xc3\x89', b'\xc3\x8d', b'\xc3\x93', b'\xc3\x9a', # Á É Í Ó Ú
            b'\xc3\xb1', b'\xc3\x91', # ñ Ñ
            b'\xc3\xbc', b'\xc3\x9c', # ü Ü
            b'\xc2\xbf', b'\xc2\xa1'  # ¿ ¡
        ]

        # Usar GitPython para obtener archivos rastreados por git
        files_to_check = [os.path.join(repo_root, f) for f in repo.git.ls_files().splitlines()]
        # Excluir spanish_words.txt y este script
        files_to_check = [f for f in files_to_check if not f.endswith('spanish_words.txt') and not f.endswith('check_no_spanish_chars.py')]

        failed = False
        for file_path in files_to_check:
            try:
                with open(file_path, 'rb') as f:
                    for i, line in enumerate(f, 1):
                        # Busca acentos por bytes
                        if any(b in line for b in forbidden_bytes):
                            print(f"[ERROR] {file_path}:{i}: {line.decode(errors='ignore').strip()}")
                            failed = True
                        # Busca palabras prohibidas si hay lista
                        if SPANISH_WORDS:
                            try:
                                decoded_line = line.decode('utf-8', errors='ignore')
                            except Exception:
                                continue
                            for word in SPANISH_WORDS:
                                if word and word.lower() in decoded_line.lower():
                                    print(f"[ERROR] {file_path}:{i}: {decoded_line.strip()} (palabra prohibida: {word})")
                                    failed = True
            except Exception as e:
                print(f"[WARN] No se pudo analizar {file_path}: {e}")
        return 1 if failed else 0
