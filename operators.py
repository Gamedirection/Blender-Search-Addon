# SPDX-License-Identifier: MIT
"""Operators: search popup, jump to result, eyedropper, and personal links."""

import time

import bpy
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty

from . import registry
from . import storage
from . import overlay
from . import ui

_ENUM_CACHE = []


def _search_items(self, context):
    # Kept in a module-level list on purpose: Blender frees a dynamic enum's
    # items if nothing else holds a reference to them.
    global _ENUM_CACHE
    entries = sorted(registry.all_entries().values(), key=lambda entry: entry["title"])
    _ENUM_CACHE = [
        (entry["id"], entry["title"], (entry.get("description") or "")[:200])
        for entry in entries
    ]
    return _ENUM_CACHE


class SEARCHADDON_OT_open_search(bpy.types.Operator):
    bl_idname = "searchaddon.open_search"
    bl_label = "Search Blender"
    bl_description = "Search for a documented Blender feature, panel, or setting"
    bl_property = "entry_id"

    entry_id: EnumProperty(name="Result", items=_search_items)

    def execute(self, context):
        bpy.ops.searchaddon.jump_to_entry('INVOKE_DEFAULT', entry_id=self.entry_id)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}


class SEARCHADDON_OT_jump_to_entry(bpy.types.Operator):
    bl_idname = "searchaddon.jump_to_entry"
    bl_label = "Show Result"
    bl_description = "Highlight this item if its editor is open"
    bl_options = {'INTERNAL'}

    entry_id: StringProperty()

    def execute(self, context):
        entry = registry.get(self.entry_id)
        if entry is None:
            self.report({'ERROR'}, "That item is no longer in the registry")
            return {'CANCELLED'}

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != entry["space_type"]:
                    continue
                region = next((r for r in area.regions if r.type == entry["region_type"]), None)
                if region is None:
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region is None:
                    continue

                overlay.set_target(region, (0, 0, region.width, region.height))
                area.tag_redraw()
                bpy.app.timers.register(overlay.clear_target, first_interval=4.0)
                bpy.ops.searchaddon.watch_highlight('INVOKE_DEFAULT', entry_id=entry["id"], duration=4.0)
                self.report({'INFO'}, "Highlighted: " + entry["title"])
                return {'FINISHED'}

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
    bl_description = "Hover over Blender's interface to learn about the nearest documented item"

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

        entry = matches[0]
        exact = len(matches) == 1 and region.type == entry.get("region_type")

        def draw(popup_self, popup_context, entry=entry, exact=exact):
            ui.draw_entry_info(popup_self.layout, entry, exact=exact)

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
