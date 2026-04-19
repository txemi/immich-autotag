from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

from typeguard import typechecked

from immich_autotag.api.immich_proxy.server import proxy_get_server_version
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.types.client_types import ImmichClient


def _normalize_semver(version_text: str) -> str:
    value = version_text.strip()
    if value.startswith("v"):
        value = value[1:]
    for sep in ("+", "-"):
        if sep in value:
            value = value.split(sep, 1)[0]
    return value


def _get_installed_immich_client_version() -> str:
    try:
        return _normalize_semver(package_version("immich-client"))
    except PackageNotFoundError as exc:
        raise RuntimeError(
            "immich-client package is not installed in the current environment."
        ) from exc


@typechecked
def assert_client_server_version_match(client: ImmichClient) -> None:
    server = proxy_get_server_version(client=client)
    if server is None:
        raise RuntimeError("Failed to fetch Immich server version: API returned None")

    server_version = f"{server.major}.{server.minor}.{server.patch}"
    client_version = _get_installed_immich_client_version()

    if client_version != server_version:
        raise RuntimeError(
            "immich-client/server version mismatch: "
            f"client={client_version}, server={server_version}. "
            "Regenerate the client with setup_venv.sh so both versions match."
        )

    log(
        f"Version check passed: immich-client {client_version} matches server {server_version}",
        level=LogLevel.INFO,
    )
