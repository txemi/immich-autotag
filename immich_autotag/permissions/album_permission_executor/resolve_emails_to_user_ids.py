from typing import List
from typeguard import typechecked
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.logging.levels import LogLevel
from immich_autotag.api.immich_proxy.permissions import proxy_search_users
from .resolve_emails_result import ResolveEmailsResult

@typechecked
def _resolve_emails_to_user_ids(
    emails: List[str], context: ImmichContext
) -> ResolveEmailsResult:
    """
    Resolve email addresses to Immich user IDs.
    Returns:
        (email_to_id_map, unresolved_emails)
        - email_to_id_map: {email → user_id (UUID)}
        - unresolved_emails: List of emails that couldn't be found
    Fetches all users from Immich and maps their emails to IDs.
    """
    if not emails:
        return ResolveEmailsResult(resolved={}, unresolved=[])

    log_debug(f"[ALBUM_PERMISSIONS] Resolving {len(emails)} emails to user IDs")
    client_wrapper = context.get_client_wrapper()
    client = client_wrapper.get_client()  # AuthenticatedClient

    all_users = proxy_search_users(client=client)
    if all_users is None:
        all_users = []

    # Build email → user_id map
    email_to_id = {}
    for user in all_users:
        if user.email:
            email_to_id[user.email] = str(user.id)

    # Check which emails were resolved
    email_set = set(emails)
    resolved = {email: email_to_id[email] for email in email_set if email in email_to_id}
    unresolved = [email for email in email_set if email not in email_to_id]

    if unresolved:
        log(
            f"[ALBUM_PERMISSIONS] Warning: Could not resolve {len(unresolved)} emails to user IDs: {unresolved}",
            level=LogLevel.IMPORTANT,
        )

    log_debug(
        f"[ALBUM_PERMISSIONS] Resolved {len(resolved)}/{len(email_set)} emails to user IDs"
    )
    return ResolveEmailsResult(resolved=resolved, unresolved=unresolved)
