# SPDX-License-Identifier: MIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty


def get_prefs(context=None):
    ctx = context or bpy.context
    addon = ctx.preferences.addons.get(__package__)
    return addon.preferences if addon else None


class SearchAddonPreferences(AddonPreferences):
    bl_idname = __package__

    highlight_color: FloatVectorProperty(
        name="Highlight Color",
        description="Color used to highlight a found item",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.9, 0.0, 0.6),
        min=0.0,
        max=1.0,
    )

    auto_reveal_offscreen: BoolProperty(
        name="Reveal Off-Screen Items Automatically",
        description=(
            "When a found item's editor is not open, switch the largest open area to "
            "show it instead of only reporting which editor to open"
        ),
        default=False,
    )

    recent_limit: IntProperty(
        name="Recent Searches to Show",
        description="How many of your most recent searches to list",
        default=5,
        min=1,
        max=50,
    )

    show_images: BoolProperty(
        name="Images",
        description="Show bundled pictures in the info popup",
        default=True,
    )
    show_gifs: BoolProperty(
        name="GIFs",
        description="Show the first frame of bundled GIFs in the info popup",
        default=True,
    )
    show_videos: BoolProperty(
        name="Videos",
        description="Show a Play Video button for bundled videos in the info popup",
        default=True,
    )
    allow_internet_media: BoolProperty(
        name="Allow Fetching Media From the Internet",
        description="Download pictures, GIFs, and video thumbnails as needed. Turn off to only use what is already downloaded",
        default=True,
    )

    def draw(self, context):
        from . import keymap
        from . import media
        from . import storage

        layout = self.layout
        layout.prop(self, "highlight_color")
        layout.prop(self, "auto_reveal_offscreen")
        layout.prop(self, "recent_limit")

        layout.separator()
        layout.label(text="Media in Popups")
        row = layout.row()
        row.prop(self, "show_images", toggle=True)
        row.prop(self, "show_gifs", toggle=True)
        row.prop(self, "show_videos", toggle=True)
        layout.prop(self, "allow_internet_media")

        box = layout.box()
        box.label(text="Offline Media Pack")
        box.label(text="Download every picture, GIF, and video thumbnail so they show without the internet.")
        box.label(text="This can be large. Check the size first.", icon='ERROR')

        if not media.online_access_allowed():
            box.label(text="Blender's own 'Allow Online Access' is off. Turn it on in", icon='ERROR')
            box.label(text="Preferences > System to use this or to show pictures at all.")

        state = media.pack_state
        if state["checking"]:
            box.label(text=f"Checking size... ({state['checked_count']} of {state['total_count']})")
        elif state["downloading"]:
            box.label(text=f"Downloading... ({state['done_count']} of {state['total_count']})")
        elif state["total_count"]:
            size_text = media.format_size(state["estimated_bytes"])
            note = f", {state['unknown_count']} file(s) of unknown size not counted" if state["unknown_count"] else ""
            box.label(text=f"Estimated download: {size_text}{note}", icon='INFO')

        row = box.row()
        row.operator("searchaddon.check_pack_size", icon='FILE_REFRESH')
        row.operator("searchaddon.download_pack", icon='IMPORT')

        box.label(text="Currently downloaded: " + media.format_size(media.cached_size_bytes()))
        box.operator("searchaddon.clear_media_cache", icon='TRASH')

        layout.separator()
        keymap.draw_settings(layout, context)

        box = layout.box()
        box.label(text="Your Contributions")

        user_entries = storage.load_user_entries().get("entries", [])
        if user_entries:
            for entry in user_entries:
                row = box.row(align=True)
                row.label(text=entry.get("title") or entry.get("id", "?"))
                edit_props = row.operator("searchaddon.edit_user_entry", text="Edit")
                edit_props.entry_id = entry["id"]
                remove_props = row.operator("searchaddon.remove_user_entry", text="Remove", icon='TRASH')
                remove_props.entry_id = entry["id"]
        else:
            box.label(text="You have not created any entries yet.", icon='INFO')

        box.label(text="Share the entries and links you have added with other people.")
        row = box.row(align=True)
        row.operator("searchaddon.export_contributions", icon='EXPORT')
        row.operator("searchaddon.import_contributions", icon='IMPORT')

        layout.separator()
        layout.operator("searchaddon.report_issue", icon='URL')


classes = (SearchAddonPreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
