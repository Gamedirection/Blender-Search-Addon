# SPDX-License-Identifier: MIT
import bpy
from bpy.types import WindowManager
from bpy.props import StringProperty, BoolProperty


def register():
    WindowManager.search_addon_query = StringProperty(
        name="Search",
        description="Type part of a name to search Blender's interface",
        default="",
    )
    WindowManager.search_addon_eyedropper_active = BoolProperty(
        name="Eyedropper Active",
        default=False,
    )


def unregister():
    del WindowManager.search_addon_eyedropper_active
    del WindowManager.search_addon_query
