# Issue Tracking & Design System

This directory is the core of the project's task management, issues, and design decisions. We use a **Local-first** and **Documentation-as-Code** approach to ensure that the technical context is eternal and processable by AI.

## 📚 Standards and Conventions
To avoid "reinventing the wheel", this system is based on the following industry standards:
## 📚 Standards and Conventions
To avoid "reinventing the wheel", this system is based on the following industry standards:

1.  **[ADR (Architecture Decision Records)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):** We follow Michael Nygard's pattern to record technical decisions in a numbered and chronological way.
2.  **[RFC (Request for Comments)](https://github.com/rust-lang/rfcs):** We adopt the workflow of projects like Rust or React, where significant changes are proposed and documented before being implemented.
3.  **[Documentation-as-Code](https://www.writethedocs.org/guide/documentation-as-code/):** We treat documentation with the same rigor as source code (versioned in Git, peer review, and Markdown format).

## 🛠 System Structure
Each task or "issue" resides in its own numbered folder (`XXXX-slug`):
## 🛠 System Structure
Each task or "issue" resides in its own numbered folder (`XXXX-slug`):

- **`index.md`**: The issue's master document. Contains requirements, tech stack (AWS, AI/ML, C++, Python, etc.) and acceptance criteria.
- **`ai-context.md`**: Critical record of LLM interaction. Prompts and reasoning are saved here so that AI-generated knowledge is not lost.
- **`design/`**: Directory for schemas, architecture diagrams (Mermaid/Draw.io) and detailed technical proposals.

## 🚀 AI Workflow (Copilot/Cursor)
To maintain consistency and avoid duplicate IDs, always use this command with your AI assistant:

> *"Based on this directory's protocol, create a new issue for [brief description]. Increment the ID based on the last existing one and update the `registry.md`."*

---
*This system ensures that the project's knowledge is sovereign, does not depend on external SaaS tools, and is optimized for analysis by language models.*

## ⚠️ Performance Regression: Test Suite Duration

Descripción breve (español): hasta hace poco la batería de pruebas completa tardaba ~4 horas y hoy tarda ~14 horas — un aumento inaceptable que hay que investigar.

Pistas iniciales:
- La funcionalidad de **auto-creación de álbumes** podría haber generado una gran cantidad de álbumes nuevos, lo que posiblemente impacte a pasos que iteren sobre álbumes o consulten metadatos repetidamente.
- Otra posibilidad es que alguna parte del código esté haciendo trabajo redundante (llamadas repetidas, recalculos, operaciones O(N^2) inesperadas, o accesos a IO innecesarios dentro de bucles).

Estrategia propuesta:
- Automatizar la generación de perfiles desde CI para capturar muestras reproducibles (CPU, tiempos wall, uso de memoria, flamegraphs). Ver [issue 0021 — Profiling & Performance Reports](../docs/issues/0021-profiling-performance/).
- Empezar con una muestra representativa pequeña para mantener el tiempo de CI razonable y luego escalar localmente para reproducciones más grandes.
- Analizar perfiles para identificar hotspots y llamadas repetidas; priorizar cambios que reduzcan re-trabajo (caching, evitar IO repetido, limitar escaneo de álbumes).

Acciones inmediatas:
1. Integrar un pequeño job de profiling en CI que ejecute un conjunto de tareas representativas y archive los artefactos (CPU/memory profiles, flamegraphs).
2. Proveer scripts en `scripts/profiling/` y un `README` con instrucciones para ejecutar localmente y en CI.
3. Revisar las rutas críticas que operan sobre álbumes y clasificación para buscar operaciones repetidas o consultas costosas.

Si quieres, puedo crear el `scripts/profiling/run_profile.sh` de ejemplo y añadir un job minimal para GitHub Actions o Jenkins que archive los artefactos.