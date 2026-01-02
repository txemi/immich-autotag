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

# todo: Tengo claro cuál es el objetivo de esta clase si el objetivo es tener los campos que van a ir al fichero y debería ser todo string o si el objetivo es tener toda la información de un registro entonces podría ser todo objetos en vez de en vez de strings esto se creó utilizando bike coding por get hat copilot y ahora me parece que hay una especie de mezcla y no tengo claro cuál es la intención de la clase estaría bien pensarlo para hacer lo que tenga más sentido Nación es que hay una función que se dedica a formatear la salida y que esto podría ser un conjunto de objetos que quedaría más claro y robusto pero no me atrevo a decirlo hasta que no lo analicemos





# --- Versión rica: con objetos ---
@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ModificationEntry:
    """
    Represents a modification in the system using rich objects (wrappers, DTOs, etc.).
    This class is intended for internal logic, validation, advanced formatting, and access to all high-level data.
    It is not meant for direct persistence or export, but for in-memory manipulation and querying.
    For persistence, export, or printing, convert each instance to SerializableModificationEntry.
    """
    datetime: str
    kind: ModificationKind
    asset_wrapper: Any = None
    tag: Optional["TagResponseWrapper"] = None
    album: Optional[AlbumResponseWrapper] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    user: Optional[UserResponseWrapper] = None
    link: Optional[str] = None
    extra: Optional[dict[str, Any]] = None

    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Convierte la entrada rica en una versión solo con datos serializables, sin getattr/hasattr.
        """
        return SerializableModificationEntry(
            datetime=self.datetime,
            kind=self.kind.name,
            asset_id=self.asset_wrapper.id_as_uuid if self.asset_wrapper is not None else None,
            asset_name=self.asset_wrapper.original_file_name if self.asset_wrapper is not None else None,
            tag_name=self.tag.tag_name if self.tag is not None else None,
            album_id=self.album.album.id if self.album is not None else None,
            album_name=self.album.album.album_name if self.album is not None else None,
            old_name=self.old_name,
            new_name=self.new_name,
            user_id=self.user.user_id if self.user is not None else None,
            link=self.link,
            extra=self.extra,
        )

# --- Versión serializable: solo datos simples ---
@attrs.define(auto_attribs=True, slots=True, frozen=True)
class SerializableModificationEntry:
    """
    Represents a modification ready to be persisted, exported, or printed.
    All fields are simple and serializable types (str, UUID, etc.),
    and correspond to the columns of the final table/log.
    This class is immutable and robust, ideal for audit, logs, and exports.
    It is always obtained from ModificationEntry via the to_serializable() method.
    """
    datetime: str
    kind: str
    asset_id: Optional[UUID] = None
    asset_name: Optional[str] = None
    tag_name: Optional[str] = None
    album_id: Optional[str] = None
    album_name: Optional[str] = None
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    user_id: Optional[str] = None
    link: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


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
        tag: Optional["TagResponseWrapper"] = None,
        album: Optional[AlbumResponseWrapper] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
        user: Optional[UserResponseWrapper] = None,
        extra: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registers a modification for any entity (tag, album, assignment, etc.).
        Maintains compatibility with previous usage.
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

        link = asset_wrapper.get_immich_photo_url().geturl() if asset_wrapper is not None else None
        entry = ModificationEntry(
            datetime=datetime.datetime.now().isoformat(),
            kind=kind,
            asset_wrapper=asset_wrapper,
            tag=tag,
            album=album,
            old_name=old_name,
            new_name=new_name,
            user=user,
            link=link,
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
        tag: Optional["TagResponseWrapper"] = None,
        old_name: Optional[str] = None,
        new_name: Optional[str] = None,
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
            old_name=old_name,
            new_name=new_name,
            user=user,
        )
    @typechecked
    def add_album_modification(
        self,
        kind: ModificationKind,
        album: AlbumResponseWrapper,
        old_name: str = None,
        new_name: str = None,
        user: UserResponseWrapper = None,
        extra: dict[str, Any] = None,
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
            old_name=old_name,
            new_name=new_name,
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
            return f"/albums/{album_id}"
        return None

    @typechecked
    def _format_modification_entry(self, entry: ModificationEntry) -> str:
        parts = [f"{entry.datetime}"]
        # Always include the operation/enum (kind)
        parts.append(
            f"kind={entry.kind.name if hasattr(entry.kind, 'name') else entry.kind}"
        )
        # Removed 'entity' and 'action' as they are not attributes of ModificationEntry
        if entry.asset_id:
            parts.append(f"asset_id={entry.asset_id}")
        if entry.asset_name:
            parts.append(f"name={entry.asset_name}")
        if entry.tag_name:
            parts.append(f"tag={entry.tag_name}")
        if entry.album:
            parts.append(f"album_id={entry.album.album.id}")
            parts.append(f"album_name={entry.album.album.album_name}")
        if entry.old_name:
            parts.append(f"old_name={entry.old_name}")
        if entry.new_name:
            parts.append(f"new_name={entry.new_name}")
        if entry.link:
            parts.append(f"link={entry.link}")
        if entry.user:
            parts.append(f"user={entry.user}")
        # Evitar duplicados de album_id y album_name
        # (el bloque anterior ya los añade si entry.album existe)
        return " | ".join(parts)
