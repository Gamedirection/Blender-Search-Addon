# SPDX-License-Identifier: MIT
"""Loads and searches the JSON registry of documented Blender UI items.

Search supports a category filter using a pipe: "category|item" searches
only inside entries whose category matches the left side, using the right
side as the search text. Typing "category|" with nothing after the pipe
lists every entry in that category. A plain search with no pipe still
finds items across every category, including ones that also belong to a
category someone could have searched for directly.

Every entry has a "locations" list, since one item can show up in more
than one editor (the eyedropper's Tab key, and the search results, both
rely on being able to check all of them). Older, single-location entries
(a single space_type/region_type/ui_path instead of a locations list) are
still accepted and are wrapped into a one-item list automatically.
"""

import json
import re
from pathlib import Path

import bpy

from .. import storage

_ENTRIES = {}
_LOADED = False

_REQUIRED_FIELDS = ("id", "title", "category", "description")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _registry_dir():
    return Path(__file__).parent


def _normalize_entry(entry):
    entry = dict(entry)
    if not entry.get("locations"):
        entry["locations"] = [{
            "space_type": entry.get("space_type"),
            "region_type": entry.get("region_type") or "WINDOW",
            "ui_path": entry.get("ui_path", ""),
        }]
    entry.setdefault("tags", [])
    entry.setdefault("images", [])
    entry.setdefault("gifs", [])
    entry.setdefault("videos", [])
    entry.setdefault("manual_url", "")
    return entry


def _has_valid_locations(entry):
    locations = entry.get("locations")
    if locations:
        return all(location.get("space_type") for location in locations)
    return bool(entry.get("space_type"))


def load_all(force=False):
    """Read every registry/*.json file, plus the user's own entries. Safe to call more than once."""
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
            if not _has_valid_locations(entry):
                print(f"[Blender Search] {path.name}: entry '{entry['id']}' has no valid location")
                continue
            entry = _normalize_entry(entry)
            entry["_source"] = "bundled"
            entries[entry["id"]] = entry

    for entry in storage.load_user_entries().get("entries", []):
        missing = [field for field in _REQUIRED_FIELDS if field not in entry]
        if missing:
            print(f"[Blender Search] your entry '{entry.get('id', '?')}' is missing {missing}")
            continue
        if not _has_valid_locations(entry):
            print(f"[Blender Search] your entry '{entry['id']}' has no valid location")
            continue
        entry = _normalize_entry(entry)
        entry["_source"] = "user"
        entries[entry["id"]] = entry

    _ENTRIES = entries
    _LOADED = True


def all_entries():
    load_all()
    return _ENTRIES


def get(entry_id):
    load_all()
    return _ENTRIES.get(entry_id)


def categories():
    load_all()
    return sorted({entry["category"] for entry in _ENTRIES.values()})


def entries_for_space(space_type, region_type=None):
    """Return registry entries with a location in this editor, preferring an exact region match."""
    load_all()
    results = [
        entry for entry in _ENTRIES.values()
        if any(location["space_type"] == space_type for location in entry["locations"])
    ]
    if region_type:
        exact = [
            entry for entry in results
            if any(
                location["space_type"] == space_type and location["region_type"] == region_type
                for location in entry["locations"]
            )
        ]
        if exact:
            return exact
    return results


def places_for_category(category, region_type_hint=None):
    """One representative entry per distinct editor sharing this category.

    Editors are ordered by when they were first seen while loading the
    registry, which is stable across calls. When an editor has more than
    one candidate entry/location in this category, prefer one matching
    region_type_hint.
    """
    load_all()
    by_space = {}
    order = []
    for entry in _ENTRIES.values():
        if entry["category"] != category:
            continue
        for location in entry["locations"]:
            space_type = location["space_type"]
            if space_type not in by_space:
                by_space[space_type] = []
                order.append(space_type)
            by_space[space_type].append((entry, location))

    places = []
    for space_type in order:
        candidates = by_space[space_type]
        if region_type_hint:
            exact = [pair for pair in candidates if pair[1]["region_type"] == region_type_hint]
            if exact:
                places.append(exact[0][0])
                continue
        places.append(candidates[0][0])
    return places


def _tokens(text):
    return set(_WORD_RE.findall(text.lower()))


def _ranked_search(entries, query, limit):
    query = query.strip().lower()
    if not query:
        return []

    query_tokens = _tokens(query)
    scored = []
    for entry in entries:
        haystack = " ".join((entry["title"], entry["category"], " ".join(entry.get("tags", []))))
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


def _search_in_category(category_query, item_query, limit):
    category_query = category_query.strip().lower()
    scoped = [entry for entry in _ENTRIES.values() if category_query in entry["category"].lower()]

    if not item_query.strip():
        scoped.sort(key=lambda entry: entry["title"])
        return scoped[:limit]

    return _ranked_search(scoped, item_query, limit)


def search(query, limit=20):
    """Score every entry against a query and return the best matches.

    Use "category|item" to filter to one category first, then search
    inside it. Plain text with no pipe searches every category at once.
    """
    load_all()
    query = query.strip()
    if not query:
        return []

    if "|" in query:
        category_part, _, item_part = query.partition("|")
        return _search_in_category(category_part, item_part, limit)

    return _ranked_search(_ENTRIES.values(), query, limit)


def _manual_map_hook():
    """Lets Blender's own native tooltip and right-click "Online Manual"
    link point at one of our entries' manual_url, for any operator or
    property (built-in or not) whose RNA identifier matches an entry's
    rna_hint. This does not identify a hovered widget for us; Blender
    resolves that itself and only calls this to look up a URL, if and when
    the user invokes its own "Online Manual" action. See
    bpy.utils.register_manual_map() for the mechanism.
    """
    pairs = []
    for entry in _ENTRIES.values():
        rna_hint = entry.get("rna_hint")
        manual_url = entry.get("manual_url")
        if not rna_hint or not manual_url:
            continue
        for key in ("operator", "property"):
            pattern = rna_hint.get(key)
            if pattern:
                pairs.append((pattern.lower(), manual_url))
    return "", pairs  # empty prefix; each "suffix" is already a full URL


def register():
    bpy.utils.register_manual_map(_manual_map_hook)


def unregister():
    bpy.utils.unregister_manual_map(_manual_map_hook)
