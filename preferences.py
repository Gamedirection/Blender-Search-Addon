# SPDX-License-Identifier: MIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatVectorProperty, BoolProperty


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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "highlight_color")
        layout.prop(self, "auto_reveal_offscreen")

        layout.label(text="Media in Popups")
        row = layout.row()
        row.prop(self, "show_images", toggle=True)
        row.prop(self, "show_gifs", toggle=True)
        row.prop(self, "show_videos", toggle=True)

        layout.operator("searchaddon.report_issue", icon='URL')


classes = (SearchAddonPreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
