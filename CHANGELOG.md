# Changelog

All notable changes to this project are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.6.0] - 2026-09-24

### Added
- The eyedropper now has two separate cycling keys. Shift+Tab cycles
  through the other items documented in the same area under the cursor
  (what Tab used to do). Tab now cycles through other places in
  Blender where that item's category also shows up, even parts of the
  screen the cursor is not on, and highlights that place too if it is
  already open.

### Investigating
- Pictures and GIFs were reported as still not showing after 0.5.1.
  Added much more detailed logging (prefixed "[Blender Search]") to
  every step of downloading and caching a picture, so the exact
  failure point shows up in the System Console on the next test.
  Please reinstall the updated zip before retesting: Blender does not
  auto-update an installed extension from a locally rebuilt file.

## [0.5.1] - 2026-09-24

### Fixed
- Pictures could get stuck forever on "Loading picture...", with no way
  to tell a slow download apart from one that had actually failed, or
  from Blender's own "Allow Online Access" preference (Preferences >
  System) being off, which blocks this addon from downloading anything.
  The info popup now shows a specific message for each of these cases,
  a real error is printed to the System Console when a download fails,
  and the addon checks `bpy.app.online_access` before trying to fetch
  or check the size of anything.
- A failed download no longer keeps retrying silently forever without
  ever surfacing why.

### Note
- A GIF showing only its first frame is expected, not a bug. Blender's
  popups cannot play GIFs or video. This is called out in the README.

## [0.5.0] - 2026-09-24

### Fixed
- The media cache crashed on every picture, GIF, and video thumbnail,
  because `'CACHE'` is not a valid `bpy.utils.user_resource()` type on
  Blender 4.4. This also took down the whole info popup, not only the
  picture. Media loading is now wrapped so a failure only affects that
  one picture.
- The search popup was not updating live as the user typed, because a
  plain popover's draw function does not reliably redraw on every
  keystroke. The search box is now a proper dialog operator, which does.
- Highlighting Extrude (and a few other items) covered the entire 3D
  Viewport instead of just where the item lives, because their registry
  entries used the `WINDOW` region instead of the header. Fixed for
  Point Light, Extrude, and Twisted Extrude, and documented in
  `docs/registry_schema.md` so future entries pick the right region.
- Pressing Escape while the eyedropper is on now redraws right away, so
  the sidebar button and the cursor update immediately instead of
  looking like the eyedropper is still on.

### Added
- A preference for how many recent searches to remember and show, from
  1 to 50 (default 5), used everywhere recent searches are listed.
- Favorites and Recent are now also directly toggleable in the Search
  sidebar panel in the 3D Viewport, without opening the full search
  popup.

## [0.4.0] - 2026-09-24

### Added
- Pictures, GIFs, and video thumbnails are now fetched from the internet
  and cached on first use, instead of being bundled with the addon. This
  keeps the addon itself small.
- A preference, "Allow Fetching Media From the Internet", to turn this
  off entirely.
- A "Download Offline Media Pack" section in preferences: check the
  estimated download size first, then download everything so it works
  with no internet connection. A "Clear Downloaded Media" button undoes
  this and frees the disk space.
- Hotkeys can now be changed from the addon's own preferences panel,
  instead of only through Blender's separate Keymap editor.

### Changed
- The example registry entries (Point Light, Twisted Extrude, Extrude)
  now reference their pictures by web address instead of a bundled copy.

## [0.3.0] - 2026-09-24

### Added
- Search now matches an item's category and tags, not only its title
  (the registry field `keywords` was renamed to `tags`).
- Category-scoped search using a pipe: `category|term` searches only
  inside one category. `category|` with nothing after the pipe lists
  every entry in that category.
- Three example registry entries showing each media type: Point Light
  (image), Twisted Extrude (GIF), and Extrude (video, linking to an
  external YouTube video with a local thumbnail).
- Video entries can now be an object with `label`, `url`, and
  `thumbnail`, for linking to an external video instead of only a
  bundled local file.
- `manual_url` is now optional, so a community tool or technique
  without an official Blender manual page can still be documented.

## [0.2.0] - 2026-09-24

### Added
- The eyedropper tool now supports Tab. Press Tab while hovering to cycle
  through every registry item that matches the same area, instead of only
  seeing the first one.
- A preference, "Reveal Off-Screen Items Automatically", that switches the
  largest open area to show a found item when its editor is not already
  open, then switches it back afterward. Off by default.
- The search popup now prefills with three groups when the search box is
  empty: Favorite, Recent, and On-Screen (items whose editor is currently
  open).
- A favorite star (pin icon) on every result and info popup, so a user can
  mark an item as a favorite. Favorites persist across sessions.
- GIF support in the info popup (shows the first frame; GIFs do not play
  back inside the popup).
- Video support in the info popup through a Play Video button that opens
  the file in the user's system video player.
- Preferences to turn Images, GIFs, and Videos on or off individually in
  the info popup, in case any of them are slow to load.
- A "Search Blender" entry in Blender's Help menu.

## [0.1.0] - 2026-09-24

### Added
- First version of the addon.
- Search bar for Blender's interface.
- Eyedropper tool for hovering over Blender's interface.
- Extensible JSON registry of documented UI items.
- Personal links storage, saved per item, kept outside the bundled registry.
- Report button linking to this repository's issue page.
- GitHub issue templates for Bug, Problem, Feature Request, Missed Item, Out
  of Date Item, Incorrect Info on Item, and Other.
