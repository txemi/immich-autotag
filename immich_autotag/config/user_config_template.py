"""
user_config_template.py

Configuration template for the Immich autotag system (without private data).
Copy and adapt this file as user_config.py for your actual configuration.

QUICK START:
  1. Set server.host, server.port, and server.api_key (get your key from
     Immich → Account Settings → API Keys).
  2. Adjust the classification rules to match how you tag/album your photos.
  3. Optionally configure album_permissions with your real user emails.

For full documentation of all config classes and fields, see:
  immich_autotag/config/models.py
"""

from immich_autotag.config.models import (
    AlbumDateConsistencyConfig,
    AlbumDetectionFromFoldersConfig,
    AlbumPermissionsConfig,
    AlbumSelectionRule,
    ClassificationConfig,
    ClassificationRule,
    Conversion,
    ConversionConfig,
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

from immich_autotag.utils.links.github import github_doc_url

# ---------------------------------------------------------------------------
# TAG / ALBUM NAME CONSTANTS
#
# "Input" tags/albums are applied by YOU (manually or via other tools) to
# signal intent to autotag — they are the *input* to the classification rules.
#
# "Output" tags/albums are written by autotag itself to report the result of
# classification — they are the *output* and should not be edited by hand.
#
# Using constants here prevents typos and makes it easy to rename them later.
# ---------------------------------------------------------------------------

# Prefixes that distinguish input signals from output results
_AUTOTAG_INPUT_PREFIX = "autotag_input_"
_AUTOTAG_OUTPUT_PREFIX = "autotag_output_"

# Input category names (you assign these to assets to guide classification)
_MEME_SUFFIX = "meme"
_ADULT_MEME_SUFFIX = "adult_meme"
_PENDING_REVIEW_SUFFIX = "pending_review"
_IGNORE_SUFFIX = "ignore"
_BROKEN_SUFFIX = "broken"

# Output status names (autotag writes these; do not assign them manually)
_UNKNOWN_SUFFIX = "unknown"
_CONFLICT_SUFFIX = "conflict"
_DUPLICATE_ASSET_ALBUM_CONFLICT_SUFFIX = "duplicate_asset_album_conflict"
_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_SUFFIX = (
    "duplicate_asset_classification_conflict"
)
_ALBUM_DETECTION_CONFLICT_SUFFIX = "album_detection_conflict"
_ALBUM_DATE_MISMATCH_SUFFIX = "album_date_mismatch"

# User group names (used both as group identifiers and as album keywords)
_FAMILY = "family"
_FRIENDS = "friends"

# Composed input tag/album names
_AUTOTAG_INPUT_MEME = _AUTOTAG_INPUT_PREFIX + _MEME_SUFFIX
_AUTOTAG_INPUT_ADULT_MEME = _AUTOTAG_INPUT_PREFIX + _ADULT_MEME_SUFFIX
_AUTOTAG_INPUT_PENDING_REVIEW = _AUTOTAG_INPUT_PREFIX + _PENDING_REVIEW_SUFFIX
_AUTOTAG_INPUT_IGNORE = _AUTOTAG_INPUT_PREFIX + _IGNORE_SUFFIX
_AUTOTAG_INPUT_BROKEN = _AUTOTAG_INPUT_PREFIX + _BROKEN_SUFFIX

# Composed output tag names (written by autotag)
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

# ---------------------------------------------------------------------------
# MAIN CONFIGURATION
# ---------------------------------------------------------------------------

user_config = UserConfig(
    description=(
        "Immich autotag configuration. "
        "For authoritative field documentation see: "
        f"{github_doc_url('immich_autotag/config/models.py')}"
    ),
    # -------------------------------------------------------------------------
    # SERVER: Immich connection details.
    #
    # host    — domain or IP of your Immich instance (no trailing slash)
    # port    — default is 2283; change if you exposed Immich on a custom port
    # api_key — generate one in Immich: Account Settings → API Keys → New key
    # -------------------------------------------------------------------------
    server=ServerConfig(
        host="immich.example.com",
        port=2283,
        api_key="YOUR_API_KEY_HERE",
    ),
    # Strip leading/trailing spaces from album names when comparing or creating them.
    enable_album_name_strip=True,
    # skip_n: skip the first N assets (useful for resuming after an interruption).
    # resume_previous: automatically resume from the last successfully processed asset.
    skip=SkipConfig(skip_n=0, resume_previous=True),
    # -------------------------------------------------------------------------
    # FILTERS: Restrict which assets are processed.
    #
    # Leave as FilterConfig() to process all assets, or pass tag/album filters
    # to target a specific subset. See FilterConfig in models.py for options.
    # -------------------------------------------------------------------------
    filters=FilterConfig(),
    # -------------------------------------------------------------------------
    # CONVERSIONS: Batch-rename or move tags/albums across assets.
    #
    # Use this when you want to consolidate multiple old tag/album names into
    # a single canonical one, or to migrate from tags to albums (or vice versa).
    #
    # mode=COPY keeps the source; mode=MOVE removes it after copying.
    #
    # Set enabled=False to skip this step entirely.
    # -------------------------------------------------------------------------
    conversions=ConversionConfig(
        enabled=True,
        description=(
            "Consolidate legacy tag variants into canonical input tags so that "
            "the classification rules only need to check one name per category."
        ),
        conversions=[
            Conversion(
                description=(
                    "Merge bare 'meme' tag (legacy, no prefix) into the canonical "
                    "input tag. MOVE mode removes the old tag after copying."
                ),
                source=ClassificationRule(
                    tag_names=[_MEME_SUFFIX, _AUTOTAG_INPUT_MEME],
                ),
                destination=Destination(
                    album_names=[_AUTOTAG_INPUT_MEME],
                ),
                mode=ConversionMode.MOVE,
            ),
            Conversion(
                description=(
                    "Merge bare 'adult_meme' tag (legacy, no prefix) into the "
                    "canonical input tag. MOVE mode removes the old tag after copying."
                ),
                source=ClassificationRule(
                    tag_names=[_ADULT_MEME_SUFFIX, _AUTOTAG_INPUT_ADULT_MEME],
                ),
                destination=Destination(
                    album_names=[_AUTOTAG_INPUT_ADULT_MEME],
                ),
                mode=ConversionMode.MOVE,
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # CLASSIFICATION RULES: Define what "classified" means for your library.
    #
    # Each rule describes one category. An asset is:
    #   - classified   → matches exactly one rule  → no output tag written
    #   - conflict     → matches more than one rule → autotag_output_conflict
    #   - unknown      → matches no rule            → autotag_output_unknown
    #
    # Rules can match by tag name, album name, or album name pattern (regex).
    #
    # Tag naming convention: use underscores '_' instead of slashes '/'.
    # Immich's hierarchical tag support is unreliable via the API, so we keep
    # the namespace purely documentary.
    #
    # Tip: start with the rules below and add your own categories as needed.
    # -------------------------------------------------------------------------
    classification=ClassificationConfig(
        description=(
            "Rules that define asset categories. Assets not matching any rule "
            "are tagged as unknown; assets matching multiple rules are tagged as "
            "conflict — both are easy to find and review in Immich."
        ),
        rules=[
            # --- Memes / jokes (not events, should not end up in date albums) ---
            ClassificationRule(
                tag_names=[
                    _MEME_SUFFIX,           # legacy bare tag — kept for compatibility
                    _AUTOTAG_INPUT_MEME,    # canonical input tag
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_MEME}$",
                ],
                description="Memes/jokes — not events, excluded from date-based albums.",
            ),
            # --- Adult / NSFW content (kept separate from family environment) ---
            ClassificationRule(
                tag_names=[
                    _ADULT_MEME_SUFFIX,         # legacy bare tag — kept for compatibility
                    _AUTOTAG_INPUT_ADULT_MEME,  # canonical input tag
                ],
                album_name_patterns=[
                    rf"^{_AUTOTAG_INPUT_ADULT_MEME}$",
                ],
                description="Adult/NSFW content — separated from the family environment.",
            ),
            # --- Assets awaiting a destination decision ---
            ClassificationRule(
                tag_names=[_AUTOTAG_INPUT_PENDING_REVIEW],
                album_name_patterns=[rf"^{_AUTOTAG_INPUT_PENDING_REVIEW}$"],
                description="Assets that still need a destination decision.",
            ),
            # --- Assets intentionally excluded from the main flow ---
            ClassificationRule(
                tag_names=[_AUTOTAG_INPUT_IGNORE],
                album_name_patterns=[rf"^{_AUTOTAG_INPUT_IGNORE}$"],
                description="Assets explicitly discarded from the main processing flow.",
            ),
            # --- Broken / corrupted files ---
            ClassificationRule(
                tag_names=[_AUTOTAG_INPUT_BROKEN],
                album_name_patterns=[rf"^{_AUTOTAG_INPUT_BROKEN}$"],
                description=(
                    "Assets detected as broken or corrupted during processing. "
                    "Kept in a separate category so they do not pollute other albums."
                ),
            ),
            # --- Date-based events (albums named YYYY, YYYY-MM, or YYYY-MM-DD) ---
            # This rule matches any album whose name starts with a date, which is a
            # common convention for event albums (holidays, trips, birthdays, etc.).
            ClassificationRule(
                album_name_patterns=[r"^\d{4}(-\d{2}(-\d{2})?)?"],
                description="Event albums identified by a date prefix in the album name.",
            ),
        ],
        # Tag written to assets that match no rule (need attention)
        autotag_unknown=_AUTOTAG_OUTPUT_UNKNOWN,
        # Tag written to assets that match more than one rule (ambiguous)
        autotag_conflict=_AUTOTAG_OUTPUT_CONFLICT,
    ),
    # -------------------------------------------------------------------------
    # DUPLICATE PROCESSING: Sync metadata between assets Immich considers duplicates.
    #
    # When Immich detects two assets as duplicates, this feature propagates
    # albums, tags, and date corrections between them so both stay in sync.
    # Conflicts (e.g. duplicates in different albums) are flagged with output tags.
    # -------------------------------------------------------------------------
    duplicate_processing=DuplicateProcessingConfig(
        description=(
            "Propagate albums, tags, and dates between assets that Immich has "
            "identified as duplicates, and flag any inconsistencies."
        ),
        # Tag for duplicates where the two copies belong to different albums
        autotag_album_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_ALBUM_CONFLICT,
        # Tag for duplicates with conflicting classification
        autotag_classification_conflict=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        # Prefix used when tagging each individual conflict group
        autotag_classification_conflict_prefix=_AUTOTAG_OUTPUT_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX,
        # Tag for assets where multiple candidate folders were found during album detection
        autotag_album_detection_conflict=_AUTOTAG_OUTPUT_ALBUM_DETECTION_CONFLICT,
        date_correction=DateCorrectionConfig(
            # Attempt to correct the asset date using the filename or folder name
            enabled=True,
            # Timezone assumed when a date string contains no timezone info
            extraction_timezone="UTC",
        ),
    ),
    # -------------------------------------------------------------------------
    # ALBUM DATE CONSISTENCY: Flag assets whose date differs from their album's date.
    #
    # Many event albums are named with a date (e.g. "2024-07-15 Beach trip").
    # This feature extracts that date and checks whether every asset in the album
    # falls within `threshold_days` of it. Mismatches are tagged for review.
    #
    # Suggested workflow: start with a large threshold (180 days) and progressively
    # tighten it (90 → 60 → 30 → 7) as you fix mismatches.
    # -------------------------------------------------------------------------
    album_date_consistency=AlbumDateConsistencyConfig(
        description=(
            "Check that assets in date-named albums are temporally close to the "
            "album's date; flag outliers with an output tag for review."
        ),
        enabled=True,
        autotag_album_date_mismatch=_AUTOTAG_OUTPUT_ALBUM_DATE_MISMATCH,
        threshold_days=180,  # Start wide; reduce gradually as mismatches are fixed
    ),
    # -------------------------------------------------------------------------
    # ALBUM DETECTION FROM FOLDERS: Auto-create albums based on library folder paths.
    #
    # When enabled, autotag looks at the folder where each asset is stored and
    # tries to assign (or create) a matching album. Useful if your files are
    # already organised into event folders on disk.
    #
    # excluded_paths: regex patterns for folder paths that should be ignored
    # (e.g. WhatsApp media dumps that should not become albums).
    # -------------------------------------------------------------------------
    album_detection_from_folders=AlbumDetectionFromFoldersConfig(
        description=(
            "Assign or create albums based on the folder path of each asset "
            "in the library. Excluded paths are skipped."
        ),
        enabled=False,
        excluded_paths=[r"whatsapp"],  # Add more patterns as needed
    ),
    # Create a generic daily album (e.g. "2024-07-15") for assets that are not
    # yet assigned to any album. You can rename or reorganise these later.
    create_album_from_date_if_missing=True,
    # -------------------------------------------------------------------------
    # ALBUM PERMISSIONS: Automatically share albums with user groups.
    #
    # Define groups of Immich users (by email) and rules that share albums with
    # those groups when the album name contains a specific keyword.
    #
    # Example: any album containing "family" in its name will be shared with
    # everyone in the "family" group. If a user is removed from the group,
    # they also lose access to those albums on the next run.
    #
    # Steps:
    #   1. Replace the example email addresses with real Immich user emails.
    #   2. Add or remove groups and keywords to match your sharing needs.
    #   3. Set enabled=True.
    # -------------------------------------------------------------------------
    album_permissions=AlbumPermissionsConfig(
        description=(
            "Share albums with groups of users automatically based on keywords "
            "in the album name, instead of managing permissions one by one."
        ),
        enabled=True,
        user_groups=[
            UserGroup(
                name=_FAMILY,
                description="Family members who should see family albums",
                members=[
                    "grandpa@example.com",
                    "grandma@example.com",
                    "mother@example.com",
                ],
            ),
            UserGroup(
                name=_FRIENDS,
                description="Close friends who should see friends albums",
                members=[
                    "john@example.com",
                    "jane@example.com",
                ],
            ),
        ],
        selection_rules=[
            AlbumSelectionRule(
                name="Share albums with 'family' in the name",
                keyword=_FAMILY,
                groups=[_FAMILY],
                access="view",
            ),
            AlbumSelectionRule(
                name="Share albums with 'friends' in the name",
                keyword=_FRIENDS,
                groups=[_FRIENDS],
                access="view",
            ),
        ],
        # Log albums that do not match any sharing rule (useful for auditing)
        log_unmatched=True,
    ),
    # -------------------------------------------------------------------------
    # PERFORMANCE: Tune for production vs. development use.
    #
    # enable_type_checking=False disables @typechecked decorators, which gives
    # roughly a 50 % speed improvement in production.
    # Keep it True during development to catch type errors early.
    # -------------------------------------------------------------------------
    performance=PerformanceConfig(
        enable_type_checking=True,
    ),
)

if __name__ == "__main__":
    import pprint

    pprint.pprint(user_config.model_dump())
