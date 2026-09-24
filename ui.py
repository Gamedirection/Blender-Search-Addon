# SPDX-License-Identifier: MIT
"""Sidebar panel, the search popup, and the shared popup layout for a registry entry."""

import textwrap
from pathlib import Path

import bpy
import bpy.utils.previews

from . import storage
from . import registry
from . import preferences
from . import media

_preview_collections = {}


def _preview_collection():
    pcoll = _preview_collections.get("main")
    if pcoll is None:
        pcoll = bpy.utils.previews.new()
        _preview_collections["main"] = pcoll
    return pcoll


def _load_preview(key, path):
    pcoll = _preview_collection()
    if key in pcoll:
        return pcoll[key].icon_id
    if not path.exists():
        return 0
    try:
        return pcoll.load(key, str(path), 'IMAGE').icon_id
    except Exception:
        return 0


def _icon_id_from_bundled(relative_path):
    """Load a picture bundled with the addon under resources/. Only shows the first frame of a GIF."""
    path = Path(__file__).parent / "resources" / relative_path
    return _load_preview(relative_path, path)


def _icon_id_for_url(url):
    """Load a cached picture for this URL. Only shows the first frame of a GIF.

    Returns 0 if it is not cached yet. If internet media is allowed, this
    also starts a background download so it is ready next time.
    """
    path = media.cache_path(url)
    if path.exists():
        return _load_preview(url, path)

    prefs = preferences.get_prefs()
    if prefs is None or prefs.allow_internet_media:
        media.request_download(url)
    return 0


def _draw_media_thumbnail(layout, source, note=None):
    """Draw one picture, whether it comes from a URL or a path bundled with the addon."""
    is_remote = source.startswith("http://") or source.startswith("https://")
    icon_id = _icon_id_for_url(source) if is_remote else _icon_id_from_bundled(source)

    if icon_id:
        layout.template_icon(icon_value=icon_id, scale=6.0)
        if note:
            layout.label(text=note)
        return

    if not is_remote:
        layout.label(text="Picture not found: " + source, icon='ERROR')
        return

    prefs = preferences.get_prefs()
    if prefs is not None and not prefs.allow_internet_media:
        layout.label(text="Not shown. Internet media is turned off.", icon='INFO')
    else:
        layout.label(text="Loading picture...")
    props = layout.operator("wm.url_open", text="Open Picture in Browser", icon='URL')
    props.url = source


def _draw_favorite_button(layout, entry_id):
    is_fav = storage.is_favorite(entry_id)
    props = layout.operator(
        "searchaddon.toggle_favorite",
        text="",
        icon='PINNED' if is_fav else 'UNPINNED',
        depress=is_fav,
    )
    props.entry_id = entry_id


def draw_entry_info(layout, entry, exact=True):
    """Draw description, media, the manual link, and personal links for one entry."""
    if not exact:
        layout.label(text="Closest known match in this area", icon='INFO')

    box = layout.box()
    header = box.row(align=True)
    _draw_favorite_button(header, entry["id"])
    header.label(text=entry["title"], icon='VIEWZOOM')

    for line in textwrap.wrap(entry.get("description", ""), width=42) or [""]:
        box.label(text=line)

    prefs = preferences.get_prefs()
    show_images = prefs is None or prefs.show_images
    show_gifs = prefs is None or prefs.show_gifs
    show_videos = prefs is None or prefs.show_videos

    if show_images:
        for image_source in entry.get("images", []):
            _draw_media_thumbnail(box, image_source)

    if show_gifs:
        for gif_source in entry.get("gifs", []):
            _draw_media_thumbnail(box, gif_source, note="First frame shown. GIFs do not play in this popup.")

    if show_videos:
        for video in entry.get("videos", []):
            if isinstance(video, str):
                video = {"path": video}
            label = video.get("label") or "Video"
            thumbnail = video.get("thumbnail")
            if thumbnail:
                _draw_media_thumbnail(box, thumbnail)
            row = box.row()
            row.label(text=label)
            if video.get("url"):
                props = row.operator("wm.url_open", text="Video", icon='PLAY')
                props.url = video["url"]
            elif video.get("path"):
                props = row.operator("searchaddon.play_video", text="Video", icon='PLAY')
                props.relative_path = video["path"]

    if entry.get("manual_url"):
        props = box.operator("wm.url_open", text="Open Blender Manual", icon='URL')
        props.url = entry["manual_url"]

    links = storage.links_for(entry["id"])
    if links:
        box.separator()
        box.label(text="Your links")
        for index, link in enumerate(links):
            row = box.row(align=True)
            open_props = row.operator("wm.url_open", text=link.get("label") or link["url"], icon='URL')
            open_props.url = link["url"]
            remove_props = row.operator("searchaddon.remove_personal_link", text="", icon='X')
            remove_props.entry_id = entry["id"]
            remove_props.index = index

    add_props = box.operator("searchaddon.add_personal_link", text="Add Your Own Link", icon='ADD')
    add_props.entry_id = entry["id"]


