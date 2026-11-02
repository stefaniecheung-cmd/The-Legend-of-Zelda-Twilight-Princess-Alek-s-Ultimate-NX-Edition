#!/usr/bin/env python3
"""Fix parameterized mod_browser strings: never put {} inside a [TOKEN].

RmlUi translates a finished string, so fmt::format("[TOKEN]", args) would drop
arg  . Instead the token carries only the words, and the values are appended
with std::string concatenation (i18n::tr() gives the translated words).

Each pair below must match exactly once.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src/dusk/ui/mod_browser.cpp"

PAIRS = [
    # --- hardware verdict lines: "<verdict> <reason>"
    ('return fmt::format("[MODS_STATUS_TESTED]", found.reason);',
     'return i18n::tr("[MODS_STATUS_TESTED]") + found.reason;'),
    ('return fmt::format("[MODS_STATUS_INACTIVE]", found.reason);',
     'return i18n::tr("[MODS_STATUS_INACTIVE]") + found.reason;'),
    ('return fmt::format("[MODS_STATUS_INCOMPATIBLE]", found.reason);',
     'return i18n::tr("[MODS_STATUS_INCOMPATIBLE]") + found.reason;'),
    ('return fmt::format("[MODS_STATUS_UNVERIFIED]", found.reason);',
     'return i18n::tr("[MODS_STATUS_UNVERIFIED]") + found.reason;'),

    # --- "by <author>"
    ('fmt::format("[MODS_BY_AUTHOR]", mod.author.name)',
     'i18n::tr("[MODS_BY_AUTHOR]") + mod.author.name'),

    # --- detail fetch errors / loading
    ('mError = fmt::format("[MODS_REQUEST_FAILED_WITH]", exception.what());',
     'mError = i18n::tr("[MODS_REQUEST_FAILED_WITH]") + exception.what();'),
    ('append_status(status, fmt::format("[MODS_LOADING]", mSummary.name),',
     'append_status(status, i18n::tr("[MODS_LOADING]") + mSummary.name,'),
    ('append_status(status, fmt::format("[MODS_COULD_NOT_LOAD]", mSummary.name), mError);',
     'append_status(status, i18n::tr("[MODS_COULD_NOT_LOAD]") + mSummary.name, mError);'),

    # --- download queue captions
    ('caption = fmt::format("[MODS_QUEUE_AHEAD]", ahead);',
     'caption = std::to_string(ahead) + i18n::tr("[MODS_QUEUE_AHEAD]");'),
    ('caption = fmt::format("[MODS_KEPT_ON_DISK]", format_bytes(queued->completed));',
     'caption = format_bytes(queued->completed) + i18n::tr("[MODS_KEPT_ON_DISK]");'),
    ('label = fmt::format("[MODS_RETRYING_IN]", queued->retrySeconds);',
     'label = std::to_string(queued->retrySeconds) + i18n::tr("[MODS_RETRYING_IN]");'),
    ('caption = fmt::format("[MODS_INSTALLED_RESTART]", staged);',
     'caption = "v" + staged + i18n::tr("[MODS_INSTALLED_RESTART]");'),

    # --- installed caption: "<Installed> · <size> · <enabled|disabled>"
    ('''caption = fmt::format("[MODS_INSTALLED_STATE]", format_bytes(package_size()),
                    local != nullptr && local->active ? "enabled" : "disabled");''',
     '''caption = i18n::tr("[INSTALLED]") + " · " + format_bytes(package_size()) + " · " +
                    (local != nullptr && local->active ? i18n::tr("[ENABLED]") : i18n::tr("[DISABLED]"));'''),

    # --- Dusklight dependency rows
    ('''                dusklightProblems.empty() ?
                    fmt::format("[MODS_DEP_AVAILABLE]", requiredDusklight) :
                    fmt::format("[MODS_DEP_REQUIRED]", requiredDusklight));''',
     '''                dusklightProblems.empty()
                    ? std::to_string(requiredDusklight) + i18n::tr("[MODS_DEP_REQUIRED]") + " · " +
                          i18n::tr("[AVAILABLE]")
                    : std::to_string(requiredDusklight) + i18n::tr("[MODS_DEP_REQUIRED]"));'''),

    # --- "N mods · sorted by <label>"
    ('heading, "small", fmt::format("[MODS_SORTED_BY]", total, sort_label(mQuery.sort)));',
     'heading, "small",\n            std::to_string(total) + i18n::tr("[MODS_SORTED_BY]") + std::string(sort_label(mQuery.sort)));'),

    # --- pagination "Page N / M"
    ('''            append_text(label,
                fmt::format("[MODS_PAGE_OF]", mPage->pagination.page, mPage->pagination.pageCount));''',
     '''            append_text(label,
                i18n::tr("[MODS_PAGE_PREFIX]") + std::to_string(mPage->pagination.page) + " / " +
                    std::to_string(mPage->pagination.pageCount));'''),

    # --- long help paragraphs: split around the embedded version number
    ('''            return fmt::format("[MODS_SWITCH_LINUX_INSTALL]",
                bundled);''',
     '''            return i18n::tr("[MODS_SWITCH_LINUX_A]") + bundled + i18n::tr("[MODS_SWITCH_LINUX_B]");'''),
    ('''        return fmt::format("[MODS_SWITCH_NEWER_THAN_BUNDLED]",
            bundled);''',
     '''        return i18n::tr("[MODS_SWITCH_NEWER_A]") + bundled + i18n::tr("[MODS_SWITCH_NEWER_B]");'''),
    ('''            mError = fmt::format("[MODS_TLS_CERT_FAILED]",
                date);''',
     '''            mError = i18n::tr("[MODS_TLS_CERT_A]") + date + i18n::tr("[MODS_TLS_CERT_B]");'''),
]


def main() -> int:
    apply = "--apply" in sys.argv
    text = TARGET.read_text(encoding="utf-8")
    out = text
    problems = []
    for old, new in PAIRS:
        count = out.count(old)
        if count != 1:
            problems.append(f"matched {count}x: {old.splitlines()[0][:70]}")
            continue
        out = out.replace(old, new)

    if problems:
        print("ABORTED:")
        for p in problems:
            print("  !", p)
        return 1

    remaining = [l for l in out.split("\n") if 'fmt::format("[MODS_' in l or 'fmt::format("[INSTALLED]' in l]
    if remaining:
        print("WARNING: possible leftover parameterized tokens:")
        for l in remaining:
            print("   ", l.strip()[:100])

    if apply:
        TARGET.write_text(out, encoding="utf-8")
        print(f"APPLIED {len(PAIRS)} rewrites")
    else:
        print(f"DRY RUN OK: {len(PAIRS)} rewrites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
