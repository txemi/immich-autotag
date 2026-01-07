
# Prompt: Automatic Spanish to English Translation in the Project

## Objective
This prompt is designed for a language model (LLM) to scan the entire project and automatically translate any text, comment, string, documentation, or message written in Spanish into English.

## Instructions for the model

1. Scan all files in the project, including source code, documentation, and scripts.
2. Identify any text, comment, string, log message, documentation, or content written in Spanish.
3. Translate each detected fragment into English, preserving the original context and meaning.
4. Return the result in the same format and location, but with the text translated into English.
5. Do not modify functional code, only textual content.
6. If you find ambiguities, translate in the most neutral and professional way possible.

## Example use cases
- Code comments
- Log messages
- Markdown documentation
- Strings in scripts

---

**Prompt for the model:**

"Scan the entire project for any text, comments, strings, documentation, or log messages written in Spanish. Automatically translate all detected content to English, preserving the original context and meaning. Do not modify functional code, only textual content. Return the result in the same format and location, with the translated text. If you find ambiguities, translate in the most neutral and professional way possible."
