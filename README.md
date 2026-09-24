# Blender Search

Blender Search is an addon for Blender. It helps you find and learn about
parts of Blender's user interface.

## What This Addon Does

- It gives you a search bar. You can search for menus, panels, and
  settings. You can find it in the side panel or in Blender's Help menu.
- It highlights the item you find. The addon uses a yellow color by
  default. You can change this color.
- It gives you an eyedropper tool. Point at a part of Blender. The addon
  shows you information about it. Press Tab to see other matches in the
  same area.
- It lets you mark any item as a favorite with a star, and it remembers
  items you searched for recently.
- It shows a link to the official Blender manual for many items.
- It can show pictures, GIFs, and videos for an item, if the item has
  them. It downloads these from the internet the first time it needs
  them, then keeps a copy. You can turn each of these off in the
  addon's preferences, or turn off internet access for pictures
  entirely.
- It has a "Download Offline Media Pack" button in preferences. It
  checks the download size first, then downloads every picture, GIF,
  and video thumbnail, so they work with no internet connection.
- You can change its hotkeys from its own preferences panel.
- It lets you save your own links for any item. You can save as many links
  as you want.
- It gives you a button to report a problem or a missing item.

## Supported Systems

This addon works on Blender 4.2 and later versions. It works the same way
on Windows, macOS, and Linux.

## How to Install It

1. Go to the Releases page of this repository, or build the addon
   yourself. See "How to Build the Addon" below.
2. Open Blender.
3. Open Edit, then Preferences, then Add-ons.
4. Click Install.
5. Choose the zip file you downloaded or built.
6. Turn on the checkbox next to "Blender Search".

## How to Build the Addon

1. Open a terminal.
2. Go to the root folder of this repository.
3. Run this command:

   ```
   python scripts/build_addon.py
   ```

4. Find your zip file inside the `dist` folder.

## How to Use the Search Bar

1. Open the 3D Viewport.
2. Open the side panel. Press N if it is not open.
3. Click the "Search" tab. You can also open the search bar from
   Blender's Help menu, under "Search Blender".
4. Click the search button.
5. If you leave the box empty, you see three groups: Favorite, Recent,
   and On-Screen (items whose editor is already open). Type part of a
   name to search everything instead. The list updates as you type.
   Search also looks at each item's category and tags, not only its
   title.
   - Type `category|term` to search inside one category only. For
     example, `modeling|extrude` only looks inside the modeling
     category. Type `modeling|` with nothing after the pipe to list
     everything in that category.
6. Click the star next to a result to add or remove it as a favorite.
7. Click a result from the list.
8. The addon highlights the item in yellow, if its editor is open.
9. Hover over the highlighted area. A popup shows a description, any
   pictures, and a link to the Blender manual.

If the item's editor is not open, the addon tells you which editor to
open. It does not move or open a new editor for you, unless you turn on
"Reveal Off-Screen Items Automatically" in the addon's preferences. When
that setting is on, the addon switches your largest open area to show
the item, then switches it back after a few seconds.

The "Search" tab in the side panel also has its own Favorites and
Recent sections. Click either heading to show or hide its list without
opening the full search popup. The addon's preferences let you choose
how many recent searches to remember, up to 50.

## How to Use the Eyedropper Tool

1. Open the side panel. Click the "Search" tab.
2. Click the eyedropper button to turn it on.
3. Move your mouse over any part of Blender's interface.
4. Wait for a moment. A popup appears.
5. The popup names the closest item the addon knows about in that area.
6. If more than one item matches that area, press Tab to see the next
   one. The popup tells you how many matches there are.
7. Click the eyedropper button again to turn it off. You can also press
   Escape or right-click.

The eyedropper cannot always name the exact button under your mouse.
Blender does not give addons that information for every button. When the
addon is not sure, it tells you the closest known item in that area. Use
Tab to check the other items it found in that same area.

## How to Add Your Own Links

1. Open the popup for any item, either from the search bar or the
   eyedropper.
2. Click "Add Your Own Link".
3. Type a label and a URL.
4. Click OK.
5. Your link now shows in the popup for that item. You can add as many
   links as you want.
6. Click the X next to a link to remove it.

Your links stay on your computer. They are not part of the addon's shared
data.

## How to Use Pictures Without the Internet

1. Open Edit, then Preferences, then Add-ons.
2. Find "Blender Search" and open its preferences.
3. Click "Check Download Size" under "Offline Media Pack". Wait for the
   estimate to appear.
4. If the size is fine for you, click "Download Offline Media Pack".
5. Wait for the download to finish. It can take a while and use
   noticeable disk space, depending on how many pictures, GIFs, and
   videos the registry has.
6. Click "Clear Downloaded Media" at any time to delete what was
   downloaded and free the disk space back up.

You can also turn off "Allow Fetching Media From the Internet" if you
never want this addon to access the internet on its own.

## How to Change a Hotkey

1. Open Edit, then Preferences, then Add-ons.
2. Find "Blender Search" and open its preferences.
3. Find "Hotkeys" near the bottom.
4. Click the key shown, then press the new key you want to use.

## How to Add a New Registry Item

The addon uses a set of JSON files to describe Blender's interface. Anyone
can add a new item or fix an old one.

1. Read `docs/registry_schema.md`. It explains every field.
2. Open a JSON file inside the `registry` folder, or create a new one.
3. Add your new entry. Follow the example in the schema document.
4. Save the file.
5. Open a pull request, or send us the file.

Most of our work on this addon is adding items people find missing. Please
use the "Missed Item" report if you are not sure how to edit the file
yourself.

## If a Picture Does Not Show

1. Check that Blender's own "Allow Online Access" setting is turned on, in
   Edit, then Preferences, then System. This addon cannot download
   pictures, GIFs, or video thumbnails while it is off, even if the
   addon's own "Allow Fetching Media From the Internet" is on.
2. If it still does not show, check the "Currently downloaded" line in
   this addon's preferences, and the System Console (Window, then
   Toggle System Console, on Windows; run Blender from a terminal on
   macOS and Linux) for a line starting with "[Blender Search]".
3. You can always click "Open Picture in Browser" under a picture that
   will not show, to see it outside Blender.

A GIF only ever shows its first frame in the popup. Blender's popups
cannot play GIFs or video. Click "Video" under a video entry to watch it
in your system's player or browser instead.

## How to Report a Problem

1. Click the "Report a Problem" button inside the addon, or go to the
   issue page of this repository.
2. Choose the type of report that fits best:
   - Bug
   - Problem
   - Feature Request
   - Missed Item
   - Out of Date Item
   - Incorrect Info on Item
   - Other
3. Fill in the description field. Give as much detail as you can.

## Version

See the `VERSION` file for the current version number. See
`CHANGELOG.md` for a list of changes.

## License

This addon uses the MIT License. See the `LICENSE` file for the full
text.
