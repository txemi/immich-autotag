"""
High-level loader for a single tag by id (no reporting, just fetch and wrap).
"""

from immich_autotag.api.immich_proxy.tags import proxy_get_tag_by_id
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.tags.tag_response_wrapper import TagWrapper, TagSource
from immich_autotag.types.uuid_wrappers import TagUUID

def load_tag_by_id_wrapped(id_: TagUUID) -> TagWrapper | None:
	"""
	Fetch a tag by id using the proxy and wrap it as TagWrapper.
	Returns the found TagWrapper or None.
	"""
	client_wrapper = ImmichClientWrapper.get_default_instance()
	client = client_wrapper.get_client()
	try:
		tag_dto = proxy_get_tag_by_id(client=client, tag_id=id_)
	except Exception:
		tag_dto = None
	if tag_dto is not None:
		return TagWrapper(tag_dto, TagSource.GET_TAG_BY_ID)
	return None
