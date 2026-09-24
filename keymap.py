# SPDX-License-Identifier: MIT
import bpy

addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="Window", space_type='EMPTY')
    kmi = km.keymap_items.new("searchaddon.open_search", type='SPACE', value='PRESS', ctrl=True, shift=True)
    addon_keymaps.append((km, kmi))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
