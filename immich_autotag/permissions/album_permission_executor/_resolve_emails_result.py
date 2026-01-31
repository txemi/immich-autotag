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
        init=False, factory=dict, metadata={"type": "Dict[EmailAddress, UserUUID]"}
    )
    _unresolved: List[EmailAddress] = attrs.field(
        init=False, factory=list, metadata={"type": "List[EmailAddress]"}
    )

    def __iter__(self):
        yield self._resolved
        yield self._unresolved

    def resolve(
        self, emails: List[EmailAddress], all_users: List["UserResponseWrapper"]
    ) -> None:
        """
        Fills this instance with resolved and unresolved emails.
        """
        from immich_autotag.logging.utils import log_debug

        self._resolved.clear()
        self._unresolved.clear()

        if not emails:
            return

        log_debug(f"[ALBUM_PERMISSIONS] Resolving {len(emails)} emails to user IDs")

        email_to_id: Dict[EmailAddress, UserUUID] = {}
        for user in all_users:
            email_obj = user.get_email()
            if email_obj:
                email_to_id[email_obj] = user.get_uuid()

        email_set = set(emails)
        for email in email_set:
            if email in email_to_id:
                self._resolved[email] = email_to_id[email]
            else:
                self._unresolved.append(email)

        if self._unresolved:
            log(
                f"[ALBUM_PERMISSIONS] Warning: Could not resolve {len(self._unresolved)} emails to user IDs: {self._unresolved}",
                level=LogLevel.IMPORTANT,
            )

        log_debug(
            f"[ALBUM_PERMISSIONS] Resolved {len(self._resolved)}/{len(email_set)} emails to user IDs"
        )

    def resolve_emails_to_user_ids(
        self, emails: list[EmailAddress], context: "ImmichContext"
    ) -> None:
        """
        Fills this instance with resolved and unresolved emails using the UserManager.
        """
        from immich_autotag.users.user_manager import UserManager

        manager = UserManager.get_instance()
        manager.load_all(context)
        all_users = manager.all_users()
        self.resolve(emails, all_users)
