from __future__ import annotations
from typing import Optional
from immich_autotag.types import ImmichClient

class ImmichClientWrapper:
    _default_instance: Optional[ImmichClient] = None

    @classmethod
    def create_default_instance(cls, client: ImmichClient) -> ImmichClient:
        if cls._default_instance is not None:
            raise RuntimeError("ImmichClient default instance already exists. Use get_default_instance().")
        cls._default_instance = client
        return client

    @classmethod
    def get_default_instance(cls) -> ImmichClient:
        if cls._default_instance is None:
            raise RuntimeError("ImmichClient default instance not initialized. Call create_default_instance() first.")
        return cls._default_instance
