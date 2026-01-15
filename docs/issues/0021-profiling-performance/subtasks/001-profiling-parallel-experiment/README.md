# Subtarea 001 — Experimento paralelo de profiling

Propósito
- Documentar y ejecutar un experimento controlado para entender por qué el tiempo de ejecución de la batería de pruebas ha crecido (ej. 4 h → 14–15 h).
- Tener un espacio ordenado para guardar snapshots (logs, perfiles pstats, outputs de `run_app.sh`) capturados en momentos clave y facilitar su análisis comparativo.

Resumen del experimento propuesto
1. Ejecutar un primer trabajo (Job A) con profiling habilitado.
2. Esperar ~1 hora desde el inicio para recoger un snapshot (logs, estimate/processed counters, profile.stats, métricas del sistema).
3. Lanzar un segundo trabajo (Job B) **en paralelo** a Job A.
4. Esperar otra hora y recoger un segundo snapshot (para Job A y para Job B), comparar estimaciones y perfiles.
5. Repetir si es necesario o ampliar ventanas si los números son ruidosos.

Motivación y razonamiento
- Las estimaciones mostradas por la aplicación ("% processed / Avg / Elapsed / Est. remaining") pueden estabilizarse después de un tiempo inicial; tomar una sola medida al inicio puede ser engañoso.
- Al comparar una ejecución sola vs. dos ejecuciones en paralelo podemos detectar:
  - Si el empeoramiento se debe a interferencia/recursos (CPU, I/O, contención de DB/API).
  - Si hay degradación por acumulación de artefactos (p. ej. creación masiva de álbumes) que solo se hace visible pasado cierto % de procesado.

Estructura de la carpeta (plantilla)
- `docs/issues/0021-profiling-performance/subtasks/001-profiling-parallel-experiment/`
  - `README.md` (este fichero)
  - `snapshots/` (subcarpeta donde se almacenan ficheros locales que compartas o referencias)
    - `jobA_t0_log.txt` — log completo de la ejecución de Job A al primer snapshot (texto)
    - `jobA_t0_profile.stats` — pstats (cProfile) generado hasta t0
    - `jobA_t0_sys.txt` — salida de comandos sistema en t0 (`top -b -n1`, `vmstat 1 5`, `iostat -x 1 5` si está disponible)
    - `jobA_t1_log.txt`, `jobA_t1_profile.stats`, `jobA_t1_sys.txt` — segundo snapshot
    - `jobB_t0_log.txt`, `jobB_t0_profile.stats`, `jobB_t0_sys.txt` — (si corresponde)
    - `notes.md` — observaciones manuales (hora de inicio, branch, commit, nodo Jenkins, carga de la máquina)
  - `analysis/` (se añadirá al producirse el análisis)
    - `report.md` — informe con resumen ejecutivo, comparativa y recomendaciones

Formato mínimo de snapshot
- Logs: fichero de texto completo; si son demasiado grandes, recorta pero conserva las secciones:
  - Cabecera con commit SHA, branch y hora
  - Líneas de progreso ("[PERF] 76255/270798 ...")
  - Tracebacks completos si aparecen
- Perfil: `profile.stats` (archivo pstats desde cProfile). Si usas py-spy o flamegraph, guarda `pyspy.svg`/`flamegraph.svg` también.
- Sistema: texto con `top -b -n1`, `vmstat 1 5`, `free -h`, `df -h`, y `iostat -x 1 5` si está disponible.

Comandos útiles para capturar (ejemplos)
- Generar pstats desde `run_app.sh` si ya se usa `profile_run.sh` (ya implementado en repo): el script debe producir `profile.stats` en `logs_local/profiling/<TIMESTAMP>/`.
- Comandos para snapshot de sistema (desde la máquina donde corre Jenkins/worker):
```bash
# snapshot básico
top -b -n1 > jobA_t0_top.txt
vmstat 1 5 > jobA_t0_vmstat.txt
free -h > jobA_t0_free.txt
uptime >> jobA_t0_uptime.txt
```
- Extraer líneas de progreso/estimación del log (ejemplo):
```bash
grep '^\[PERF\]' logs_local/.../immich_autotag_full_output.log > jobA_t0_perf_lines.txt
```

Plantilla de metadata (añadir en `notes.md`)
- `job`: JobA / JobB
- `start_time_utc`:
- `snapshot_time_utc`:
- `branch` / `commit`:
- `jenkins_node`:
- `profile_file`:
- `estimate_at_snapshot` (línea exacta del log):
- `processed_count_at_snapshot`:
- `total_assets`:
- `concurrent_jobs_on_node` (si lo sabes):

Privacidad / sensibilidad
- Si los logs contienen PII o URLs privadas, no subas los ficheros completos. En su lugar:
  - Redacta `user ids`, `email addresses`, `asset URLs` — reemplázalos por tokens `USER_123`.
  - Conserva las líneas de progreso, estimaciones y tracebacks intactas.
- Alternativa: subir los ficheros a un canal privado (S3/drive privado) y compartir conmigo los paths/IDs. Aquí dejaré referencias a los nombres de fichero que debes copiar allí.

Criterios de éxito del experimento
- Obtendremos perfiles comparables (pstats) y métricas sistema en dos momentos (t0, t1) para Job A y, si procede, Job B.
- El análisis deberá responder a preguntas como:
  - ¿La degradación de la estimación se confirma entre t0 y t1? (cuánto cambia la ETA relativa y absoluta)
  - ¿Aparecen hotspots en el perfil que expliquen la mayor CPU por asset?
  - ¿Se observa contención en I/O, swap o CPU por concurrencia?

Proceso operativo propuesto (pasos concretos)
1. Yo documento este plan (hecho) y preparo la carpeta plantilla.
2. Tú ejecutas Job A normalmente y, tras ~1 hora, me pasas (o subes) los ficheros indicados en `snapshots/jobA_t0_*` y la `notes.md` con metadata.
3. Arrancas Job B en paralelo.
4. Tras ~1 hora más, recoges `jobA_t1_*` y `jobB_t1_*` (o los que correspondan) y me los pasas.
5. Yo analizo los pstats y logs, produzco `analysis/report.md` con hallazgos y recomendaciones.

Sugerencias técnicas rápidas
- Si el tamaño de `profile.stats` es grande, comprímelo (`gzip`) antes de compartir.
- Si no puedes generar pstats, captura al menos los logs de progreso y `top`/`vmstat` en los momentos indicados.

Checklist rápida para cuando prepares snapshot (copiar en `notes.md`)
- [ ] Hora UTC del snapshot
- [ ] Commit / branch que se está ejecutando
- [ ] Ficheros generados: listados (log, pstats, top, vmstat)
- [ ] Redacciones realizadas (si hubo PII)
- [ ] Nodo Jenkins / identificador de la máquina

Contacto y siguientes pasos
- Cuando tengas el primer snapshot (t0) súbelo o indícame dónde está y lo analizaré. Si prefieres que espere a t1 para recibir ambos, dime y espero.

---

Si estás de acuerdo con este plan, confirmamelo y crearé la estructura en el repo (esta carpeta ya se ha creado localmente); a continuación dime cómo vas a compartir los archivos (directo en el repo, S3 privado, o por otro medio) y el horario aproximado (hora UTC) para la primera captura y yo estaré listo para analizar.
