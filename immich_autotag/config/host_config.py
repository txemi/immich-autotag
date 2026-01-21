import attrs
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True, on_setattr=attrs.setters.validate)
class HostPort:
    host: str = attrs.field(validator=attrs.validators.instance_of(str))
    port: int = attrs.field(validator=attrs.validators.instance_of(int))


@typechecked
def _get_host_and_port() -> HostPort:
    # Get host and port from the experimental config singleton
    from immich_autotag.config.manager import (
        ConfigManager,
    )

    manager = ConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ConfigManager or server config not initialized")
    return HostPort(host=manager.config.server.host, port=manager.config.server.port)


@typechecked
def get_immich_web_base_url() -> str:
    host_port = _get_host_and_port()
    return f"http://{host_port.host}:{host_port.port}"


def get_immich_base_url():
    # In the future, IMMICH_HOST and IMMICH_PORT will be loaded dynamically from a singleton
    return f"{get_immich_web_base_url()}/api"


IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"
