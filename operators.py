# SPDX-License-Identifier: MIT
"""Operators: search popup, jump to result, eyedropper, favorites, personal
links, and the New Entry contribution workflow (create, export, import)."""

import json
import re
import time
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import registry
from . import storage
from . import overlay
from . import preferences
from . import media
from . import ui

_POINT_HIGHLIGHT_HALF_SIZE = 26


def _current_workspace_name(context=None):
    ctx = context or bpy.context
    return ctx.workspace.name if ctx.workspace else ""


def _point_for_current_layout(location, context=None):
    """A location's point, but only if it was captured in the workspace tab
    that is active right now. A pixel position is only meaningful in the
    specific workspace it was clicked in, since a different workspace can
    arrange or size even the same kind of editor differently."""
    point = (location or {}).get("point")
    if not point:
        return None
    if point.get("workspace") != _current_workspace_name(context):
        return None
    return point


def _location_rect(region, location, context=None):
    """The box to highlight for one location. Blender does not give addons a
    reliable way to find one button's exact position, but a location saved
    with a precise spot (captured by clicking, see SEARCHADDON_OT_pick_location)
    can highlight a small box there instead of the whole region, as long as
    the current workspace tab matches the one it was captured in."""
    point = _point_for_current_layout(location, context)
    if point:
        px = point["x"] * region.width
        py = point["y"] * region.height
        half = _POINT_HIGHLIGHT_HALF_SIZE
        return (px - half, py - half, px + half, py + half)
    return (0, 0, region.width, region.height)


