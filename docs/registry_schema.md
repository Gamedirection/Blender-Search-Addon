# Registry Schema

This document explains the JSON format used inside the `registry` folder.
Anyone can add a new file, or add a new entry to an existing file.

## File Format

Each file holds one JSON object with two fields.

```json
{
  "schema_version": 1,
  "entries": [ ]
}
```

- `schema_version`: the number 1. Do not change this unless the addon's
  code also changes.
- `entries`: a list of entry objects. See the field list below.

## Entry Fields

| Field | Required | Type | Meaning |
|---|---|---|---|
| `id` | Yes | text | A short, unique name for this entry. Use lowercase letters, numbers, dots, and underscores. Example: `view3d.proportional_edit_falloff`. |
| `title` | Yes | text | The name shown to the user. |
| `category` | Yes | text | A short group name, such as `modeling` or `shading`. |
| `space_type` | Yes | text | The Blender editor this item lives in, such as `VIEW_3D`, `PROPERTIES`, `NODE_EDITOR`, or `OUTLINER`. |
| `region_type` | Yes | text | The part of the editor, such as `WINDOW`, `HEADER`, `TOOL_HEADER`, or `UI`. |
| `ui_path` | Yes | text | A short, human path to the item, such as `3D Viewport > Header > Proportional Editing dropdown`. |
| `description` | Yes | text | A short, clear explanation of what the item does. |
| `manual_url` | Yes | text | A link to the matching page on `docs.blender.org`. |
| `images` | No | list of text | Paths to pictures under the `resources/images` folder. |
| `gifs` | No | list of text | Paths to GIF files under the `resources/images` folder. Only the first frame shows in the popup. |
| `videos` | No | list | Either a path to a local video file, or an object with `url`, `label`, and `thumbnail` (see below). |
| `tags` | No | list of text | Extra words people might search for. Also used by category search, see below. |
| `rna_hint` | No | object | Optional. Holds `operator` and `property` values, kept for future use by more precise matching. |

`manual_url` is optional. Most entries link to a page on `docs.blender.org`, but a
community tool or technique can link anywhere useful instead, or leave the field out.

### Video Entries

A video entry can be a plain text path to a local file under `resources`, which
shows a "Play Video" button that opens the file in the user's system player. It
can also be an object, for an external video such as one on YouTube:

```json
{
  "label": "Extrude Tool Explained (3Dnot2D)",
  "url": "https://youtu.be/BRCAR-c6DFU",
  "thumbnail": "images/video_examples/extrude_tool_explained_thumb.jpg"
}
```

The `thumbnail` is a picture path, shown the same way as an image. The "Video"
button next to it opens the `url` in the user's browser.

## Searching by Category

Typing a category name, then a pipe (`|`), then a search term filters results
to only that category before searching. For example, `modeling|extrude` only
looks inside the "modeling" category for "extrude". Typing `modeling|` with
nothing after the pipe lists every entry in that category.

Searching without a pipe still searches every category at once. The pipe is
only a way to narrow things down, not a requirement.

## Worked Example

```json
{
  "schema_version": 1,
  "entries": [
    {
      "id": "view3d.proportional_edit_falloff",
      "title": "Proportional Editing Falloff",
      "category": "modeling",
      "space_type": "VIEW_3D",
      "region_type": "TOOL_HEADER",
      "ui_path": "3D Viewport > Header > Proportional Editing dropdown",
      "description": "Controls the falloff curve used by proportional editing, so nearby geometry moves more than distant geometry.",
      "manual_url": "https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/proportional_editing.html",
      "images": [],
      "tags": ["proportional", "falloff", "soft selection"]
    }
  ]
}
```

## How to Add a New File

1. Pick a name that matches the editor, such as `sequencer.json`.
2. Start the file with `{"schema_version": 1, "entries": []}`.
3. Add your entries inside the `entries` list.
4. Do not use an em dash inside any text field. Use a comma or a period.

## A Note on the Eyedropper Tool

Blender does not give addons a general way to ask "what button is under
the mouse right now". The eyedropper tool matches the current editor and
region against the closest entry it can find. Precise fields, such as
`ui_path` and `region_type`, make this match better. Adding entries with
accurate fields helps the eyedropper give a closer answer to everyone.
