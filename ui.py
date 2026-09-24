# SPDX-License-Identifier: MIT
"""Sidebar panel and the shared popup layout for a registry entry."""

import textwrap
from pathlib import Path

import bpy
import bpy.utils.previews

from . import storage

_preview_collections = {}


def _preview_collection():
    pcoll = _preview_collections.get("main")
    if pcoll is None:
        pcoll = bpy.utils.previews.new()
        _preview_collections["main"] = pcoll
    return pcoll


def _icon_id_for(relative_path):
    pcoll = _preview_collection()
    if relative_path in pcoll:
        return pcoll[relative_path].icon_id
    path = Path(__file__).parent / "resources" / relative_path
    if not path.exists():
        return 0
    try:
        return pcoll.load(relative_path, str(path), 'IMAGE').icon_id
    except Exception:
        return 0


def draw_entry_info(layout, entry, exact=True):
    """Draw description, images, the manual link, and personal links for one entry."""
    if not exact:
        layout.label(text="Closest known match in this area", icon='INFO')

    box = layout.box()
    box.label(text=entry["title"], icon='VIEWZOOM')
    for line in textwrap.wrap(entry.get("description", ""), width=42) or [""]:
        box.label(text=line)

    for image_path in entry.get("images", []):
        icon_id = _icon_id_for(image_path)
        if icon_id:
            box.template_icon(icon_value=icon_id, scale=6.0)

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


classes = (SEARCHADDON_PT_sidebar,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for pcoll in _preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    _preview_collections.clear()
