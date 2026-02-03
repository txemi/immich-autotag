import attrs

from .shared_symbols import (
    IMMICH_CLIENT_PREFIX,
    IMMICH_PROXY_PREFIX,
    LOGGING_PROXY_MODULE_NAME,
)


@attrs.define(frozen=True, auto_attribs=True)
class FullnameInfo:
    _fullname: str

    def is_immich_api_module(self) -> bool:
        return self._fullname.startswith(IMMICH_CLIENT_PREFIX)

    def is_import_from_immich_proxy(self) -> bool:
        return self._fullname.startswith(IMMICH_PROXY_PREFIX)

    def is_import_from_logging_proxy(self) -> bool:
        return self._fullname.startswith(LOGGING_PROXY_MODULE_NAME)

    def __str__(self):
        return self._fullname
