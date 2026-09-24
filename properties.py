# SPDX-License-Identifier: MIT
import bpy
from bpy.types import PropertyGroup, WindowManager
from bpy.props import BoolProperty, StringProperty, FloatProperty, CollectionProperty, PointerProperty


class SearchAddonDraftLocation(PropertyGroup):
    space_type: StringProperty(name="Editor")
    region_type: StringProperty(name="Region", default="WINDOW")
    ui_path: StringProperty(name="Path", description="A short, human path to this spot, such as \"3D Viewport > Header > Mesh menu\"")
    has_point: BoolProperty(
        name="Has a Precise Spot",
        description="Whether this location remembers exactly where in the region you clicked",
        default=False,
    )
    point_x: FloatProperty(default=0.5, min=0.0, max=1.0)
    point_y: FloatProperty(default=0.5, min=0.0, max=1.0)
    point_workspace: StringProperty(
        name="Captured In",
        description="The workspace tab this precise spot was clicked in. Only used to highlight there again",
        default="",
    )


class SearchAddonDraftLink(PropertyGroup):
    kind: StringProperty()  # "image", "gif", or "video"
    url: StringProperty(name="URL")
    label: StringProperty(name="Label")
    thumbnail_url: StringProperty(name="Thumbnail URL")


classes = (
    SearchAddonDraftLocation,
    SearchAddonDraftLink,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

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

    WindowManager.search_addon_compose_active = BoolProperty(
        name="New Entry Open",
        default=False,
    )
    WindowManager.search_addon_draft_editing_id = StringProperty(
        name="Editing",
        description="The id of your entry being edited. Empty means this draft will create a new one",
        default="",
    )
    WindowManager.search_addon_draft_title = StringProperty(name="Title")
    WindowManager.search_addon_draft_category = StringProperty(
        name="Category",
        description="A short group name, such as modeling or lighting. Reuse an existing one where it fits",
    )
    WindowManager.search_addon_draft_tags = StringProperty(
        name="Tags",
        description="Extra words people might search for, separated by commas",
    )
    WindowManager.search_addon_draft_description_text = PointerProperty(
        type=bpy.types.Text,
        name="Description",
        description=(
            "A real multi-line text block for this entry's description. "
            "Markdown is allowed; this addon shows it as plain text, since it "
            "cannot render Markdown, but an exported file keeps it as written"
        ),
    )
    WindowManager.search_addon_draft_manual_url = StringProperty(
        name="Manual or Source Link",
        description="A link to the Blender manual, or any other page about this",
    )
    WindowManager.search_addon_draft_locations = CollectionProperty(type=SearchAddonDraftLocation)
    WindowManager.search_addon_draft_links = CollectionProperty(type=SearchAddonDraftLink)


def unregister():
    del WindowManager.search_addon_draft_links
    del WindowManager.search_addon_draft_locations
    del WindowManager.search_addon_draft_manual_url
    del WindowManager.search_addon_draft_description_text
    del WindowManager.search_addon_draft_tags
    del WindowManager.search_addon_draft_category
    del WindowManager.search_addon_draft_title
    del WindowManager.search_addon_draft_editing_id
    del WindowManager.search_addon_compose_active
    del WindowManager.search_addon_show_recent
    del WindowManager.search_addon_show_favorites
    del WindowManager.search_addon_eyedropper_active

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
