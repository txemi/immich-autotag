"""
The one place where a dry run cuts the writes: the HTTP transport of the client.

Every call to Immich, whatever the module that makes it, goes through the
``httpx`` client of ImmichClientWrapper. In a dry run that client gets this
transport, so no write can leave the process even if some code path forgot about
the dry run: reads go to Immich (and are patched to stay coherent), writes are
recorded and answered by the simulation. See request_classifier for the rule
that separates them (POST searches are reads).
"""

from __future__ import annotations

import httpx

from immich_autotag.dry_run.change_journal import DryRunJournal
from immich_autotag.dry_run.read_overlay import ReadOverlay
from immich_autotag.dry_run.request_classifier import (
    RequestKind,
    classify_request,
    relative_api_path,
)
from immich_autotag.dry_run.simulated_state import SimulatedState
from immich_autotag.dry_run.upstream_reader import UpstreamReader
from immich_autotag.dry_run.write_simulator import WriteSimulator


class DryRunTransport(httpx.BaseTransport):
    def __init__(
        self,
        *,
        inner: httpx.BaseTransport,
        base_path: str,
        journal: DryRunJournal,
        state: SimulatedState | None = None,
    ) -> None:
        self._inner = inner
        self._base_path = base_path
        self._journal = journal
        self._state = state if state is not None else SimulatedState()
        upstream = UpstreamReader(
            inner=inner, base_path=base_path, on_read=journal.count_forwarded_read
        )
        self._overlay = ReadOverlay(state=self._state, upstream=upstream)
        self._simulator = WriteSimulator(
            state=self._state, journal=journal, upstream=upstream, overlay=self._overlay
        )

    def get_journal(self) -> DryRunJournal:
        return self._journal

    def get_state(self) -> SimulatedState:
        return self._state

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        relative_path = relative_api_path(request.url.path, self._base_path)
        # Classify on the path as it goes on the wire (not decoded): an encoded
        # segment must not turn a write into a read.
        wire_path = request.url.raw_path.decode("ascii", "replace").split("?", 1)[0]
        wire_relative = relative_api_path(wire_path, self._base_path)
        if (
            classify_request(request.method, wire_relative) is RequestKind.WRITE
            or classify_request(request.method, relative_path) is RequestKind.WRITE
        ):
            return self._simulator.simulate(request, relative_path)
        local = self._overlay.answer_locally(request, relative_path)
        if local is not None:
            self._journal.count_local_read()
            return local
        self._journal.count_forwarded_read()
        response = self._inner.handle_request(request)
        return self._overlay.patch(request, relative_path, response)

    def close(self) -> None:
        self._inner.close()
