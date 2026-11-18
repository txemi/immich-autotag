"""Small helpers to read request bodies and build simulated HTTP responses."""

from __future__ import annotations

import json
from typing import Any

import httpx

# Every response the dry run builds carries this header, so a simulated answer
# can always be told apart from one that came from Immich.
DRY_RUN_HEADER = "x-immich-autotag-dry-run"
SIMULATED = "simulated"
OVERLAY = "overlay"


def read_json_body(request: httpx.Request) -> Any:
    """The JSON body of a request, or None when it has none or is not JSON."""
    content = request.read()
    if not content:
        return None
    try:
        return json.loads(content)
    except ValueError:
        return None


def read_json_response(response: httpx.Response) -> Any:
    """The JSON body of a response, or None when it is not JSON."""
    response.read()
    try:
        return response.json()
    except ValueError:
        return None


def json_response(
    status_code: int, data: Any, marker: str = SIMULATED
) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json", DRY_RUN_HEADER: marker},
        content=json.dumps(data, default=str).encode("utf-8"),
    )


def empty_response(status_code: int) -> httpx.Response:
    return httpx.Response(status_code, headers={DRY_RUN_HEADER: SIMULATED})


def error_response(status_code: int, message: str) -> httpx.Response:
    return json_response(
        status_code,
        {"message": message, "statusCode": status_code, "dryRun": True},
    )


def string_list(value: Any) -> list[str]:
    """A list of strings from a JSON value; anything else gives an empty list."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
