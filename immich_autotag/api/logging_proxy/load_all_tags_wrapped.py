"""
High-level loader for all tags (no reporting, just fetch and wrap).
This function loads all tags from the API and returns them wrapped as TagWrapper objects.
"""

from immich_autotag.api.immich_proxy.tags import proxy_get_all_tags
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.tags.tag_response_wrapper import TagWrapper


def load_all_tags_wrapped() -> list[TagWrapper]:
    """
    Loads all tags from the API and returns them wrapped as TagWrapper objects.
    No reporting, no logging, just fetch and wrap.
    """
    client_wrapper = ImmichClientWrapper.get_default_instance()
    client = client_wrapper.get_client()
    tags_dto = proxy_get_all_tags(client=client)
    if tags_dto is None:
        raise RuntimeError("API returned None when fetching all tags")
    return [TagWrapper(tag_dto) for tag_dto in tags_dto]
