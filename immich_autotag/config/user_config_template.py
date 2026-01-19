"""
user_config_template.py

Configuration template for the Immich autotag system (without private data).
You can copy and adapt this file as user_config.py for your actual configuration.

This template is designed to be self-explanatory and easy to adapt. Each block includes comments to guide you.
"""

from immich_autotag.config.models import (
    AlbumDateConsistencyConfig,
    AlbumDetectionFromFoldersConfig,
    AlbumPermissionsConfig,
    AlbumSelectionRule,
    ClassificationConfig,
    ClassificationRule,
    Conversion,
    ConversionMode,
    DateCorrectionConfig,
    Destination,
    DuplicateProcessingConfig,
    FilterConfig,
    PerformanceConfig,
    ServerConfig,
    SkipConfig,
    UserConfig,
    UserGroup,
)

# Private module-level constants for repeated tag/album/group names

# AUTOTAG CLASSIFICATION RULES INPUT STRINGS
_AUTOTAG_INPUT_PREFIX = "autotag_input_"
_AUTOTAG_OUTPUT_PREFIX = "autotag_output_"

_ADULT_MEME_SUFFIX = "adult_meme"
_MEME_SUFFIX = "meme"
_PENDING_REVIEW_SUFFIX = "pending_review"

# AUTOTAG CLASSIFICATION RULE OUPUT STRINGS
_IGNORE_SUFFIX = "ignore"
_UNKNOWN_SUFFIX = "unknown"
_CONFLICT_SUFFIX = "conflict"
_DUPLICATE_ASSET_ALBUM_CONFLICT_SUFFIX = "duplicate_asset_album_conflict"
_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_SUFFIX = (
    "duplicate_asset_classification_conflict"
)
_ALBUM_DETECTION_CONFLICT_SUFFIX = "album_detection_conflict"
_ALBUM_DATE_MISMATCH_SUFFIX = "album_date_mismatch"

# USER GROUPS
_FAMILY = "family"
_FRIENDS = "friends"

# COMPOSED VALUES FOR CONVENIENCE
_AUTOTAG_INPUT_ADULT_MEME = _AUTOTAG_INPUT_PREFIX + _ADULT_MEME_SUFFIX
_AUTOTAG_INPUT_MEME = _AUTOTAG_INPUT_PREFIX + _MEME_SUFFIX
_AUTOTAG_INPUT_PENDING_REVIEW = _AUTOTAG_INPUT_PREFIX + _PENDING_REVIEW_SUFFIX
_AUTOTAG_INPUT_IGNORE = _AUTOTAG_INPUT_PREFIX + _IGNORE_SUFFIX
_ADULT_MEME = _ADULT_MEME_SUFFIX

_AUTOTAG_OUTPUT_UNKNOWN = _AUTOTAG_OUTPUT_PREFIX + _UNKNOWN_SUFFIX
_AUTOTAG_OUTPUT_CONFLICT = _AUTOTAG_OUTPUT_PREFIX + _CONFLICT_SUFFIX
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_ALBUM_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _DUPLICATE_ASSET_ALBUM_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX = (
    _AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT + "_"
)
_AUTOTAG_OUTPUT_ALBUM_DETECTION_CONFLICT = (
    _AUTOTAG_OUTPUT_PREFIX + _ALBUM_DETECTION_CONFLICT_SUFFIX
)
_AUTOTAG_OUTPUT_ALBUM_DATE_MISMATCH = (
    _AUTOTAG_OUTPUT_PREFIX + _ALBUM_DATE_MISMATCH_SUFFIX
)

# ACTUAL CONFIG

