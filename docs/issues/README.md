# Issue Tracking & Design System

Este directorio es el núcleo de la gestión de tareas, incidencias y decisiones de diseño del proyecto. Utilizamos un enfoque **Local-first** y **Documentation-as-Code** para garantizar que el contexto técnico sea eterno y procesable por IA.

## 📚 Estándares y Convenciones
Para evitar "reinventar la rueda", este sistema se basa en los siguientes estándares de la industria:

1.  **[ADR (Architecture Decision Records)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):** Seguimos el patrón de Michael Nygard para registrar decisiones técnicas de forma numerada y cronológica.
2.  **[RFC (Request for Comments)](https://github.com/rust-lang/rfcs):** Adoptamos el flujo de trabajo de proyectos como Rust o React, donde los cambios significativos se proponen y documentan antes de ser implementados.
3.  **[Documentation-as-Code](https://www.writethedocs.org/guide/documentation-as-code/):** Tratamos la documentación con el mismo rigor que el código fuente (versionado en Git, revisión por pares y formato Markdown).

## 🛠 Estructura del Sistema
Cada tarea o "issue" reside en su propia carpeta numerada (`XXXX-slug`):

- **`index.md`**: El documento maestro del issue. Contiene requisitos, stack tecnológico (AWS, IA/ML, C++, Python, etc.) y criterios de aceptación.
- **`ai-context.md`**: Registro crítico de la interacción con LLMs. Aquí se guardan los prompts y razonamientos para que el conocimiento generado por la IA no se pierda.
- **`design/`**: Directorio para esquemas, diagramas de arquitectura (Mermaid/Draw.io) y propuestas técnicas detalladas.

## 🚀 Flujo de Trabajo con IA (Copilot/Cursor)
Para mantener la consistencia y evitar duplicidad de IDs, utiliza siempre este comando con tu asistente de IA:

> *"Basándote en el protocolo de este directorio, crea un nuevo issue para [breve descripción]. Incrementa el ID basándote en el último existente y actualiza el `registry.md`."*

---
*Este sistema asegura que el conocimiento del proyecto sea soberano, no dependa de herramientas SaaS externas y esté optimizado para el análisis mediante modelos de lenguaje.*