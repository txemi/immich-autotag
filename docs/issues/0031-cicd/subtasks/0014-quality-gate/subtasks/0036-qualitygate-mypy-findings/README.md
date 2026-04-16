Título: QualityGate (mypy) — 5 findings bloqueando pipeline

Resumen
- Jenkins está fallando la fase `Quality Gate (Python OO)` en el chequeo `check_mypy` con 5 hallazgos. Local funciona (la app arranca), pero el Quality Gate del CI detecta errores de tipado que bloquean el pipeline.

Errores observados (extraído del log de Jenkins)

  1. immich_autotag/albums/album/album_user_wrapper.py:43: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  2. immich_autotag/albums/album/album_dto_state.py:195: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  3. immich_autotag/albums/album/album_dto_state.py:236: "AlbumResponseDto" has no attribute "assets" [attr-defined]
  4. immich_autotag/users/user_response_wrapper.py:64: Argument 1 to "from_string" of "BaseUUIDWrapper" has incompatible type "UUID"; expected "str" [arg-type]
  5. immich_autotag/users/user_response_wrapper.py:72: Incompatible return value type (got "str | UUID", expected "str") [return-value]

Contexto y observaciones
- El fallo aparece en el paso `check_mypy` del script `scripts/devtools/quality_gate_py/venv_launcher.sh`.
- El pipeline activa `./.venv` y ejecuta los checks; los paquetes de desarrollo parecen instalados correctamente.
- Estos errores son problemas de tipos estáticos (mypy) — no excepciones de importación — y provienen de incompatibilidades entre los tipos usados y las firmas esperadas.

Archivos a inspeccionar (líneas indicadas)
- `immich_autotag/albums/album/album_user_wrapper.py` (línea ~43)
- `immich_autotag/albums/album/album_dto_state.py` (líneas ~195, ~236)
- `immich_autotag/users/user_response_wrapper.py` (líneas ~64, ~72)

Pasos para reproducir localmente (recomendado)
1. Activar el venv de proyecto:

```bash
source .venv/bin/activate
```

2. Ejecutar solo el chequeo mypy (desde la raíz del repo):

```bash
# usando el launcher del proyecto (recomendado)
bash scripts/devtools/quality_gate_py/venv_launcher.sh --mode CHECK --only-check=check_mypy

# o ejecutar mypy directamente (si hay config):
.venv/bin/python -m mypy immich_autotag
```

3. Revisar los archivos y las líneas reportadas por mypy.

Posibles causas y acciones sugeridas
- Causa probable: firmas de helpers (`BaseUUIDWrapper.from_string`) y usos reales no coinciden — p.ej. pasar `UUID` donde se espera `str`.
- Verificar definiciones de `BaseUUIDWrapper.from_string` (tipo de parámetro) y adaptar llamadas o la firma para aceptar `UUID` o `str | UUID`.
- En el caso de `AlbumResponseDto.assets` — comprobar el DTO generado/definición: tal vez falta el atributo en el tipo declarado o hay una condición donde sólo está presente dinámicamente; en ese caso anotar con `# type: ignore[attr-defined]` o ajustar el tipo del DTO.

Mitigaciones temporales
- Si se necesita desbloquear CI mientras se corrige la raíz, permitir que `check_mypy` no bloquee la pipeline para ramas de integración (no recomendado a largo plazo). Alternativa: excluir archivos concretos con `# type: ignore` o actualizar la configuración mypy para aceptar estos casos.

Siguientes pasos propuestos (priorizados)
1. Reproducir localmente `check_mypy` y copiar salida completa.
2. Abrir PR con correcciones de tipado en los archivos listados (preferible) o aplicar `# type: ignore` en los puntos justificados.
3. Re-evaluar reglas del Quality Gate si los falsos positivos persisten.

Adjuntos / logs
- Copiar aquí el trozo de log seleccionado (ya incluido en este README). Añadir más trazas si es necesario.

Asignación
- Dejar sin asignar; asignar a quien haga triage del CI/mypy o a la persona que conozca el submódulo de `albums`/`users`.

Notas
- Si confirmas, puedo: (A) generar PR con cambios de tipo mínimos propuestos, o (B) añadir pasos de instrumentación al job de Jenkins para obtener más información (por ejemplo, imprimir `mypy --version`, `which python`, y la salida completa de mypy).