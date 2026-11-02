#!/usr/bin/env python3
"""Apply i18n tokens to mod_browser.cpp (Alexgg1014 NX Edition).

Replaces exact quoted string literals with [TOKEN] placeholders.
Reuses keys already present in res/i18n/en.xml where the English matches.
Aborts if any literal's occurrence count differs from the expectation.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src/dusk/ui/mod_browser.cpp"

# (literal_without_quotes, KEY, expected_occurrences)
REPLACEMENTS = [
    # --- sort options
    ("Featured", "FEATURED", 1),
    ("Recently updated", "RECENTLY_UPDATED", 1),
    ("Most downloaded", "MOST_DOWNLOADED", 1),
    ("Newest", "NEWEST", 1),
    ("Name", "MODS_SORT_NAME", 1),
    # --- navigation / generic buttons
    ("Back", "BACK", 4),
    ("Previous", "PREVIOUS", 2),
    ("Next", "NEXT", 2),
    ("Retry", "MOD_RETRY", 2),
    ("Install", "INSTALL", 1),
    ("Update", "UPDATE", 1),
    ("All", "ALL", 1),
    ("Search", "SEARCH", 1),
    ("Available", "AVAILABLE", 1),
    ("Installed", "INSTALLED", 2),
    ("Unavailable", "UNAVAILABLE", 2),
    # NOTE: "Category" is NOT replaced globally - one occurrence is a search
    # filter logic key (.key = "Category") that must stay untranslated.
    # --- states / badges
    ("Update available", "UPDATE_AVAILABLE_MODS", 1),
    ("Switch build included", "MODS_SWITCH_BUILD_INCLUDED", 1),
    ("Incompatible with this build", "MODS_INCOMPATIBLE_BUILD", 1),
    ("A required provider is unavailable", "MODS_PROVIDER_UNAVAILABLE", 1),
    ("Queued", "QUEUED", 1),
    ("Resume", "RESUME", 1),
    ("Official", "OFFICIAL", 1),
    ("Uncategorized", "UNCATEGORIZED", 3),
    # --- headers / sections
    ("Browse Mods", "BROWSE_MODS", 1),
    ("Screenshots", "SCREENSHOTS", 1),
    ("Dependencies", "DEPENDENCIES", 1),
    ("Version", "VERSION", 1),
    ("Last updated", "LAST_UPDATED", 1),
    ("License", "LICENSE", 1),
    ("Dusklight services", "DUSKLIGHT_SERVICES", 1),
    ("Sort by", "SORT_BY", 1),
    ("Compatible only", "COMPATIBLE_ONLY", 1),
    ("All mods", "ALL_MODS", 2),
    ("Changelog ", "CHANGELOG", 1),
    # --- progress / status
    ("Verifying\u2026", "MODS_VERIFYING", 1),
    ("Installing\u2026", "MODS_INSTALLING", 1),
    ("Checking\u2026", "CHECKING", 1),
    ("Check for updates", "MODS_CHECK_FOR_UPDATES", 1),
    ("Checking package integrity", "MODS_CHECKING_INTEGRITY", 1),
    ("Applying package", "MODS_APPLYING_PACKAGE", 1),
    ("Retrying mod activation", "MODS_RETRYING_ACTIVATION", 1),
    ("Restart to finish", "MODS_RESTART_TO_FINISH", 1),
    ("Retry download", "RETRY_DOWNLOAD", 1),
    ("Retry package", "RETRY_PACKAGE", 1),
    ("Retry activation", "RETRY_ACTIVATION", 1),
    ("View download", "VIEW_DOWNLOAD", 1),
    ("View compatible update", "MODS_VIEW_COMPATIBLE_UPDATE", 1),
    ("View downloads & installs", "MODS_VIEW_DOWNLOADS", 1),
    ("Open in browser", "OPEN_IN_BROWSER", 2),
    ("Requires bundling", "REQUIRES_BUNDLING", 2),
    ("Contains native code; requires bundling.", "CONTAINS_NATIVE_CODE_REQUIRES_BUNDLING", 1),
    ("The installed version cannot be compared.", "MODS_VERSION_NOT_COMPARABLE", 1),
    # --- errors / empty states
    ("Could not start download", "COULD_NOT_START_DOWNLOAD", 1),
    ("The catalog download descriptor is invalid.", "MODS_DESCRIPTOR_INVALID", 1),
    ("The mod request failed.", "THE_MOD_REQUEST_FAILED", 2),
    ("The catalog request failed.", "THE_CATALOG_REQUEST_FAILED", 2),
    ("Package preparation failed", "PACKAGE_PREPARATION_FAILED", 1),
    ("Activation failed", "ACTIVATION_FAILED", 1),
    ("No description provided.", "NO_DESCRIPTION_PROVIDED", 1),
    ("No changelog was provided.", "NO_CHANGELOG_WAS_PROVIDED", 1),
    ("This build has no HTTP backend.", "THIS_BUILD_HAS_NO_HTTP_BACKEND", 1),
    ("Loading catalog", "LOADING_CATALOG", 1),
    ("Fetching published mods...", "FETCHING_PUBLISHED_MODS", 1),
    ("Fetching mod details and images...", "FETCHING_MOD_DETAILS_AND_IMAGES", 1),
    ("Could not load mods", "COULD_NOT_LOAD_MODS", 1),
    ("Catalog unavailable", "CATALOG_UNAVAILABLE", 1),
    ("No mods found", "NO_MODS_FOUND", 1),
    ("Try changing the search or category.", "MODS_TRY_CHANGING_SEARCH", 1),
    ("Network error \u00b7 keeps retrying itself", "NETWORK_ERROR_KEEPS_RETRYING_ITSELF", 1),
    # --- format strings (keep {} placeholders)
    ("{} required \u00b7 Available", "MODS_DEP_AVAILABLE", 1),
    ("{} required", "MODS_DEP_REQUIRED", 1),
    ("{} ahead \u00b7 view downloads", "MODS_QUEUE_AHEAD", 1),
    ("Next \u00b7 view downloads", "MODS_NEXT_VIEW_DOWNLOADS", 1),
    ("{} kept on disk", "MODS_KEPT_ON_DISK", 1),
    ("Retrying in {}s", "MODS_RETRYING_IN", 1),
    ("Installed \u00b7 {} \u00b7 {}", "MODS_INSTALLED_STATE", 1),
    ("v{} installed \u00b7 restart the game to run it", "MODS_INSTALLED_RESTART", 1),
    ("Could not load {}", "MODS_COULD_NOT_LOAD", 1),
    ("Loading {}", "MODS_LOADING", 1),
    ("The mod request failed: {}", "MODS_REQUEST_FAILED_WITH", 1),
    ("by {}", "MODS_BY_AUTHOR", 1),
    ("Page {} of {}", "MODS_PAGE_OF", 1),
    ("{} mods \u00b7 sorted by {}", "MODS_SORTED_BY", 1),
    ("Tested on Switch with this build. {}", "MODS_STATUS_TESTED", 1),
    ("Installs on Switch but stays inactive. {}", "MODS_STATUS_INACTIVE", 1),
    ("Incompatible with this build. {}", "MODS_STATUS_INCOMPATIBLE", 1),
    ("Unverified on Switch. {}", "MODS_STATUS_UNVERIFIED", 1),
    (" downloads", "MODS_DOWNLOADS_SUFFIX", 1),
    (" endorsements", "MODS_ENDORSEMENTS_SUFFIX", 1),
]

# Contextual replacements: (exact substring, replacement, KEY)
# Used where the bare literal is ambiguous (e.g. also used as a logic key).
CONTEXTUAL = [
    ('detailList, "Category",', 'detailList, "[CATEGORY]",', "CATEGORY"),
]

# Multi-line concatenated literals: replace the whole fmt::format(...) call.
MULTILINE = [
    (
        '''fmt::format("Installs the catalog's Linux build, which runs through the compatibility layer. "
                               "This release also has a Switch package (v{}) tested on the console: to use it "
                               "instead, copy it from the release zip into sdmc:/switch/dusklight/mods/.",
                bundled);''',
        '''fmt::format("[MODS_SWITCH_LINUX_INSTALL]",
                bundled);''',
        "MODS_SWITCH_LINUX_INSTALL",
    ),
    (
        '''fmt::format("Newer than this build's own Switch package (v{}). Installing it replaces that one with "
                           "the catalog's Linux build, which runs through the compatibility layer. To go back, copy "
                           "the Switch package from the release zip into sdmc:/switch/dusklight/mods/.",
            bundled);''',
        '''fmt::format("[MODS_SWITCH_NEWER_THAN_BUNDLED]",
            bundled);''',
        "MODS_SWITCH_NEWER_THAN_BUNDLED",
    ),
    (
        '''fmt::format("Secure connection failed: the server's certificate was not accepted. The console's "
                                 "date and time are probably wrong (it reads {}). Set them in System Settings > "
                                 "System > Date and Time, then press Retry.",
                date);''',
        '''fmt::format("[MODS_TLS_CERT_FAILED]",
                date);''',
        "MODS_TLS_CERT_FAILED",
    ),
]


def main() -> int:
    apply = "--apply" in sys.argv
    text = TARGET.read_text(encoding="utf-8")
    problems = []
    out = text

    for lit, key, expected in REPLACEMENTS:
        needle = f'"{lit}"'
        count = out.count(needle)
        if count != expected:
            problems.append(f"{key}: expected {expected} occurrence(s) of {needle!r}, found {count}")
            continue
        out = out.replace(needle, f'"[{key}]"')

    for old, new, key in CONTEXTUAL:
        count = out.count(old)
        if count != 1:
            problems.append(f"{key}: contextual anchor matched {count} time(s)")
            continue
        out = out.replace(old, new)

    for old, new, key in MULTILINE:
        count = out.count(old)
        if count != 1:
            problems.append(f"{key}: multiline anchor matched {count} time(s)")
            continue
        out = out.replace(old, new)

    if problems:
        print("ABORTED - no changes written:")
        for p in problems:
            print("  !", p)
        return 1

    replaced = text.count('"') - out.count('"')  # sanity only
    tokens = out.count('["')
    if apply:
        TARGET.write_text(out, encoding="utf-8")
        print(f"APPLIED. tokens now in file: {tokens}")
    else:
        print(f"DRY RUN OK. tokens that would be in file: {tokens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
