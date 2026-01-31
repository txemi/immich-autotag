import subprocess
import re
from pathlib import Path
from scripts.devtools.quality_gate_py.base import Check

class CheckNoSpanishChars(Check):
    def __init__(self):
        super().__init__('check_no_spanish_chars')

    def check(self, args):
        # Busca palabras y caracteres españoles en todos los .py
        SPANISH_WORDS = [
            'aquellas', 'aquellos', 'antes', 'cambiado', 'cierto', 'claro', 'comentario', 'complicado', 'complejo',
            'compatibilidad', 'correcto', 'devuelve', 'devolviendo', 'durante', 'ejemplo', 'entonces', 'estructura',
            'etiqueta', 'etiquetas', 'falso', 'grande', 'hoy', 'imposible', 'importante', 'improbable', 'inicio',
            'interesante', 'limpieza', 'lista', 'lento', 'luego', 'mantenimiento', 'mayor', 'mejor', 'menos',
            'mientras', 'muy', 'nombre', 'nuevo', 'nueva', 'nuevas', 'nuevos', 'nunca', 'oscuro', 'peor', 'posible',
            'primera', 'primeras', 'primero', 'primeros', 'probable', 'referencia', 'seguro', 'sencillo', 'si',
            'siempre', 'soporta', 'tenemos', 'usamos', 'verdadero', 'vieja', 'viejas', 'viejo', 'viejos'
        ]
        SPANISH_PATTERN = re.compile(r"[áéíóúÁÉÍÓÚñÑüÜ¿¡]|\\b(" + '|'.join(SPANISH_WORDS) + ")\\b", re.IGNORECASE)
        failed = False
        for pyfile in Path(args.target_dir).rglob('*.py'):
            with open(pyfile, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if SPANISH_PATTERN.search(line):
                        print(f"[ERROR] {pyfile}:{i}: {line.strip()}")
                        failed = True
        return 1 if failed else 0

    def apply(self, args):
        # No modifica nada
        return self.check(args)