def _draw_result_row(layout, entry):
    row = layout.row(align=True)
    _draw_favorite_button(row, entry["id"])
    select_props = row.operator("searchaddon.jump_to_entry", text=entry["title"])
    select_props.entry_id = entry["id"]


def _open_space_types(context):
    types = set()
    window = context.window
    if window is not None:
        for area in window.screen.areas:
            types.add(area.type)
    return types


def _draw_grouped_results(layout, context):
    shown_ids = set()

    favorite_entries = [registry.get(i) for i in storage.favorites()]
    favorite_entries = [e for e in favorite_entries if e is not None]
    if favorite_entries:
        layout.label(text="Favorite", icon='PINNED')
        for entry in favorite_entries:
            _draw_result_row(layout, entry)
            shown_ids.add(entry["id"])

    recent_entries = [registry.get(i) for i in storage.recent() if i not in shown_ids]
    recent_entries = [e for e in recent_entries if e is not None]
    if recent_entries:
        layout.label(text="Recent", icon='RECOVER_LAST')
        for entry in recent_entries:
            _draw_result_row(layout, entry)
            shown_ids.add(entry["id"])

    on_screen_types = _open_space_types(context)
    on_screen_entries = [
        entry for entry in registry.all_entries().values()
        if entry["id"] not in shown_ids and entry["space_type"] in on_screen_types
    ]
    on_screen_entries.sort(key=lambda entry: entry["title"])
    if on_screen_entries:
        layout.label(text="On-Screen")
        for entry in on_screen_entries[:10]:
            _draw_result_row(layout, entry)

    if not favorite_entries and not recent_entries and not on_screen_entries:
        layout.label(text="Type to search, or favorite items to see them here", icon='INFO')


def draw_search_popover(popup_self, context):
    wm = context.window_manager
    layout = popup_self.layout
    layout.prop(wm, "search_addon_query", text="", icon='VIEWZOOM')

    query = wm.search_addon_query.strip()
    if not query:
        _draw_grouped_results(layout, context)
        return

    results = registry.search(query, limit=20)
    if not results:
        layout.label(text="No matches", icon='INFO')
        return
    for entry in results:
        _draw_result_row(layout, entry)


class SEARCHADDON_PT_sidebar(bpy.types.Panel):
    bl_label = "Search"
    bl_idname = "SEARCHADDON_PT_sidebar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Search"

    def draw(self, context):
        layout = self.layout
        layout.operator("searchaddon.open_search", icon='VIEWZOOM')
        layout.operator(
            "searchaddon.eyedropper",
            icon='EYEDROPPER',
            depress=context.window_manager.search_addon_eyedropper_active,
        )
        layout.operator("searchaddon.report_issue", icon='URL')


def _draw_help_menu(self, context):
    self.layout.separator()
    self.layout.operator("searchaddon.open_search", icon='VIEWZOOM', text="Search Blender")


classes = (SEARCHADDON_PT_sidebar,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_help.append(_draw_help_menu)


def unregister():
    bpy.types.TOPBAR_MT_help.remove(_draw_help_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for pcoll in _preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    _preview_collections.clear()
