"""
GET requests the dry run itself sends to Immich, to build coherent answers.

A simulated write sometimes has to answer with the entity it would have changed
(``PUT /assets/{id}`` answers with the asset). The reader fetches it with a GET,
the only method it can send, reusing the authentication headers of the request
being simulated. Answers are cached: nothing changes on the server during a dry
run, because nothing is written.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import httpx

from immich_autotag.dry_run.http_helpers import read_json_response

_BODY_HEADERS = frozenset({"content-length", "content-type", "transfer-encoding"})


class UpstreamReader:
    def __init__(
        self,
        *,
        inner: httpx.BaseTransport,
        base_path: str,
        on_read: Callable[[], None],
    ) -> None:
        self._inner = inner
        self._base_path = base_path.rstrip("/")
        self._on_read = on_read
        self._cache: dict[str, Any] = {}

    def get_json(
        self, template: httpx.Request, relative_path: str, query: str = ""
    ) -> Any:
        """GET ``relative_path``; the parsed JSON, or None if it did not answer 200."""
        raw_path = self._base_path + relative_path
        if query:
            raw_path = f"{raw_path}?{query}"
        if raw_path in self._cache:
            return copy.deepcopy(self._cache[raw_path])
        headers = {
            key: value
            for key, value in template.headers.items()
            if key.lower() not in _BODY_HEADERS
        }
        request = httpx.Request(
            "GET",
            template.url.copy_with(raw_path=raw_path.encode("utf-8")),
            headers=headers,
        )
        self._on_read()
        response = self._inner.handle_request(request)
        data = read_json_response(response) if response.status_code == 200 else None
        response.close()
        self._cache[raw_path] = data
        return copy.deepcopy(data)
