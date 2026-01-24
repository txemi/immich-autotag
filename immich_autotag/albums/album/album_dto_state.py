
import datetime
import enum
from uuid import UUID
import attrs
from immich_client.models.album_response_dto import AlbumResponseDto

class AlbumLoadSource(enum.Enum):
    """
    Enum to indicate the API call source for an AlbumResponseDto.
    SEARCH: Loaded from album list/search API (partial/summary info).
    DETAIL: Loaded from album detail API (full info).
    """
    SEARCH = "search"
    DETAIL = "detail"

@attrs.define(auto_attribs=True, slots=True)
class AlbumDtoState:
    """
    Encapsula el estado de un AlbumResponseDto recuperado de la API.

    Esta clase agrupa tres atributos que siempre se obtienen juntos al consultar un álbum:
      - El DTO de álbum (privado, no se expone directamente)
      - El enum AlbumLoadSource que indica la fuente de la API
      - El timestamp (loaded_at) de la obtención

    El DTO no se expone directamente. El acceso debe hacerse mediante métodos públicos
    que devuelven solo la información necesaria.
    """
    _dto: AlbumResponseDto = attrs.field(validator=attrs.validators.instance_of(AlbumResponseDto))
    _load_source: AlbumLoadSource = attrs.field(validator=attrs.validators.instance_of(AlbumLoadSource))
    _loaded_at: datetime.datetime = attrs.field(factory=datetime.datetime.now, validator=attrs.validators.instance_of(datetime.datetime))

    def __attrs_post_init__(self):
        if self._dto is None:
            raise ValueError("_dto (AlbumResponseDto) no puede ser None")

    def get_album_id(self) -> UUID:
        """Devuelve el ID del álbum (sin exponer el DTO completo)."""
        return self._dto.id

    def get_album_name(self) -> str:
        """Devuelve el nombre del álbum (sin exponer el DTO completo)."""
        return self._dto.albumName

    def get_load_source(self) -> AlbumLoadSource:
        """Devuelve la fuente de la API desde la que se obtuvo el álbum."""
        return self._load_source

    def get_loaded_at(self) -> datetime.datetime:
        """Devuelve el timestamp de obtención del álbum."""
        return self._loaded_at

    def update(self, dto: AlbumResponseDto, load_source: AlbumLoadSource) -> None:
        """
        Actualiza el estado con un nuevo DTO, fuente y timestamp actual.
        Garantiza que loaded_at nunca retrocede en el tiempo.
        """
        now = datetime.datetime.now()
        if self._loaded_at and now < self._loaded_at:
            raise RuntimeError(
                "New loaded_at timestamp is earlier than previous loaded_at."
            )
        self._dto = dto
        self._load_source = load_source
        self._loaded_at = now
    def get_album_users(self) -> "AlbumUserList":
        users = [AlbumUserWrapper(user=u) for u in self._dto.album_users]
        return AlbumUserList(users)
    def get_owner_uuid(self) -> "UUID":
        return UUID(self._album_dto.owner_id)