# SPDX-License-Identifier: MIT
import bpy
from bpy.types import PropertyGroup, WindowManager
from bpy.props import BoolProperty, StringProperty, CollectionProperty


class SearchAddonDraftLocation(PropertyGroup):
    space_type: StringProperty(name="Editor")
    region_type: StringProperty(name="Region", default="WINDOW")
    ui_path: StringProperty(name="Path", description="A short, human path to this spot, such as \"3D Viewport > Header > Mesh menu\"")


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
    WindowManager.search_addon_draft_description = StringProperty(
        name="Description",
        description="Plain text, one paragraph. You can write it with Markdown, but this addon only shows it as plain text",
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
    del WindowManager.search_addon_draft_description
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
