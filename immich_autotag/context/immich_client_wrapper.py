from __future__ import annotations

from immich_autotag.types import ImmichClient

# Singleton de módulo
_singleton: "ImmichClientWrapper | None" = None

class ImmichClientWrapper:
    def __init__(self, client: ImmichClient):
        global _singleton
        if _singleton is not None:
            raise RuntimeError("ImmichClientWrapper singleton already exists. Use get_default_instance().")
        self._client = client
        _singleton = self

    @staticmethod
    def create_default_instance(client: ImmichClient) -> "ImmichClientWrapper":
        if _singleton is not None:
            raise RuntimeError("ImmichClientWrapper singleton already exists. Use get_default_instance().")
        return ImmichClientWrapper(client)

    @staticmethod
    def get_default_instance() -> "ImmichClientWrapper":
        if _singleton is None:
            raise RuntimeError("ImmichClientWrapper singleton not initialized. Call create_default_instance() first.")
        return _singleton

    def get_client(self) -> ImmichClient:
        return self._client
