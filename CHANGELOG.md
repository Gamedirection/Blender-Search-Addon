# Changelog

All notable changes to this project are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
