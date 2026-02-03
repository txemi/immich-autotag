# Import-Linter Configuration - Quality Levels

Este documento describe los niveles de calidad y las reglas de arquitectura que se aplican con import-linter en este proyecto. Cada nivel define qué contratos se aplican y cómo se refuerzan los límites entre módulos.

## Niveles de calidad

### STANDARD (CI/CD)
- Solo logging_proxy puede acceder a immich_proxy
- Solo immich_proxy puede acceder a immich_client

### TARGET (Release)
- Incluye las reglas STANDARD
- Añade reglas de aislamiento entre módulos (más estrictas)

### STRICT (Futuro)
- Máxima restricción, incluye todo lo anterior y posibles reglas futuras

## Propósito
- STANDARD: feedback rápido y evitar violaciones graves
- TARGET: validación de arquitectura para releases
- STRICT: experimentación y mejora continua

## Estado actual
- Todos los contratos STANDARD pasan
- TARGET y STRICT pueden tener reglas rotas en desarrollo

---

(Contenido movido desde docs/dev/import-linter-levels.md)
