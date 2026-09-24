# SPDX-License-Identifier: MIT
"""Reads and writes this addon's user data: personal links, favorites, and recent items.

All of this lives outside the bundled registry, so it survives addon updates.
"""

import json
import os
import time
from pathlib import Path

import bpy

_LINKS_FILE_NAME = "personal_links.json"
_STATE_FILE_NAME = "search_state.json"
_SCHEMA_VERSION = 1
_RECENT_LIMIT = 50


def _data_dir():
    return Path(bpy.utils.user_resource('CONFIG', path="blender_search_addon", create=True))


def _read_json(file_name, default):
    path = _data_dir() / file_name
    if not path.exists():
        return default()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default()


def _write_json(file_name, data):
    path = _data_dir() / file_name
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp_path, path)


# Personal links, saved per registry item. A user can save as many as they want.

def _default_links():
    return {"schema_version": _SCHEMA_VERSION, "links": {}}


def load():
    data = _read_json(_LINKS_FILE_NAME, _default_links)
    data.setdefault("links", {})
    return data


def links_for(entry_id):
    return load().get("links", {}).get(entry_id, [])


def add_link(entry_id, label, url):
    data = load()
    data["links"].setdefault(entry_id, []).append({
        "label": label,
        "url": url,
        "added": time.strftime("%Y-%m-%d"),
    })
    _write_json(_LINKS_FILE_NAME, data)


def remove_link(entry_id, index):
    data = load()
    items = data["links"].get(entry_id, [])
    if 0 <= index < len(items):
        items.pop(index)
        if not items:
            data["links"].pop(entry_id, None)
        _write_json(_LINKS_FILE_NAME, data)


# Favorites and recent items. Used to prefill the search popup.

def _default_state():
    return {"schema_version": _SCHEMA_VERSION, "favorites": [], "recent": []}


def load_state():
    data = _read_json(_STATE_FILE_NAME, _default_state)
    data.setdefault("favorites", [])
    data.setdefault("recent", [])
    return data


def favorites():
    return list(load_state()["favorites"])


def is_favorite(entry_id):
    return entry_id in load_state()["favorites"]


def toggle_favorite(entry_id):
    data = load_state()
    if entry_id in data["favorites"]:
        data["favorites"].remove(entry_id)
        is_now_favorite = False
    else:
        data["favorites"].append(entry_id)
        is_now_favorite = True
    _write_json(_STATE_FILE_NAME, data)
    return is_now_favorite


def recent(limit=_RECENT_LIMIT):
    return list(load_state()["recent"][:limit])


def record_recent(entry_id, limit=_RECENT_LIMIT):
    data = load_state()
    items = data["recent"]
    if entry_id in items:
        items.remove(entry_id)
    items.insert(0, entry_id)
    del items[limit:]
    _write_json(_STATE_FILE_NAME, data)


# Entries a user creates themselves, kept separate from the bundled registry
# so an addon update never overwrites them, and so they can be exported.

_ENTRIES_FILE_NAME = "my_entries.json"


def _default_user_entries():
    return {"schema_version": _SCHEMA_VERSION, "entries": []}


def load_user_entries():
    data = _read_json(_ENTRIES_FILE_NAME, _default_user_entries)
    data.setdefault("entries", [])
    return data


def has_user_entry(entry_id):
    return any(entry.get("id") == entry_id for entry in load_user_entries()["entries"])


def add_user_entry(entry):
    """Add a new entry, or replace one with the same id."""
    data = load_user_entries()
    entries = [e for e in data["entries"] if e.get("id") != entry.get("id")]
    entries.append(entry)
    data["entries"] = entries
    _write_json(_ENTRIES_FILE_NAME, data)


def remove_user_entry(entry_id):
    data = load_user_entries()
    data["entries"] = [e for e in data["entries"] if e.get("id") != entry_id]
    _write_json(_ENTRIES_FILE_NAME, data)
