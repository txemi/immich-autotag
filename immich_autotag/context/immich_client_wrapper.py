from __future__ import annotations

from immich_autotag.config.manager import ConfigManager
from immich_autotag.types.client_types import ImmichClient

# Module singleton
_singleton: "ImmichClientWrapper | None" = None


class ImmichClientWrapper:
    def __init__(self):
        global _singleton
        if _singleton is not None:
            raise RuntimeError(
                "ImmichClientWrapper singleton already exists. Use get_default_instance()."
            )
        self._client = None  # type: ImmichClient | None
        _singleton = self

    def _build_client(self):
        from immich_autotag.config.host_config import get_immich_base_url
        from immich_autotag.types.client_types import ImmichClient

        manager = ConfigManager.get_instance()
        api_key = manager.get_config_or_raise().server.api_key
        return ImmichClient(
            base_url=get_immich_base_url(),
            token=api_key,
            prefix="",
            auth_header_name="x-api-key",
            raise_on_unexpected_status=True,
        )

    @staticmethod
    def get_default_instance() -> "ImmichClientWrapper":
        global _singleton
        if _singleton is None:
            _singleton = ImmichClientWrapper()
        return _singleton

    def get_client(self) -> ImmichClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client
