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
        self._client_is_dry_run = False
        _singleton = self

    def _build_client(self):
        from immich_autotag.config.host_config import get_immich_base_url
        from immich_autotag.dry_run.dry_run_mode import is_dry_run_active
        from immich_autotag.types.client_types import ImmichClient

        manager = ConfigManager.get_instance()
        api_key = manager.get_config().server.api_key
        base_url = get_immich_base_url()
        httpx_args = {}
        self._client_is_dry_run = is_dry_run_active()
        if self._client_is_dry_run:
            # Dry run: every request goes through DryRunTransport, the one place
            # where writes are cut. Nothing else in the code needs to know.
            from immich_autotag.dry_run.dry_run_session import (
                DryRunSession,
                start_for_current_run,
            )

            session = DryRunSession.get_current() or start_for_current_run(base_url)
            httpx_args["transport"] = session.get_transport()
        return ImmichClient(
            base_url=base_url,
            token=api_key,
            prefix="",
            auth_header_name="x-api-key",
            raise_on_unexpected_status=True,
            httpx_args=httpx_args,
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
        if not self._client_is_dry_run:
            from immich_autotag.dry_run.dry_run_mode import is_dry_run_active

            if is_dry_run_active():
                raise RuntimeError(
                    "Dry run requested after the Immich client was built without "
                    "it: refusing to go on, the client could write to Immich."
                )
        return self._client
