#!/usr/bin/env python3
"""Print one version's section from CHANGELOG.md.

Used by the release workflow to fill in a GitHub release's notes
automatically, so the changelog only needs to be written once.
"""
import sys
from pathlib import Path


def section_for(text, version=None):
    lines = text.splitlines()

    start = None
    end = len(lines)
    for index, line in enumerate(lines):
        if not line.startswith("## ["):
            continue
        if start is None:
            if version is not None:
                matches = f"[{version}]" in line
            else:
                # No arg: the latest released section, skipping "Unreleased".
                matches = "[Unreleased]" not in line
            if matches:
                start = index + 1
            continue
        end = index
        break

    if start is None:
        return ""
    return "\n".join(lines[start:end]).strip()


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else None
    text = Path("CHANGELOG.md").read_text(encoding="utf-8")
    print(section_for(text, version))


if __name__ == "__main__":
    main()
