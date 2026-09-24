# SPDX-License-Identifier: MIT
"""Reads and writes personal_links.json, kept outside the bundled registry."""

import json
import os
import time
from pathlib import Path

import bpy

_FILE_NAME = "personal_links.json"
_SCHEMA_VERSION = 1


def _storage_path():
    directory = bpy.utils.user_resource('CONFIG', path="blender_search_addon", create=True)
    return Path(directory) / _FILE_NAME


def load():
    path = _storage_path()
    if not path.exists():
        return {"schema_version": _SCHEMA_VERSION, "links": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": _SCHEMA_VERSION, "links": {}}
    data.setdefault("links", {})
    return data


def _save(data):
    path = _storage_path()
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp_path, path)


def links_for(entry_id):
    return load().get("links", {}).get(entry_id, [])


def add_link(entry_id, label, url):
    data = load()
    data["links"].setdefault(entry_id, []).append({
        "label": label,
        "url": url,
        "added": time.strftime("%Y-%m-%d"),
    })
    _save(data)


def remove_link(entry_id, index):
    data = load()
    items = data["links"].get(entry_id, [])
    if 0 <= index < len(items):
        items.pop(index)
        if not items:
            data["links"].pop(entry_id, None)
        _save(data)
