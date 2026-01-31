"""
This module is internal to the package and should not be imported directly.
"""

from typing import TYPE_CHECKING, Dict, List

import attrs

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.types.email_address import EmailAddress
from immich_autotag.types.uuid_wrappers import UserUUID

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper


@attrs.define(auto_attribs=True, on_setattr=attrs.setters.validate)
class ResolveEmailsResult:

    _resolved: Dict[EmailAddress, UserUUID] = attrs.field(
        validator=attrs.validators.instance_of(dict)
    )
    _unresolved: List[EmailAddress] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    def __iter__(self):
        # allow unpacking: resolved, unresolved = func(...)
        yield self._resolved
        yield self._unresolved

    @staticmethod
    def resolve(
        emails: List[str], all_users: List["UserResponseWrapper"]
    ) -> "ResolveEmailsResult":
        """
        Encapsulated logic to resolve emails to user IDs.
        Returns a ResolveEmailsResult instance.
        """
        from immich_autotag.logging.utils import log_debug
        from immich_autotag.types.email_address import EmailAddress

        if not emails:
            return ResolveEmailsResult(resolved={}, unresolved=[])

        log_debug(f"[ALBUM_PERMISSIONS] Resolving {len(emails)} emails to user IDs")

        # Build email → user_id map using EmailAddress
        from immich_autotag.types.uuid_wrappers import UserUUID

        email_to_id: Dict[EmailAddress, UserUUID] = {}
        for user in all_users:
            email_obj = user.get_email()
            if email_obj:
                email_to_id[email_obj] = user.get_uuid()

        # If emails are already EmailAddress objects, use them directly
        email_set = set(emails)
        resolved = {
            email: email_to_id[email] for email in email_set if email in email_to_id
        }
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

    @staticmethod
    def resolve_emails_to_user_ids(
        emails: list[EmailAddress], context: "ImmichContext"
    ) -> "ResolveEmailsResult":
        """
        Static method to resolve a list of EmailAddress objects to user IDs using the UserManager.
        Returns a ResolveEmailsResult instance.
        """
        from immich_autotag.users.user_manager import UserManager

        manager = UserManager.get_instance()
        manager.load_all(context)
        all_users = manager.all_users()
        return ResolveEmailsResult.resolve(emails, all_users)
