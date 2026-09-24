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


def draw_settings(layout, context):
    """Let the user rebind this addon's hotkeys from its own preferences panel.

    This mirrors the hotkey editor Blender's own Preferences > Keymap page
    uses (rna_keymap_ui.draw_kmi). Check this against a real Blender install
    when testing, since that module is an internal script, not a stable API.
    """
    layout.label(text="Hotkeys")

    wm = context.window_manager
    kc = wm.keyconfigs.user
    if kc is None or not addon_keymaps:
        layout.label(text="Change hotkeys in Preferences > Keymap.")
        return

    try:
        import rna_keymap_ui
    except ImportError:
        layout.label(text="Change hotkeys in Preferences > Keymap.")
        return

    for km_addon, kmi_addon in addon_keymaps:
        km_user = kc.keymaps.get(km_addon.name)
        if km_user is None:
            continue
        for kmi_user in km_user.keymap_items:
            if kmi_user.idname == kmi_addon.idname:
                layout.context_pointer_set("keymap", km_user)
                rna_keymap_ui.draw_kmi([], kc, km_user, kmi_user, layout, 0)
                break