user_config = UserConfig(
    # -------------------------------------------------------------------------
    # API and connection: Immich access credentials
    # host: Immich domain or IP
    # port: Port where Immich listens
    # api_key: Immich API key
    server=ServerConfig(
        host="immich.example.com", port=2283, api_key="YOUR_API_KEY_HERE"
    ),
    enable_album_name_strip=True,  # Trim spaces in album names
    skip=SkipConfig(skip_n=0, resume_previous=True),  # Resume from last processed asset
    # -------------------------------------------------------------------------
    # ASSET FILTER: Global filter assets by tag, album name pattern or ID. Inclussion or exclusion.
    filters=FilterConfig(filter_in=[ClassificationRule(asset_links=[])]),
    # -------------------------------------------------------------------------
    # TAG CONVERSIONS: mapping of old tags or albums to new ones (compatibility/refactor)
    conversions=[
        Conversion(
            source=ClassificationRule(tag_names=[_MEME_SUFFIX]),
            destination=Destination(tag_names=[_AUTOTAG_INPUT_MEME]),
        ),
        Conversion(
            source=ClassificationRule(tag_names=[_ADULT_MEME]),
            destination=Destination(tag_names=[_AUTOTAG_INPUT_ADULT_MEME]),
        ),
        # Example conversion with COPY mode for testing
        Conversion(
            description="Testing both tags and albums: This conversion is for experiments, to quickly populate the index with both tags and albums. In some cases, tags are faster and better; in others, albums work better. This lets us compare both approaches in the database.",
            source=ClassificationRule(
                tag_names=[_AUTOTAG_INPUT_MEME],
                album_name_patterns=[_AUTOTAG_INPUT_MEME],
            ),
            destination=Destination(
                tag_names=[_AUTOTAG_INPUT_MEME], album_names=[_AUTOTAG_INPUT_MEME]
            ),
            mode=ConversionMode.COPY,
        ),
        # Example conversion with COPY mode for testing
        Conversion(
            description="Testing both tags and albums: This conversion is for experiments, to quickly populate the index with both tags and albums. In some cases, tags are faster and better; in others, albums work better. This lets us compare both approaches in the database.",
            source=ClassificationRule(
                tag_names=[_AUTOTAG_INPUT_ADULT_MEME],
                album_name_patterns=[_AUTOTAG_INPUT_ADULT_MEME],
            ),
            destination=Destination(
                tag_names=[_AUTOTAG_INPUT_ADULT_MEME],
                album_names=[_AUTOTAG_INPUT_ADULT_MEME],
            ),
            mode=ConversionMode.COPY,
        ),
    ],
    # -------------------------------------------------------------------------
    # CLASSIFICATION AND RULES:
    # These are the rules that define asset categories and determine the classification status of each asset.
    # An asset is considered classified if it matches exactly one rule, in conflict if it matches more than one rule, and unclassified if it matches none.
    # Example: only albums starting with a date (YYYY-, YYYY-MM, YYYY-MM-DD) are considered "events".
    # Output tags are used to mark assets as classified, in conflict, or unclassified, making it easy to review the current state.
    #
    # NOTE: We no longer use real tag hierarchy (slashes '/').
    # All tags use underscores '_' instead of slashes. The namespace is only virtual/documentary.
    # This avoids issues with the Immich API and tag discovery, as hierarchical tags are not reliably supported.
    classification=ClassificationConfig(
        rules=[
            ClassificationRule(
                tag_names=[
                    _MEME_SUFFIX,  # (LEGACY) Meme: humorous images, no prefix. Compatibility.
                    _AUTOTAG_INPUT_MEME,  # Memes/jokes uploaded indiscriminately, not events.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_MEME}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _ADULT_MEME,  # (LEGACY) Adult meme: NSFW content, no prefix. Compatibility.
                    _AUTOTAG_INPUT_ADULT_MEME,  # NSFW/adult memes, separate from family environment.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_ADULT_MEME}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _AUTOTAG_INPUT_PENDING_REVIEW,  # Pending review: decide destination.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_PENDING_REVIEW}$"  # Albums with exact name
                ],
            ),
            ClassificationRule(
                tag_names=[
                    _AUTOTAG_INPUT_IGNORE,  # Ignore: photos discarded from main flow.
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_IGNORE}$"  # Albums with exact name
                ],
            ),
            # This rule is common and useful for many users, as a lot of people organize albums by events related to a specific date.
            ClassificationRule(
                album_name_patterns=[
                    r"^\d{4}-(\d{2}(-\d{2})?)?"
                ]  # Only albums with a date name are considered "events"
            ),
        ],
        autotag_unknown=_AUTOTAG_OUTPUT_UNKNOWN,  # Assets not assigned to any categorization rule
        autotag_conflict=_AUTOTAG_OUTPUT_CONFLICT,  # Assets matching more than one categorization rule (conflict)
    ),
    # -------------------------------------------------------------------------
    # DUPLICATE PROCESSING: configuration for handling duplicates
    duplicate_processing=DuplicateProcessingConfig(
        autotag_album_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_ALBUM_CONFLICT,  # Duplicates with album conflict
        autotag_classification_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,  # Duplicates with classification conflict
        autotag_classification_conflict_prefix=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX,  # Prefix for group conflicts
        autotag_album_detection_conflict=_AUTOTAG_OUTPUT_ALBUM_DETECTION_CONFLICT,  # Multiple candidate folders for album detection
        date_correction=DateCorrectionConfig(
            enabled=True,  # Date correction by file/folder name
            extraction_timezone="UTC",  # Timezone for date extraction
        ),
    ),
    # -------------------------------------------------------------------------
    # ALBUM DATE CONSISTENCY: check if asset dates match album dates in name
    album_date_consistency=AlbumDateConsistencyConfig(
        enabled=True,
        autotag_album_date_mismatch=_AUTOTAG_OUTPUT_ALBUM_DATE_MISMATCH,
        threshold_days=180,  # 6 months - gradually reduce as you fix mismatches (180->90->60->30->7)
    ),
    album_detection_from_folders=AlbumDetectionFromFoldersConfig(
        enabled=True,  # Create albums from folders (disabled)
        excluded_paths=[r"whatsapp"],  # Exclude folders by pattern
    ),
    create_album_from_date_if_missing=True,  # Enables creation of generic daily albums for unclassified assets, you can rename or modify them later
    # -------------------------------------------------------------------------
    # ALBUM PERMISSIONS: Automatic album sharing to user groups based on keywords
    #
    # This section lets you define user groups and assign users (by email) to each group.
    # You can also define rules that automatically share albums with specific groups based on keywords in the album name.
    # For example, if an album name contains the keyword "familia", it will be automatically shared with all users in the "familia" group.
    #
    # Only users listed in the relevant group(s) will have access to albums that match the rule.
    # If a user is removed from a group, they will lose access to the corresponding albums.
    #
    # To enable, set enabled=True and customize the groups and rules below:
    album_permissions=AlbumPermissionsConfig(
        enabled=True,  # Set to True to enable album permission detection
        user_groups=[
            UserGroup(
                name=_FAMILY,
                description="Family members",
                members=[
                    "grandpa@example.com",
                    "grandma@example.com",
                    "mother@example.com",
                ],
            ),
            UserGroup(
                name=_FRIENDS,
                description="Close friends",
                members=[
                    "john@example.com",
                    "jane@example.com",
                ],
            ),
        ],
        selection_rules=[
            AlbumSelectionRule(
                name="Share Family albums",
                keyword=_FAMILY,
                groups=[_FAMILY],
                access="view",
            ),
            AlbumSelectionRule(
                name="Share Friends albums",
                keyword=_FRIENDS,
                groups=[_FRIENDS],
                access="view",
            ),
        ],
        log_unmatched=True,  # Set to True to log albums that don't match any rule
    ),
    # -------------------------------------------------------------------------
    # PERFORMANCE: Tuning for production vs development
    performance=PerformanceConfig(
        enable_type_checking=True,  # Disable @typechecked in production (~50% perf improvement)
        # Set to True only for development/debugging to catch type errors early
    ),
)

if __name__ == "__main__":
    import pprint

    pprint.pprint(user_config.model_dump())
