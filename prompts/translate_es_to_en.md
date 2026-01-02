# Prompt: Traducción automática de español a inglés en el proyecto

## Objetivo
Este prompt está diseñado para que un modelo de lenguaje (LLM) escanee todo el proyecto y traduzca automáticamente cualquier texto, comentario, string, documentación o mensaje que esté en español al inglés.

## Instrucciones para el modelo

1. Recorre todos los archivos del proyecto, incluyendo código fuente, documentación y scripts.
2. Identifica cualquier texto, comentario, string, mensaje de log, documentación o contenido que esté en español.
3. Traduce cada fragmento detectado al inglés, manteniendo el contexto y el significado original.
4. Devuelve el resultado en el mismo formato y ubicación, pero con el texto traducido al inglés.
5. No modifiques el código funcional, solo el contenido textual.
6. Si encuentras ambigüedades, traduce de la forma más neutra y profesional posible.

## Ejemplo de uso
- Comentarios en código
- Mensajes de log
- Documentación en Markdown
- Strings en scripts

---

**Prompt para el modelo:**

"Scan the entire project for any text, comments, strings, documentation, or log messages written in Spanish. Automatically translate all detected content to English, preserving the original context and meaning. Do not modify functional code, only textual content. Return the result in the same format and location, with the translated text. If you find ambiguities, translate in the most neutral and professional way possible."
