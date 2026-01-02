from __future__ import annotations

import datetime
from typing import Any, Optional, TYPE_CHECKING
from urllib.parse import ParseResult
from uuid import UUID

import attrs

from immich_autotag.tags.modification_kind import ModificationKind
from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.users.user_response_wrapper import UserResponseWrapper
if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagResponseWrapper
from typing import Any

# todo: Tengo claro cuál es el objetivo de esta clase si el objetivo es tener los campos que van a ir al fichero y debería ser todo string o si el objetivo es tener toda la información de un registro entonces podría ser todo objetos en vez de en vez de strings esto se creó utilizando bike coding por get hat copilot y ahora me parece que hay una especie de mezcla y no tengo claro cuál es la intención de la clase estaría bien pensarlo para hacer lo que tenga más sentido Nación es que hay una función que se dedica a formatear la salida y que esto podría ser un conjunto de objetos que quedaría más claro y robusto pero no me atrevo a decirlo hasta que no lo analicemos





# --- Versión rica: con objetos ---
@attrs.define(auto_attribs=True, slots=True, frozen=True, kw_only=True)
class ModificationEntry:
    """
    Represents a modification in the system using rich objects (wrappers, DTOs, etc.).
    This class is intended for internal logic, validation, advanced formatting, and access to all high-level data.
    It is not meant for direct persistence or export, but for in-memory manipulation and querying.
    For persistence, export, or printing, convert each instance to SerializableModificationEntry.
    """
    datetime: datetime.datetime = attrs.field(validator=attrs.validators.instance_of(datetime.datetime))
    kind: ModificationKind = attrs.field(validator=attrs.validators.instance_of(ModificationKind))
    asset_wrapper: Any = attrs.field(default=None)
    tag: Optional["TagResponseWrapper"] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(object)))
    album: Optional[AlbumResponseWrapper] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(AlbumResponseWrapper)))
    old_value: Any = attrs.field(default=None)
    new_value: Any = attrs.field(default=None)
    user: Optional[UserResponseWrapper] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(UserResponseWrapper)))
    extra: Optional[dict[str, Any]] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(dict)))



    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Converts the rich entry to a serializable version (only simple types).
        The link is not stored, but can be derived from asset/album/user if needed.
        """
        return SerializableModificationEntry(
            datetime=self.datetime.isoformat(),
            kind=self.kind.name,
            asset_id=self.asset_wrapper.id_as_uuid if self.asset_wrapper is not None else None,
            asset_name=self.asset_wrapper.original_file_name if self.asset_wrapper is not None else None,
            tag_name=self.tag.tag_name if self.tag is not None else None,
            album_id=self.album.album.id if self.album is not None else None,
            album_name=self.album.album.album_name if self.album is not None else None,
            old_value=str(self.old_value) if self.old_value is not None else None,
            new_value=str(self.new_value) if self.new_value is not None else None,
            user_id=self.user.user_id if self.user is not None else None,
            extra=self.extra,
        )

# --- Versión serializable: solo datos simples ---
@attrs.define(auto_attribs=True, slots=True, frozen=True, kw_only=True)
class SerializableModificationEntry:
    """
    Represents a modification ready to be persisted, exported, or printed.
    All fields are simple and serializable types (str, UUID, etc.),
    and correspond to the columns of the final table/log.
    This class is immutable and robust, ideal for audit, logs, and exports.
    It is always obtained from ModificationEntry via the to_serializable() method.
    """
    datetime: str = attrs.field(validator=attrs.validators.instance_of(str))
    kind: str = attrs.field(validator=attrs.validators.instance_of(str))
    asset_id: Optional[UUID] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(UUID)))
    asset_name: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    tag_name: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    album_id: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    album_name: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    old_value: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    new_value: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    user_id: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    extra: Optional[dict[str, Any]] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(dict)))


# TODO: la siguiente clase es mas generiga que tag, requiere refactorizar nombre y ubicacion


@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:



    _instance: "TagModificationReport | None" = None  # Singleton instance
    _instance_created = False  # Class-level flag

    import datetime as dt
    import os

    log_dir: str = attrs.field(
        default="logs", validator=attrs.validators.instance_of(str)
    )
    report_path: str = attrs.field(
        default=f"logs/tag_modification_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.txt",
        validator=attrs.validators.instance_of(str),
    )
    batch_size: int = attrs.field(
        default=1, validator=attrs.validators.instance_of(int)
    )
    modifications: list[ModificationEntry] = attrs.field(  # type: ignore
        factory=list, init=False
    )
    _since_last_flush: int = attrs.field(
        default=0, init=False, validator=attrs.validators.instance_of(int)
    )
    _cleared_report: bool = attrs.field(
        default=False,
        init=False,
        repr=False,
        validator=attrs.validators.instance_of(bool),
    )

    def __attrs_post_init__(self):
        cls = self.__class__
        if getattr(cls, "_instance_created", False):
            raise RuntimeError(
                "TagModificationReport instance already exists. Use TagModificationReport.get_instance() instead of creating a new one."
            )
        cls._instance_created = True
        cls._instance = self

    @staticmethod
    def get_instance() -> "TagModificationReport":
        if TagModificationReport._instance is None:
            TagModificationReport()
        return TagModificationReport._instance  # type: ignore[return-value]

    from typeguard import typechecked
    # todo: tag se esta pasando como string en varias funciones, valorar usar wrapper
    # todo: asset_wrapper se esta pasando como Any en varias funciones, tipar bien
    @typechecked
    def add_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Any,
        tag: Any = None,
        album: Optional[AlbumResponseWrapper] = None,
        old_value: Any = None,
        new_value: Any = None,
        user: Optional[UserResponseWrapper] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registers a modification for any entity (tag, album, assignment, etc.).
        """
        if not self._cleared_report:
            import os
            try:
                os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
                with open(self.report_path, "w", encoding="utf-8"):
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True

        entry = ModificationEntry(
            datetime=datetime.datetime.now(),
            kind=kind,
            asset_wrapper=asset_wrapper,
            tag=tag,
            album=album,
            old_value=old_value,
            new_value=new_value,
            user=user,
            extra=extra,
        )
        self.modifications.append(entry)
        self._since_last_flush += 1
        if self._since_last_flush >= self.batch_size:
            self.flush()
    # todo: revisar old_name y new_name el uso, ya que no solo se usan para nombres, puede ser mejor old_value y new_value?
    # Métodos específicos para cada tipo de acción
    @typechecked
    def add_tag_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Any,
        tag: Any = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ADD_TAG_TO_ASSET,
            ModificationKind.REMOVE_TAG_FROM_ASSET,
            ModificationKind.REMOVE_TAG_GLOBALLY,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            tag=tag,
            old_value=old_value,
            new_value=new_value,
            user=user,
        )
    @typechecked
    def add_album_modification(
        self,
        kind: ModificationKind,
        album: AlbumResponseWrapper,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registers a modification related to an album (e.g., rename, create).
        """
        assert kind in {
            ModificationKind.CREATE_ALBUM,
            ModificationKind.DELETE_ALBUM,
            ModificationKind.RENAME_ALBUM,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=None,
            album=album,
            old_value=old_value,
            new_value=new_value,
            user=user,
            extra=extra,
        )
    @typechecked
    def add_assignment_modification(
        self,
        kind: ModificationKind,
        asset_wrapper: Any,
        album: Optional[AlbumResponseWrapper] = None,
        user: Optional[UserResponseWrapper] = None,
    ) -> None:
        assert kind in {
            ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            ModificationKind.REMOVE_ASSET_FROM_ALBUM,
        }
        self.add_modification(
            kind=kind,
            asset_wrapper=asset_wrapper,
            album=album,
            user=user,
        )

    @typechecked
    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        import os

        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                f.write(self._format_modification_entry(entry) + "\n")
        self._since_last_flush = 0

    @typechecked
    def print_summary(self) -> None:
        print("\n[SUMMARY] Modifications:")
        for entry in self.modifications:
            print(self._format_modification_entry(entry))
        print(f"Total modifications: {len(self.modifications)}")

    @typechecked
    def _build_link(
        self, kind: ModificationKind, asset_id: Optional[UUID], album_id: Optional[UUID]
    ) -> Optional[ParseResult]:
        """
        Build a link for the modification entry based on kind and ids.
        """
        from immich_autotag.utils.get_immich_album_url import \
            get_immich_photo_url

        if (
            kind
            in {
                ModificationKind.ADD_TAG_TO_ASSET,
                ModificationKind.REMOVE_TAG_FROM_ASSET,
                ModificationKind.REMOVE_TAG_GLOBALLY,
                ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                ModificationKind.REMOVE_ASSET_FROM_ALBUM,
            }
            and asset_id
        ):
            return get_immich_photo_url(asset_id)
        elif (
            kind
            in {
                ModificationKind.CREATE_ALBUM,
                ModificationKind.DELETE_ALBUM,
                ModificationKind.RENAME_ALBUM,
            }
            and album_id
        ):
            # todo: Aquí estamos creando el enlace al álbum directamente sin utilizar una función de ayuda cuando en el resto del proyecto estamos utilizando funciones de helper para construir enlaces de hecho el la clase activo tiene un método para construir su propio su propio su propio enlace que aquí nos gastamos un poco saltando y el árbol estamos construyendo a pelo sin utilizar creo que lo suyo sería que el que el roaper de álbum tuviese un método para conseguir el enlace sería lo más limpio lo más simétrico y lo más bonito Si es preciso aquí podríamos pasar como argumento no lo sudes sino directamente el Roper de el Roper de álbum y de activo para que este método lo haga lo más limpio y elegante posible

            return f"/albums/{album_id}"
        return None

    @typechecked
    def _format_modification_entry(self, entry: ModificationEntry) -> str:
        parts = [f"{entry.datetime}"]
        # Always include the operation/enum (kind)
        # todo: Este otro método está creando directamente la lo que se escupe al fichero directamente desde la clase con objetos sin pasar por la clase serializada que no sé si el objetivo era eso y sería también lo más limpio de hecho esta lógica podría estar repartida entre las dos clases que hemos creado para esto en este en este en este fichero habíamos creado una una clase para tener una entrada de log con objetos y otra con datos serializados y estas dos clases podrían colaborar por construyendo en dos pasos el lo que al final finalmente se coloca en el fichero eh por 

        parts.append(
            f"kind={entry.kind.name if hasattr(entry.kind, 'name') else entry.kind}"
        )
        # asset_wrapper may be None
        if entry.asset_wrapper is not None:
            if hasattr(entry.asset_wrapper, 'id_as_uuid'):
                parts.append(f"asset_id={entry.asset_wrapper.id_as_uuid}")
            if hasattr(entry.asset_wrapper, 'original_file_name'):
                parts.append(f"name={entry.asset_wrapper.original_file_name}")
        if entry.tag is not None and hasattr(entry.tag, 'tag_name'):
            parts.append(f"tag={entry.tag.tag_name}")
        if entry.album is not None and hasattr(entry.album, 'album'):
            album_obj = entry.album.album
            if hasattr(album_obj, 'id'):
                parts.append(f"album_id={album_obj.id}")
            if hasattr(album_obj, 'album_name'):
                parts.append(f"album_name={album_obj.album_name}")
        if entry.old_value is not None:
            parts.append(f"old_value={entry.old_value}")
        if entry.new_value is not None:
            parts.append(f"new_value={entry.new_value}")
        if entry.user is not None:
            # Try to print user_id if available
            user_id = getattr(entry.user, 'user_id', None)
            if user_id is not None:
                parts.append(f"user_id={user_id}")
            else:
                parts.append(f"user={entry.user}")
        return " | ".join(parts)
