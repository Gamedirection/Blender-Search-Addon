# SPDX-License-Identifier: MIT
bl_info = {
    "name": "Blender Search",
    "author": "GameDirection",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Search",
    "description": "Search Blender's interface, inspect elements with an eyedropper, and save your own links.",
    "warning": "",
    "doc_url": "https://github.com/Gamedirection/Blender-Search-Addon",
    "tracker_url": "https://github.com/Gamedirection/Blender-Search-Addon/issues/new/choose",
    "category": "Interface",
}


def register():
    from . import registry
    registry.load_all()

    from . import properties
    from . import preferences
    from . import operators
    from . import ui
    from . import overlay
    from . import keymap

    properties.register()
    preferences.register()
    operators.register()
    ui.register()
    overlay.register()
    keymap.register()


def unregister():
    from . import keymap
    from . import overlay
    from . import ui
    from . import operators
    from . import preferences
    from . import properties

    keymap.unregister()
    overlay.unregister()
    ui.unregister()
    operators.unregister()
    preferences.unregister()
    properties.unregister()


if __name__ == "__main__":
    register()
