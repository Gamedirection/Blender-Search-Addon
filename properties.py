# SPDX-License-Identifier: MIT
import bpy
from bpy.types import WindowManager
from bpy.props import BoolProperty


def register():
    WindowManager.search_addon_eyedropper_active = BoolProperty(
        name="Eyedropper Active",
        default=False,
    )
    WindowManager.search_addon_show_favorites = BoolProperty(
        name="Show Favorites",
        description="Show your favorite items in the Search sidebar panel",
        default=False,
    )
    WindowManager.search_addon_show_recent = BoolProperty(
        name="Show Recent",
        description="Show your recent searches in the Search sidebar panel",
        default=False,
    )


def unregister():
    del WindowManager.search_addon_show_recent
    del WindowManager.search_addon_show_favorites
    del WindowManager.search_addon_eyedropper_active
