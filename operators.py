# SPDX-License-Identifier: MIT
"""Operators: search popup, jump to result, eyedropper, favorites, and personal links."""

import time
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty

from . import registry
from . import storage
from . import overlay
from . import preferences
from . import ui


class SEARCHADDON_OT_open_search(bpy.types.Operator):
    bl_idname = "searchaddon.open_search"
    bl_label = "Search Blender"
    bl_description = "Search for a documented Blender feature, panel, or setting"

    def invoke(self, context, event):
        context.window_manager.popover(ui.draw_search_popover, ui_units_x=20)
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

    def _highlight(self, area, region, revert=None):
        overlay.set_target(region, (0, 0, region.width, region.height), revert=revert)
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
                if area.type != entry["space_type"]:
                    continue
                region = self._find_region(area, entry["region_type"])
                if region is None:
                    continue
                self._highlight(area, region)
                self.report({'INFO'}, "Highlighted: " + entry["title"])
                return {'FINISHED'}

        prefs = preferences.get_prefs(context)
        if prefs is not None and prefs.auto_reveal_offscreen:
            window = context.window
            areas = list(window.screen.areas) if window else []
            if areas:
                target_area = max(areas, key=lambda a: a.width * a.height)
                previous_type = target_area.type
                target_area.type = entry["space_type"]
                region = self._find_region(target_area, entry["region_type"])
                if region is not None:
                    self._highlight(target_area, region, revert=(target_area, previous_type))
                    self.report({'INFO'}, "Revealed: " + entry["title"])
                    return {'FINISHED'}
                target_area.type = previous_type

        editor_name = entry["space_type"].replace("_", " ").title()
        self.report({'WARNING'}, "Open the " + editor_name + " editor to see this")
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
    bl_description = "Hover over Blender's interface to learn about the nearest documented item. Press Tab to see other matches in the same area"

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
        self._hover_start = 0.0
        self._shown_for = None
        self._match_index = 0
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
                self._match_index = 0

        if event.type == 'TAB' and event.value == 'PRESS':
            if self._hover_region is not None:
                matches = registry.entries_for_space(self._hover_area.type, self._hover_region.type)
                if matches:
                    self._match_index = (self._match_index + 1) % len(matches)
                    self._shown_for = None
                    self._show_popup(context)
            # Consume Tab so Blender does not also toggle Edit Mode underneath.
            return {'RUNNING_MODAL'}

        if (
            event.type == 'TIMER'
            and self._hover_region is not None
            and self._shown_for is not self._hover_region
            and time.monotonic() - self._hover_start >= 0.6
        ):
            self._show_popup(context)

        return {'PASS_THROUGH'}

    def _show_popup(self, context):
        area = self._hover_area
        region = self._hover_region
        self._shown_for = region
        if area is None or region is None:
            return

        matches = registry.entries_for_space(area.type, region.type)
        if not matches:
            return

        index = self._match_index % len(matches)
        entry = matches[index]
        exact = region.type == entry.get("region_type")
        more_available = len(matches) > 1

        def draw(popup_self, popup_context, entry=entry, exact=exact,
                 more=more_available, shown_index=index, total=len(matches)):
            ui.draw_entry_info(popup_self.layout, entry, exact=exact)
            if more:
                popup_self.layout.label(
                    text=f"Press Tab for more matches here ({shown_index + 1} of {total})",
                    icon='TRIA_RIGHT',
                )

        context.window_manager.popover(draw, ui_units_x=16)

    def _finish(self, context):
        context.window_manager.search_addon_eyedropper_active = False
        try:
            context.window.cursor_modal_restore()
        except Exception:
            pass
        if getattr(self, "_timer", None) is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
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
    SEARCHADDON_OT_report_issue,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