class SEARCHADDON_OT_open_search(bpy.types.Operator):
    bl_idname = "searchaddon.open_search"
    bl_label = "Search Blender"
    bl_description = "Search for a documented Blender feature, panel, or setting"

    # A plain popover's draw function does not reliably redraw on every
    # keystroke. An operator-owned property inside invoke_popup does, since
    # Blender re-runs draw() after every property change while it is open.
    query: StringProperty(name="Search", default="", options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self.query = ""
        return context.window_manager.invoke_popup(self, width=400)

    def draw(self, context):
        ui.draw_search_popup(self, context)

    def execute(self, context):
        return {'FINISHED'}


class SEARCHADDON_OT_jump_to_entry(bpy.types.Operator):
    bl_idname = "searchaddon.jump_to_entry"
    bl_label = "Show Result"
    bl_description = "Highlight this item if its editor is open"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty()

    @staticmethod
    def _find_region(area, region_type):
        return (
            next((r for r in area.regions if r.type == region_type), None)
            or next((r for r in area.regions if r.type == 'WINDOW'), None)
        )

    def _highlight(self, area, region, location=None, revert=None):
        overlay.set_target(region, _location_rect(region, location), revert=revert)
        area.tag_redraw()
        bpy.app.timers.register(overlay.clear_target, first_interval=4.0)
        bpy.ops.searchaddon.watch_highlight('INVOKE_DEFAULT', entry_id=self.entry_id, duration=4.0)

    def execute(self, context):
        entry = registry.get(self.entry_id)
        if entry is None:
            self.report({'ERROR'}, "That item is no longer in the registry")
            return {'CANCELLED'}

        storage.record_recent(entry["id"])

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                for location in entry["locations"]:
                    if area.type != location["space_type"]:
                        continue
                    region = self._find_region(area, location["region_type"])
                    if region is None:
                        continue
                    self._highlight(area, region, location=location)
                    self.report({'INFO'}, "Highlighted: " + entry["title"])
                    return {'FINISHED'}

        prefs = preferences.get_prefs(context)
        if prefs is not None and prefs.auto_reveal_offscreen and entry["locations"]:
            window = context.window
            areas = list(window.screen.areas) if window else []
            if areas:
                target_area = max(areas, key=lambda a: a.width * a.height)
                previous_type = target_area.type
                location = entry["locations"][0]
                target_area.type = location["space_type"]
                region = self._find_region(target_area, location["region_type"])
                if region is not None:
                    self._highlight(target_area, region, location=location, revert=(target_area, previous_type))
                    self.report({'INFO'}, "Revealed: " + entry["title"])
                    return {'FINISHED'}
                target_area.type = previous_type

        editor_names = sorted({
            location["space_type"].replace("_", " ").title() for location in entry["locations"]
        })
        self.report({'WARNING'}, "Open one of these to see this: " + ", ".join(editor_names))
        return {'CANCELLED'}


class SEARCHADDON_OT_watch_highlight(bpy.types.Operator):
    bl_idname = "searchaddon.watch_highlight"
    bl_label = "Watch Highlight"
    bl_description = "Show a popup when the user hovers a highlighted item"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty()
    duration: FloatProperty(default=4.0)

    def invoke(self, context, event):
        self._start = time.monotonic()
        self._hover_start = None
        self._shown = False
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if time.monotonic() - self._start >= self.duration:
            return self._finish(context)

        region = overlay.get_target_region()
        inside = False
        if region is not None and event.mouse_x is not None:
            inside = (
                region.x <= event.mouse_x <= region.x + region.width
                and region.y <= event.mouse_y <= region.y + region.height
            )

        if inside:
            if self._hover_start is None:
                self._hover_start = time.monotonic()
            elif not self._shown and time.monotonic() - self._hover_start >= 0.4:
                self._shown = True
                entry = registry.get(self.entry_id)
                if entry is not None:
                    def draw(popup_self, popup_context, entry=entry):
                        ui.draw_entry_info(popup_self.layout, entry, exact=True)
                    context.window_manager.popover(draw, ui_units_x=16)
        else:
            self._hover_start = None
            self._shown = False

        return {'PASS_THROUGH'}

    def _finish(self, context):
        if getattr(self, "_timer", None) is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        return {'CANCELLED'}


def _area_region_at(context, mouse_x, mouse_y):
    window = context.window
    if window is None:
        return None, None
    for area in window.screen.areas:
        if not (area.x <= mouse_x <= area.x + area.width and area.y <= mouse_y <= area.y + area.height):
            continue
        for region in area.regions:
            if region.width == 0 or region.height == 0:
                continue
            if region.x <= mouse_x <= region.x + region.width and region.y <= mouse_y <= region.y + region.height:
                return area, region
    return None, None


class SEARCHADDON_OT_eyedropper(bpy.types.Operator):
    bl_idname = "searchaddon.eyedropper"
    bl_label = "Eyedropper"
    bl_description = (
        "Hover over Blender's interface to learn about the nearest documented item. "
        "Shift+Tab cycles other items in this same area. Tab cycles other places "
        "this item's category shows up. Shift+Click starts a new entry for what "
        "you are hovering"
    )

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.search_addon_eyedropper_active:
            # A modal loop is already running. Turn it off instead of starting a second one.
            wm.search_addon_eyedropper_active = False
            return {'CANCELLED'}

        wm.search_addon_eyedropper_active = True
        context.window.cursor_modal_set('EYEDROPPER')
        self._timer = wm.event_timer_add(0.1, window=context.window)
        self._hover_area = None
        self._hover_region = None
        self._hover_point = None
        self._hover_start = 0.0
        self._shown_for = None
        self._item_index = 0
        self._active_entry_id = None
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm = context.window_manager

        if not wm.search_addon_eyedropper_active:
            return self._finish(context)

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            wm.search_addon_eyedropper_active = False
            return self._finish(context)

        if event.type == 'MOUSEMOVE':
            area, region = _area_region_at(context, event.mouse_x, event.mouse_y)
            if area is not self._hover_area or region is not self._hover_region:
                self._hover_area = area
                self._hover_region = region
                self._hover_start = time.monotonic()
                self._shown_for = None
                self._item_index = 0
                self._active_entry_id = None
            if region is not None and region.width > 0 and region.height > 0:
                self._hover_point = (
                    (event.mouse_x - region.x) / region.width,
                    (event.mouse_y - region.y) / region.height,
                )
            else:
                self._hover_point = None

        if event.type == 'TAB' and event.value == 'PRESS':
            if event.shift:
                self._cycle_item(context)
            else:
                self._cycle_place(context)
            # Consume Tab (and Shift+Tab) so Blender does not also toggle Edit
            # Mode or switch workspace tabs underneath.
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS' and event.shift:
            if self._hover_area is not None and self._hover_region is not None:
                _start_new_entry(
                    context,
                    initial_location=(self._hover_area.type, self._hover_region.type),
                )
                wm.search_addon_eyedropper_active = False
                return self._finish(context)
            return {'RUNNING_MODAL'}

        if (
            event.type == 'TIMER'
            and self._hover_region is not None
            and self._shown_for is not self._hover_region
            and time.monotonic() - self._hover_start >= 0.6
        ):
            self._show_popup(context)

        return {'PASS_THROUGH'}

    def _ordered_by_proximity(self, matches):
        """When several documented items share this same area, show whichever
        one has a precise spot (see SEARCHADDON_OT_pick_location) closest to
        the cursor first, instead of an arbitrary order. Entries with no
        precise spot for this area sort after ones that have one."""
        if self._hover_point is None or self._hover_area is None or self._hover_region is None:
            return matches
        space_type = self._hover_area.type
        region_type = self._hover_region.type
        hx, hy = self._hover_point

        def distance(entry):
            best = None
            for location in entry["locations"]:
                if location["space_type"] != space_type or location["region_type"] != region_type:
                    continue
                point = _point_for_current_layout(location)
                if point is None:
                    continue
                d = (point["x"] - hx) ** 2 + (point["y"] - hy) ** 2
                if best is None or d < best:
                    best = d
            return best if best is not None else float("inf")

        return sorted(matches, key=distance)

    def _current_matches(self):
        if self._hover_area is None or self._hover_region is None:
            return []
        matches = registry.entries_for_space(self._hover_area.type, self._hover_region.type)
        return self._ordered_by_proximity(matches)

    def _current_reference_entry(self):
        """The entry Tab and Shift+Tab both treat as "the one you are looking at"."""
        if self._active_entry_id is not None:
            entry = registry.get(self._active_entry_id)
            if entry is not None:
                return entry

        matches = self._current_matches()
        if not matches:
            return None
        return matches[self._item_index % len(matches)]

    def _cycle_item(self, context):
        """Shift+Tab: the other items documented in the area under the cursor."""
        matches = self._current_matches()
        if not matches:
            return
        self._item_index = (self._item_index + 1) % len(matches)
        self._shown_for = None
        self._show_popup(context)

    def _cycle_place(self, context):
        """Tab: the other editors where this item's category also shows up."""
        entry = self._current_reference_entry()
        if entry is None:
            return
        region_type_hint = self._hover_region.type if self._hover_region is not None else None
        places = registry.places_for_category(entry["category"], region_type_hint=region_type_hint)
        if not places:
            return

        start_index = 0
        for index, place_entry in enumerate(places):
            if place_entry["id"] == entry["id"]:
                start_index = index
                break
        next_index = (start_index + 1) % len(places)
        self._shown_for = None
        self._show_place(context, places[next_index], next_index, len(places))

    def _show_popup(self, context):
        area = self._hover_area
        region = self._hover_region
        self._shown_for = region
        if area is None or region is None:
            return

        matches = self._current_matches()
        if not matches:
            return

        index = self._item_index % len(matches)
        entry = matches[index]
        matched_location = next(
            (
                location for location in entry["locations"]
                if location["space_type"] == area.type and location["region_type"] == region.type
            ),
            None,
        )
        footer = None
        if len(matches) > 1:
            footer = f"Shift+Tab for more items here ({index + 1} of {len(matches)})"

        self._display_entry(context, entry, matched_location is not None, footer)
        if matched_location is not None:
            overlay.set_target(region, _location_rect(region, matched_location))
            area.tag_redraw()
            bpy.app.timers.register(overlay.clear_target, first_interval=4.0)

    def _show_place(self, context, entry, index, total):
        footer = None
        if total > 1:
            editor_names = sorted({
                location["space_type"].replace("_", " ").title() for location in entry["locations"]
            })
            footer = f"Tab for other places ({index + 1} of {total}): {', '.join(editor_names)}"

        self._display_entry(context, entry, True, footer)
        self._highlight_if_open(context, entry)

    def _display_entry(self, context, entry, exact, footer_text):
        self._active_entry_id = entry["id"]

        def draw(popup_self, popup_context, entry=entry, exact=exact, footer_text=footer_text):
            ui.draw_entry_info(popup_self.layout, entry, exact=exact)
            if footer_text:
                popup_self.layout.label(text=footer_text, icon='TRIA_RIGHT')

        context.window_manager.popover(draw, ui_units_x=16)

    @staticmethod
    def _highlight_if_open(context, entry):
        """If Tab lands on an editor that happens to already be open, highlight
        it there too, even though the cursor never physically moved to it."""
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                for location in entry["locations"]:
                    if area.type != location["space_type"]:
                        continue
                    region = (
                        next((r for r in area.regions if r.type == location["region_type"]), None)
                        or next((r for r in area.regions if r.type == 'WINDOW'), None)
                    )
                    if region is None:
                        continue
                    overlay.set_target(region, _location_rect(region, location))
                    area.tag_redraw()
                    bpy.app.timers.register(overlay.clear_target, first_interval=4.0)
                    return

    def _finish(self, context):
        context.window_manager.search_addon_eyedropper_active = False
        try:
            context.window.cursor_modal_restore()
        except Exception:
            pass
        if getattr(self, "_timer", None) is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

        # Redraw right away so the sidebar's toggle button un-presses and the
        # cursor change is visible immediately, instead of waiting for the
        # next unrelated redraw.
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        return {'CANCELLED'}


class SEARCHADDON_OT_toggle_favorite(bpy.types.Operator):
    bl_idname = "searchaddon.toggle_favorite"
    bl_label = "Toggle Favorite"
    bl_description = "Add or remove this item from your favorites"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        storage.toggle_favorite(self.entry_id)
        return {'FINISHED'}


class SEARCHADDON_OT_play_video(bpy.types.Operator):
    bl_idname = "searchaddon.play_video"
    bl_label = "Play Video"
    bl_description = "Open this video with your system's default player"
    bl_options = {'INTERNAL'}

    relative_path: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        path = Path(__file__).parent / "resources" / self.relative_path
        if not path.exists():
            self.report({'ERROR'}, "Video file not found")
            return {'CANCELLED'}
        bpy.ops.wm.path_open(filepath=str(path))
        return {'FINISHED'}


class SEARCHADDON_OT_add_personal_link(bpy.types.Operator):
    bl_idname = "searchaddon.add_personal_link"
    bl_label = "Add a Personal Link"
    bl_description = "Save a link of your own for this item"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty(options={'HIDDEN'})
    label: StringProperty(name="Label", default="")
    url: StringProperty(name="URL", default="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "label")
        layout.prop(self, "url")

    def execute(self, context):
        url = self.url.strip()
        if not url:
            self.report({'ERROR'}, "Enter a URL")
            return {'CANCELLED'}
        storage.add_link(self.entry_id, self.label.strip() or url, url)
        return {'FINISHED'}


class SEARCHADDON_OT_remove_personal_link(bpy.types.Operator):
    bl_idname = "searchaddon.remove_personal_link"
    bl_label = "Remove Link"
    bl_description = "Delete this saved link"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty(options={'HIDDEN'})
    index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        storage.remove_link(self.entry_id, self.index)
        return {'FINISHED'}


def _poll_pack_state():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()
    if media.pack_state["checking"] or media.pack_state["downloading"]:
        return 0.3
    return None


def _start_ui_poll():
    bpy.app.timers.register(_poll_pack_state, first_interval=0.3)


class SEARCHADDON_OT_check_pack_size(bpy.types.Operator):
    bl_idname = "searchaddon.check_pack_size"
    bl_label = "Check Download Size"
    bl_description = "Estimate how much data the offline media pack will download"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        media.start_size_check()
        _start_ui_poll()
        return {'FINISHED'}


class SEARCHADDON_OT_download_pack(bpy.types.Operator):
    bl_idname = "searchaddon.download_pack"
    bl_label = "Download Offline Media Pack"
    bl_description = "Download every picture, GIF, and video thumbnail so they show without the internet. This can be large"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        media.start_pack_download()
        _start_ui_poll()
        return {'FINISHED'}


class SEARCHADDON_OT_clear_media_cache(bpy.types.Operator):
    bl_idname = "searchaddon.clear_media_cache"
    bl_label = "Clear Downloaded Media"
    bl_description = "Delete every picture, GIF, and video thumbnail this addon has downloaded"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        media.clear_cache()
        self.report({'INFO'}, "Cleared the downloaded media cache")
        return {'FINISHED'}


def _slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "entry"


def _clear_draft_description_text(wm):
    """The description is a real bpy.types.Text datablock (Blender has no
    multi-line string widget), used only as a scratchpad while drafting; its
    content is copied into the saved entry as a plain string. Remove it once
    a draft is done with it, so these do not pile up in bpy.data.texts."""
    text = wm.search_addon_draft_description_text
    if text is not None:
        try:
            bpy.data.texts.remove(text)
        except Exception:
            pass
        wm.search_addon_draft_description_text = None


def _reset_draft(wm):
    _clear_draft_description_text(wm)
    wm.search_addon_draft_editing_id = ""
    wm.search_addon_draft_title = ""
    wm.search_addon_draft_category = ""
    wm.search_addon_draft_tags = ""
    wm.search_addon_draft_manual_url = ""
    wm.search_addon_draft_locations.clear()
    wm.search_addon_draft_links.clear()


def _redraw_all(wm):
    for window in wm.windows:
        for area in window.screen.areas:
            area.tag_redraw()


def _start_new_entry(context, initial_location=None):
    wm = context.window_manager
    _reset_draft(wm)
    if initial_location is not None:
        space_type, region_type = initial_location
        item = wm.search_addon_draft_locations.add()
        item.space_type = space_type
        item.region_type = region_type
    wm.search_addon_compose_active = True
    _redraw_all(wm)


def _load_entry_into_draft(context, entry):
    """Fill the New Entry form with an existing entry of the user's own, so
    they can change it instead of starting over. Keeps the same id, since
    personal links, favorites, and recent searches are all keyed by it."""
    wm = context.window_manager
    _reset_draft(wm)
    wm.search_addon_draft_editing_id = entry.get("id", "")
    wm.search_addon_draft_title = entry.get("title", "")
    wm.search_addon_draft_category = entry.get("category", "")
    wm.search_addon_draft_tags = ", ".join(entry.get("tags", []))
    wm.search_addon_draft_manual_url = entry.get("manual_url", "")

    description = entry.get("description", "")
    if description:
        text = bpy.data.texts.new(name="Blender Search Description")
        text.from_string(description)
        wm.search_addon_draft_description_text = text

    for location in entry.get("locations", []):
        item = wm.search_addon_draft_locations.add()
        item.space_type = location.get("space_type", "")
        item.region_type = location.get("region_type", "WINDOW")
        item.ui_path = location.get("ui_path", "")
        point = location.get("point")
        if point:
            item.has_point = True
            item.point_x = point.get("x", 0.5)
            item.point_y = point.get("y", 0.5)
            item.point_workspace = point.get("workspace", "")

    for url in entry.get("images", []):
        item = wm.search_addon_draft_links.add()
        item.kind = "image"
        item.url = url
    for url in entry.get("gifs", []):
        item = wm.search_addon_draft_links.add()
        item.kind = "gif"
        item.url = url
    for video in entry.get("videos", []):
        item = wm.search_addon_draft_links.add()
        item.kind = "video"
        if isinstance(video, str):
            item.url = video
        else:
            item.url = video.get("url", "")
            item.label = video.get("label", "")
            item.thumbnail_url = video.get("thumbnail", "")

    wm.search_addon_compose_active = True
    _redraw_all(wm)


class SEARCHADDON_OT_new_entry(bpy.types.Operator):
    bl_idname = "searchaddon.new_entry"
    bl_label = "New Entry"
    bl_description = "Create a new registry entry of your own"

    def execute(self, context):
        _start_new_entry(context)
        return {'FINISHED'}


class SEARCHADDON_OT_edit_user_entry(bpy.types.Operator):
    bl_idname = "searchaddon.edit_user_entry"
    bl_label = "Edit Entry"
    bl_description = "Load this entry into the New Entry form so you can change it"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        data = storage.load_user_entries()
        entry = next((e for e in data["entries"] if e.get("id") == self.entry_id), None)
        if entry is None:
            self.report({'ERROR'}, "That entry was not found")
            return {'CANCELLED'}

        _load_entry_into_draft(context, entry)
        self.report({'INFO'}, "Loaded into the New Entry form in the Search sidebar panel")
        return {'FINISHED'}


class SEARCHADDON_OT_remove_user_entry(bpy.types.Operator):
    bl_idname = "searchaddon.remove_user_entry"
    bl_label = "Remove Entry"
    bl_description = "Delete this entry of yours. This cannot be undone"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty(options={'HIDDEN'})

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        storage.remove_user_entry(self.entry_id)
        registry.load_all(force=True)
        self.report({'INFO'}, "Removed")
        return {'FINISHED'}


class SEARCHADDON_OT_cancel_new_entry(bpy.types.Operator):
    bl_idname = "searchaddon.cancel_new_entry"
    bl_label = "Cancel"
    bl_description = "Discard this draft and close the New Entry form"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        wm = context.window_manager
        _reset_draft(wm)
        wm.search_addon_compose_active = False
        return {'FINISHED'}


class SEARCHADDON_OT_pick_location(bpy.types.Operator):
    bl_idname = "searchaddon.pick_location"
    bl_label = "Pick a Location"
    bl_description = "Click anywhere in Blender's interface to add that place to this entry"

    def invoke(self, context, event):
        context.window.cursor_modal_set('EYEDROPPER')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            context.window.cursor_modal_restore()
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            area, region = _area_region_at(context, event.mouse_x, event.mouse_y)
            context.window.cursor_modal_restore()
            if area is not None and region is not None:
                item = context.window_manager.search_addon_draft_locations.add()
                item.space_type = area.type
                item.region_type = region.type
                if region.width > 0 and region.height > 0:
                    item.has_point = True
                    item.point_x = min(1.0, max(0.0, (event.mouse_x - region.x) / region.width))
                    item.point_y = min(1.0, max(0.0, (event.mouse_y - region.y) / region.height))
                    item.point_workspace = _current_workspace_name(context)
                _redraw_all(context.window_manager)
            return {'FINISHED'}

        return {'PASS_THROUGH'}


class SEARCHADDON_OT_add_draft_location(bpy.types.Operator):
    bl_idname = "searchaddon.add_draft_location"
    bl_label = "Add Location Manually"
    bl_description = "Add a blank location row to type in yourself"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        item = context.window_manager.search_addon_draft_locations.add()
        item.space_type = "VIEW_3D"
        item.region_type = "WINDOW"
        return {'FINISHED'}


class SEARCHADDON_OT_remove_draft_location(bpy.types.Operator):
    bl_idname = "searchaddon.remove_draft_location"
    bl_label = "Remove Location"
    bl_options = {'INTERNAL'}

    index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        locations = context.window_manager.search_addon_draft_locations
        if 0 <= self.index < len(locations):
            locations.remove(self.index)
        return {'FINISHED'}


class SEARCHADDON_OT_add_draft_link(bpy.types.Operator):
    bl_idname = "searchaddon.add_draft_link"
    bl_label = "Add Link"
    bl_options = {'INTERNAL'}

    kind: StringProperty(options={'HIDDEN'})  # "image", "gif", or "video"

    def execute(self, context):
        item = context.window_manager.search_addon_draft_links.add()
        item.kind = self.kind
        return {'FINISHED'}


class SEARCHADDON_OT_remove_draft_link(bpy.types.Operator):
    bl_idname = "searchaddon.remove_draft_link"
    bl_label = "Remove Link"
    bl_options = {'INTERNAL'}

    index: IntProperty(options={'HIDDEN'})

    def execute(self, context):
        links = context.window_manager.search_addon_draft_links
        if 0 <= self.index < len(links):
            links.remove(self.index)
        return {'FINISHED'}


class SEARCHADDON_OT_save_draft_entry(bpy.types.Operator):
    bl_idname = "searchaddon.save_draft_entry"
    bl_label = "Save Entry"
    bl_description = "Save this as one of your own registry entries"

    def execute(self, context):
        wm = context.window_manager
        title = wm.search_addon_draft_title.strip()
        if not title:
            self.report({'ERROR'}, "Give this entry a title")
            return {'CANCELLED'}

        locations = []
        for location in wm.search_addon_draft_locations:
            if not location.space_type:
                continue
            location_dict = {
                "space_type": location.space_type,
                "region_type": location.region_type or "WINDOW",
                "ui_path": location.ui_path.strip(),
            }
            if location.has_point:
                location_dict["point"] = {
                    "x": location.point_x,
                    "y": location.point_y,
                    "workspace": location.point_workspace,
                }
            locations.append(location_dict)
        if not locations:
            self.report({'ERROR'}, "Add at least one location")
            return {'CANCELLED'}

        category = wm.search_addon_draft_category.strip() or "uncategorized"
        tags = [tag.strip() for tag in wm.search_addon_draft_tags.split(",") if tag.strip()]

        images, gifs, videos = [], [], []
        for link in wm.search_addon_draft_links:
            url = link.url.strip()
            if not url:
                continue
            if link.kind == "image":
                images.append(url)
            elif link.kind == "gif":
                gifs.append(url)
            elif link.kind == "video":
                video = {"url": url}
                if link.label.strip():
                    video["label"] = link.label.strip()
                if link.thumbnail_url.strip():
                    video["thumbnail"] = link.thumbnail_url.strip()
                videos.append(video)

        description_text = wm.search_addon_draft_description_text
        description = description_text.as_string().strip() if description_text is not None else ""

        entry_id = wm.search_addon_draft_editing_id or ("user." + _slugify(category) + "." + _slugify(title))
        entry = {
            "id": entry_id,
            "title": title,
            "category": category,
            "description": description,
            "manual_url": wm.search_addon_draft_manual_url.strip(),
            "images": images,
            "gifs": gifs,
            "videos": videos,
            "tags": tags,
            "locations": locations,
        }

        storage.add_user_entry(entry)
        registry.load_all(force=True)
        _clear_draft_description_text(wm)

        self.report({'INFO'}, "Saved: " + title)
        wm.search_addon_compose_active = False
        return {'FINISHED'}


class SEARCHADDON_OT_export_contributions(bpy.types.Operator, ExportHelper):
    bl_idname = "searchaddon.export_contributions"
    bl_label = "Export Your Contributions"
    bl_description = "Save your new entries and personal links to a file others can import"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    @staticmethod
    def _without_points(entries):
        """Strip each location's precise spot before sharing an entry. A
        pixel position is tied to one person's own workspace arrangement, so
        it is meaningless, and now inert, on anyone else's machine."""
        stripped = []
        for entry in entries:
            entry = dict(entry)
            entry["locations"] = [
                {key: value for key, value in location.items() if key != "point"}
                for location in entry.get("locations", [])
            ]
            stripped.append(entry)
        return stripped

    def execute(self, context):
        data = {
            "schema_version": 1,
            "export_kind": "blender_search_addon_contribution",
            "entries": self._without_points(storage.load_user_entries().get("entries", [])),
            "personal_links": storage.load().get("links", {}),
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
        except OSError as error:
            self.report({'ERROR'}, "Could not save file: " + str(error))
            return {'CANCELLED'}

        self.report(
            {'INFO'},
            f"Exported {len(data['entries'])} entries and links for {len(data['personal_links'])} items",
        )
        return {'FINISHED'}


class SEARCHADDON_OT_import_contributions(bpy.types.Operator, ImportHelper):
    bl_idname = "searchaddon.import_contributions"
    bl_label = "Import Contributions"
    bl_description = "Add entries and personal links someone shared with you"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):
        try:
            with open(self.filepath, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as error:
            self.report({'ERROR'}, "Could not read file: " + str(error))
            return {'CANCELLED'}

        imported_entries = 0
        skipped_entries = 0
        for entry in data.get("entries", []):
            entry_id = entry.get("id")
            if not entry_id:
                continue
            if registry.get(entry_id) is not None and not storage.has_user_entry(entry_id):
                # This id belongs to a bundled entry. Do not silently shadow it.
                skipped_entries += 1
                continue
            storage.add_user_entry(entry)
            imported_entries += 1

        imported_links = 0
        for entry_id, links in data.get("personal_links", {}).items():
            for link in links:
                storage.add_link(entry_id, link.get("label", ""), link.get("url", ""))
                imported_links += 1

        registry.load_all(force=True)

        self.report(
            {'INFO'},
            f"Imported {imported_entries} entries ({skipped_entries} skipped) and {imported_links} links",
        )
        return {'FINISHED'}


class SEARCHADDON_OT_report_issue(bpy.types.Operator):
    bl_idname = "searchaddon.report_issue"
    bl_label = "Report a Problem"
    bl_description = "Open this addon's issue page in your browser"

    def execute(self, context):
        bpy.ops.wm.url_open(url="https://github.com/Gamedirection/Blender-Search-Addon/issues/new/choose")
        return {'FINISHED'}


classes = (
    SEARCHADDON_OT_open_search,
    SEARCHADDON_OT_jump_to_entry,
    SEARCHADDON_OT_watch_highlight,
    SEARCHADDON_OT_eyedropper,
    SEARCHADDON_OT_toggle_favorite,
    SEARCHADDON_OT_play_video,
    SEARCHADDON_OT_add_personal_link,
    SEARCHADDON_OT_remove_personal_link,
    SEARCHADDON_OT_check_pack_size,
    SEARCHADDON_OT_download_pack,
    SEARCHADDON_OT_clear_media_cache,
    SEARCHADDON_OT_new_entry,
    SEARCHADDON_OT_edit_user_entry,
    SEARCHADDON_OT_remove_user_entry,
    SEARCHADDON_OT_cancel_new_entry,
    SEARCHADDON_OT_pick_location,
    SEARCHADDON_OT_add_draft_location,
    SEARCHADDON_OT_remove_draft_location,
    SEARCHADDON_OT_add_draft_link,
    SEARCHADDON_OT_remove_draft_link,
    SEARCHADDON_OT_save_draft_entry,
    SEARCHADDON_OT_export_contributions,
    SEARCHADDON_OT_import_contributions,
    SEARCHADDON_OT_report_issue,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
