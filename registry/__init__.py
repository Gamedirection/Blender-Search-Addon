# SPDX-License-Identifier: MIT
"""Loads and searches the JSON registry of documented Blender UI items."""

import json
import re
from pathlib import Path

_ENTRIES = {}
_LOADED = False

_REQUIRED_FIELDS = (
    "id",
    "title",
    "category",
    "space_type",
    "region_type",
    "description",
    "manual_url",
)

_WORD_RE = re.compile(r"[a-z0-9]+")


def _registry_dir():
    return Path(__file__).parent


def load_all(force=False):
    """Read every registry/*.json file into memory. Safe to call more than once."""
    global _ENTRIES, _LOADED
    if _LOADED and not force:
        return

    entries = {}
    for path in sorted(_registry_dir().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"[Blender Search] Could not read {path.name}: {error}")
            continue

        for entry in data.get("entries", []):
            missing = [field for field in _REQUIRED_FIELDS if field not in entry]
            if missing:
                entry_id = entry.get("id", "?")
                print(f"[Blender Search] {path.name}: entry '{entry_id}' is missing {missing}")
                continue
            entries[entry["id"]] = entry

    _ENTRIES = entries
    _LOADED = True


def all_entries():
    load_all()
    return _ENTRIES


def get(entry_id):
    load_all()
    return _ENTRIES.get(entry_id)


def entries_for_space(space_type, region_type=None):
    """Return registry entries for an editor, preferring an exact region match."""
    load_all()
    results = [entry for entry in _ENTRIES.values() if entry["space_type"] == space_type]
    if region_type:
        exact = [entry for entry in results if entry["region_type"] == region_type]
        if exact:
            return exact
    return results


def _tokens(text):
    return set(_WORD_RE.findall(text.lower()))


def search(query, limit=20):
    """Score every entry against a query and return the best matches."""
    load_all()
    query = query.strip().lower()
    if not query:
        return []

    query_tokens = _tokens(query)
    scored = []
    for entry in _ENTRIES.values():
        haystack = " ".join((entry["title"], entry["category"], " ".join(entry.get("keywords", []))))
        haystack_tokens = _tokens(haystack)

        if query in entry["title"].lower():
            score = 3
        elif query_tokens & haystack_tokens:
            score = 2
        elif any(query in token for token in haystack_tokens):
            score = 1
        else:
            continue

        scored.append((score, entry["title"], entry))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [entry for _score, _title, entry in scored[:limit]]
