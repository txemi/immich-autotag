Title: Investigation — Immich API change causing missing `assets` on AlbumResponseDto

Summary

I reviewed the issue in your repository. The error is critical but has a clear technical cause tied to changes in Immich's API between recent releases (v1.126.x → v1.127.x).

Observed runtime symptom

- AttributeError: 'AlbumResponseDto' object has no attribute 'assets'

Root cause (breaking change in the API)

- Historically, GET /api/albums/{id} returned an `AlbumResponseDto` including an embedded `assets` list.
- In recent Immich versions, the API removed the `assets` field from the album response DTO. The server now requires clients to fetch album assets from a dedicated endpoint.

New, canonical flow

1. GET /api/albums/{id} -> returns album metadata (name, asset count, etc.).
2. GET /api/albums/{id}/assets -> returns the album's assets (paginated or full, depending on parameters).

Why this change was made

- The change forces explicit retrieval of assets to avoid memory pressure on servers and clients when albums contain large numbers of assets (your case: 66,135 assets in an album).

Immediate code-level fix for `immich-autotag`

- Remove any direct references to `album.assets`.
- Replace implicit iteration over `album.assets` with an explicit call to the new assets endpoint.

Example patch (conceptual)

```python
# 1. Get album metadata
album = client.album_api.get_album_info(id=album_id)

# 2. Get album assets explicitly
# If your SDK exposes a helper, use it (e.g., `get_album_assets`).
album_assets = client.album_api.get_album_assets(id=album_id)

for asset in album_assets:
    # existing autotag logic
    print(f"Processing asset: {asset.id}")
```

Pagination and scalability notes (important for large albums)

- For very large albums, retrieving all assets in one request may cause timeouts or excessive memory use.
- The modern Immich assets endpoint supports pagination with `page` and `size` parameters.
- Recommendation: iterate assets in batches (e.g., `size=5000`) to keep memory use bounded and allow progress checks/retries.

Suggested remediation plan

Short-term (fast unblock)

- Update the code that assumes `album.assets` is present to call the dedicated assets endpoint instead.
- Add guards or clearer errors if the assets endpoint is unreachable.

Medium-term (robust solution)

- Regenerate or update the OpenAPI client (if you use a generated SDK) so it exposes the `get_album_assets` method and proper typing for the album metadata vs asset list endpoints.
- Add unit/integration tests that simulate partial DTOs (album metadata only) and full assets retrieval.
- Add CI instrumentation to detect accidental API contract changes (e.g., run a small contract test against a pinned server version or record `immich-client` version used in CI).

Long-term (operational)

- If you rely on a specific server contract, consider pinning the `immich-client` or the generated SDK version used by `immich-autotag` until you adapt the code for the new flow.
- Alternatively, implement an adapter that tolerates both shapes (legacy `album.assets` and new explicit endpoint), then remove the adapter once server-side rollouts are complete.

Action items I can do for you

- Generate a PR that updates the failing function (if you paste the exact code for the failing function, I will patch it and open the PR for review).
- Regenerate the client SDK files and run a local test against a controlled server to validate behavior.
- Create a short `02-strategy/pin-client.md` with pros/cons to present to maintainers.

If you want me to proceed, tell me which action to take first (patch + PR, regenerate SDK, or draft a strategy doc).