# SPDX-License-Identifier: MIT
"""Fetches and caches images, GIFs, and video thumbnails from their source URLs.

Nothing here blocks Blender's UI thread: every network call runs on a
background thread that only touches the filesystem. Once a file is cached,
normal code on the main thread loads it like any other file on disk.
"""

import hashlib
import os
import threading
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import bpy

_USER_AGENT = "Mozilla/5.0 (compatible; BlenderSearchAddon/1.0)"
_TIMEOUT = 20

_pending = set()
_status = {}
_lock = threading.Lock()

pack_state = {
    "checking": False,
    "estimated_bytes": 0,
    "unknown_count": 0,
    "checked_count": 0,
    "total_count": 0,
    "downloading": False,
    "done_count": 0,
    "blocked": False,
}


def online_access_allowed():
    """Blender's own "Allow Online Access" preference (added in 4.2). Older
    Blender versions do not have this attribute at all, so default to True
    there rather than assuming the newer, more restrictive behavior."""
    return getattr(bpy.app, "online_access", True)


def _cache_dir():
    # 'CACHE' is not a valid bpy.utils.user_resource() type (confirmed on
    # Blender 4.4: only 'DATAFILES', 'CONFIG', 'SCRIPTS', 'EXTENSIONS' are
    # accepted). Use a subfolder under 'CONFIG' instead, kept separate from
    # storage.py's personal_links.json and search_state.json.
    return Path(bpy.utils.user_resource('CONFIG', path="blender_search_addon/media_cache", create=True))


def _cache_key(url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    suffix = Path(urlparse(url).path).suffix
    if len(suffix) > 6:
        suffix = ""
    return digest + suffix


def cache_path(url):
    return _cache_dir() / _cache_key(url)


def is_cached(url):
    return cache_path(url).exists()


def status_for(url):
    """None (nothing wrong so far), "error", or "blocked"."""
    with _lock:
        return _status.get(url)


def _download_one(url):
    path = cache_path(url)
    if path.exists():
        return True
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
        data = response.read()

    # Note: if a single-item fetch and a pack download race on the exact
    # same URL, both threads write the same temp path. Worst case is a
    # cached file that fails to load once, self-healing on the next try.
    temp_path = Path(str(path) + ".part")
    temp_path.write_bytes(data)
    os.replace(temp_path, path)
    return True


def request_download(url):
    """Fetch a single URL in the background if it is not already cached or pending."""
    if is_cached(url):
        return

    if not online_access_allowed():
        with _lock:
            _status[url] = "blocked"
        return

    with _lock:
        if url in _pending:
            return
        _pending.add(url)
        _status.pop(url, None)

    def worker():
        try:
            _download_one(url)
            with _lock:
                _status.pop(url, None)
        except Exception as error:
            print(f"[Blender Search] Could not download {url}: {error}")
            with _lock:
                _status[url] = "error"
        finally:
            with _lock:
                _pending.discard(url)

    threading.Thread(target=worker, daemon=True).start()


def _content_length(url):
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            length = response.headers.get("Content-Length")
            return int(length) if length is not None else None
    except Exception as error:
        print(f"[Blender Search] Could not check size of {url}: {error}")
        return None


def all_media_urls():
    """Every image, GIF, and video thumbnail URL referenced by the registry."""
    from . import registry

    urls = []
    for entry in registry.all_entries().values():
        urls.extend(entry.get("images", []))
        urls.extend(entry.get("gifs", []))
        for video in entry.get("videos", []):
            if isinstance(video, dict) and video.get("thumbnail"):
                urls.append(video["thumbnail"])

    seen = set()
    unique_urls = []
    for url in urls:
        if url.startswith("http://") or url.startswith("https://"):
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
    return unique_urls


def start_size_check():
    if pack_state["checking"]:
        return
    if not online_access_allowed():
        pack_state["blocked"] = True
        return
    pack_state["blocked"] = False
    urls = [url for url in all_media_urls() if not is_cached(url)]
    pack_state.update({
        "checking": True,
        "estimated_bytes": 0,
        "unknown_count": 0,
        "checked_count": 0,
        "total_count": len(urls),
    })

    def worker():
        total = 0
        unknown = 0
        for index, url in enumerate(urls, start=1):
            size = _content_length(url)
            if size is None:
                unknown += 1
            else:
                total += size
            pack_state["estimated_bytes"] = total
            pack_state["unknown_count"] = unknown
            pack_state["checked_count"] = index
        pack_state["checking"] = False

    threading.Thread(target=worker, daemon=True).start()


def start_pack_download():
    if pack_state["downloading"]:
        return
    if not online_access_allowed():
        pack_state["blocked"] = True
        return
    pack_state["blocked"] = False
    urls = [url for url in all_media_urls() if not is_cached(url)]
    pack_state.update({
        "downloading": True,
        "done_count": 0,
        "total_count": len(urls),
    })

    def worker():
        for url in urls:
            try:
                _download_one(url)
            except Exception as error:
                print(f"[Blender Search] Could not download {url}: {error}")
            pack_state["done_count"] += 1
        pack_state["downloading"] = False

    threading.Thread(target=worker, daemon=True).start()


def cached_size_bytes():
    total = 0
    cache_dir = _cache_dir()
    if cache_dir.exists():
        for path in cache_dir.glob("*"):
            if path.is_file():
                total += path.stat().st_size
    return total


def clear_cache():
    cache_dir = _cache_dir()
    if not cache_dir.exists():
        return
    for path in cache_dir.glob("*"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                pass


def format_size(num_bytes):
    size = float(num_bytes)
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
