from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagResponseWrapper

# todo: Tengo claro cuál es el objetivo de esta clase si el objetivo es tener los campos que van a ir al fichero y debería ser todo string o si el objetivo es tener toda la información de un registro entonces podría ser todo objetos en vez de en vez de strings esto se creó utilizando bike coding por get hat copilot y ahora me parece que hay una especie de mezcla y no tengo claro cuál es la intención de la clase estaría bien pensarlo para hacer lo que tenga más sentido Nación es que hay una función que se dedica a formatear la salida y que esto podría ser un conjunto de objetos que quedaría más claro y robusto pero no me atrevo a decirlo hasta que no lo analicemos





# --- Versión rica: con objetos ---

# --- Versión serializable: solo datos simples ---

# TODO: la siguiente clase es mas generiga que tag, requiere refactorizar nombre y ubicacion


