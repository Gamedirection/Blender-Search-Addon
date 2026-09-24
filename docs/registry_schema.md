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
| `description` | Yes | text | A short, clear explanation of what the item does. |
| `locations` | Yes | list of objects | Every place this item shows up. See "Locations" below. |
| `manual_url` | No | text | A link to the matching page on `docs.blender.org`, or any other page about this. |
| `images` | No | list of text | Pictures to show in the popup. See "Pictures, GIFs, and Video" below. |
| `gifs` | No | list of text | GIF files to show in the popup. Only the first frame shows. See below. |
| `videos` | No | list | Either a path to a local video file, or an object with `url`, `label`, and `thumbnail` (see below). |
| `tags` | No | list of text | Extra words people might search for. Also used by category search, see below. |
| `rna_hint` | No | object | Optional. Holds `operator` and `property` values, kept for future use by more precise matching. |

## Locations

An entry's `locations` field is a list, since the same item can show up in
more than one place (the eyedropper's Tab key cycles through them, see
"A Note on the Eyedropper Tool" below). Each location is an object:

```json
{
  "space_type": "VIEW_3D",
  "region_type": "HEADER",
  "ui_path": "3D Viewport > Header > Mesh menu > Extrude"
}
```

- `space_type`: the Blender editor, such as `VIEW_3D`, `PROPERTIES`, `NODE_EDITOR`, or `OUTLINER`.
- `region_type`: the part of the editor, such as `WINDOW`, `HEADER`, `TOOL_HEADER`, or `UI`. See "Choosing region_type" below.
- `ui_path`: a short, human path to the item, such as `3D Viewport > Header > Proportional Editing dropdown`.

Older entries written before this addon supported more than one location
still work: a single `space_type`, `region_type`, and `ui_path` directly on
the entry (instead of inside a `locations` list) is read the same as a
`locations` list with one item in it. New entries should use `locations`.

## Pictures, GIFs, and Video

Most registry entries should use a web address (starting with `http://` or
`https://`) for `images`, `gifs`, and video `thumbnail` fields. This is the
normal case. The addon downloads the picture the first time it is needed and
keeps a copy, so it loads instantly after that. Nothing is bundled with the
addon itself, which keeps it small.

A picture can also be a path to a file placed under this addon's own
`resources` folder, if a contributor wants a picture that always works with
no internet connection at all. Use a plain relative path, such as
`images/my_folder/my_picture.png`, instead of a web address.

A user can turn off internet pictures entirely in the addon's preferences.
When that setting is off, only pictures already downloaded, or bundled under
`resources`, will show. The preferences panel also has a "Download Offline
Media Pack" button that checks the download size first, then downloads every
picture, GIF, and video thumbnail used by the registry, so everything works
without the internet from then on.

Keep a GIF small: a large file with many frames (a few megabytes, tens of
frames, over roughly 1000 pixels wide) can fail to generate a thumbnail in
Blender's popup, even though it downloads and is a valid GIF. A short, few
second clip at a modest resolution works reliably. Since Blender's popup can
only ever show the first frame anyway, a short GIF loses nothing that a long
one would have shown.

### Video Entries

A video entry can be a plain text path to a local file under `resources`, which
shows a "Video" button that opens the file in the user's system player. It can
also be an object, for an external video such as one on YouTube:

```json
{
  "label": "Extrude Tool Explained (3Dnot2D)",
  "url": "https://youtu.be/BRCAR-c6DFU",
  "thumbnail": "https://i.ytimg.com/vi/BRCAR-c6DFU/hqdefault.jpg"
}
```

The `thumbnail` is a picture, shown the same way as an image (a web address
downloads and caches, a relative path reads a bundled file). The "Video"
button next to it opens the `url` in the user's browser. Blender's popups
cannot play video or an animated GIF, so an external video always opens
outside Blender. If the thumbnail cannot be shown, the button to open it
directly is always there as a fallback.

## Searching by Category

Typing a category name, then a pipe (`|`), then a search term filters results
to only that category before searching. For example, `modeling|extrude` only
looks inside the "modeling" category for "extrude". Typing `modeling|` with
nothing after the pipe lists every entry in that category.

Searching without a pipe still searches every category at once. The pipe is
only a way to narrow things down, not a requirement.

## Choosing region_type

The addon highlights the whole region named by `region_type`, not just one
button inside it, since Blender does not give addons a reliable way to find
one button's exact position. Pick the smallest region that is actually true:

- Use `HEADER` or `TOOL_HEADER` for anything found through a menu or button
  in a header bar. This is correct far more often than not.
- Use `UI` for something in a sidebar tab (the panel opened with N).
- Only use `WINDOW` for something that is genuinely about the whole working
  area, such as a general modeling or sculpting concept. `WINDOW` in the 3D
  Viewport highlights the entire viewport, which is rarely what you want,
  even for something started with a keyboard shortcut like Extrude's E key.
  Point contributors instead at the menu or header item used to reach it.

## Worked Example

```json
{
  "schema_version": 1,
  "entries": [
    {
      "id": "view3d.proportional_edit_falloff",
      "title": "Proportional Editing Falloff",
      "category": "modeling",
      "locations": [
        {
          "space_type": "VIEW_3D",
          "region_type": "TOOL_HEADER",
          "ui_path": "3D Viewport > Header > Proportional Editing dropdown"
        }
      ],
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

Shift+Tab cycles through the other entries documented in the same area.
Tab cycles through an entry's own other `locations`, and through other
entries sharing its `category` in a different editor.

## Contributing From Inside Blender

Most contributions do not need this file at all. The addon itself can
create one for you:

1. Click "New Entry" in the Search sidebar panel, or turn on the
   eyedropper and Shift+Click the thing you want to document.
2. Fill in the title, category, tags, a plain text description, and a
   manual or source link.
3. Add every place this shows up, either by clicking "Add by Clicking"
   and then clicking the real spot in Blender, or by typing the editor
   and region names in yourself.
4. Add any pictures, GIFs, or videos as web links. See "Pictures, GIFs,
   and Video" above.
5. Click "Save Entry". It is saved on your computer, and searchable
   right away.

Your own entries are stored separately from the ones bundled with the
addon, so an addon update never overwrites them. Use "Export Your
Contributions" in the addon's preferences to save your new entries and
personal links to a file, and send that file to someone else, or open a
pull request with it. They use "Import Contributions" to add them.
