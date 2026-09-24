# SPDX-License-Identifier: MIT
"""Draws the highlight rectangle over a found registry item."""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import registry
from . import preferences

_SPACE_CLASSES = {
    'VIEW_3D': bpy.types.SpaceView3D,
    'PROPERTIES': bpy.types.SpaceProperties,
    'NODE_EDITOR': bpy.types.SpaceNodeEditor,
    'OUTLINER': bpy.types.SpaceOutliner,
    'IMAGE_EDITOR': bpy.types.SpaceImageEditor,
    'SEQUENCE_EDITOR': bpy.types.SpaceSequenceEditor,
}

_handlers = []
_target = {"region": None, "rect": None, "revert": None}


def set_target(region, rect, revert=None):
    """Show the highlight. `revert`, if given, is (area, previous_type) to restore on clear."""
    _target["region"] = region
    _target["rect"] = rect
    _target["revert"] = revert
    region.tag_redraw()


def get_target_region():
    return _target["region"]


def clear_target():
    region = _target["region"]
    revert = _target["revert"]
    _target["region"] = None
    _target["rect"] = None
    _target["revert"] = None

    if revert is not None:
        area, previous_type = revert
        try:
            area.type = previous_type
        except (ReferenceError, AttributeError):
            pass
    elif region is not None:
        try:
            region.tag_redraw()
        except ReferenceError:
            pass
    return None


def _highlight_color():
    prefs = preferences.get_prefs()
    if prefs is None:
        return (1.0, 0.9, 0.0, 0.6)
    return tuple(prefs.highlight_color)


def _draw():
    region = bpy.context.region
    if region is None or region != _target["region"]:
        return
    rect = _target["rect"]
    if rect is None:
        return

    x0, y0, x1, y1 = rect
    coords = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    indices = ((0, 1, 2), (2, 3, 0))
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords}, indices=indices)

    gpu.state.blend_set('ALPHA')
    shader.bind()
    shader.uniform_float("color", _highlight_color())
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def _used_space_region_pairs():
    pairs = set()
    for entry in registry.all_entries().values():
        for location in entry.get("locations", []):
            space_type = location.get("space_type")
            region_type = location.get("region_type") or "WINDOW"
            if space_type in _SPACE_CLASSES:
                pairs.add((space_type, region_type))
    return pairs


def register():
    _handlers.clear()
    for space_type, region_type in _used_space_region_pairs():
        space_cls = _SPACE_CLASSES[space_type]
        handler = space_cls.draw_handler_add(_draw, (), region_type, 'POST_PIXEL')
        _handlers.append((space_cls, region_type, handler))


def unregister():
    for space_cls, region_type, handler in _handlers:
        space_cls.draw_handler_remove(handler, region_type)
    _handlers.clear()
    clear_target()
