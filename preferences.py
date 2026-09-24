# SPDX-License-Identifier: MIT
import bpy
from bpy.types import AddonPreferences
from bpy.props import FloatVectorProperty


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

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "highlight_color")
        layout.operator("searchaddon.report_issue", icon='URL')


classes = (SearchAddonPreferences,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
