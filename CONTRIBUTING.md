# Contributing

Thank you for helping with this addon.

## Rules for Every Commit

1. Update the `VERSION` file for every commit that changes the addon.
2. Match the version number in `bl_info` inside `__init__.py`.
3. Match the version number in `blender_manifest.toml`.
4. Add a line to `CHANGELOG.md` for every change.

## How to Choose a Version Number

This project uses semantic versioning: MAJOR.MINOR.PATCH.

- Raise PATCH for most commits. Examples: a bug fix, a doc edit, a new
  registry item.
- Raise MINOR for a new feature. Examples: a new panel, a new tool, a new
  registry category.
- Raise MAJOR for a breaking change. Examples: a change to the personal
  links file format, a removed operator, a dropped Blender version.
- When you raise a number, set every number below it back to 0.

Once a change with a new `VERSION` reaches the `main` branch, a GitHub
Actions workflow (`.github/workflows/release.yml`) builds the addon zip
and publishes it as a GitHub Release automatically, tagged `v<VERSION>`,
using that version's section of `CHANGELOG.md` as the release notes. There
is nothing to do by hand for this; it only runs when `VERSION` changes,
and skips a version that already has a release.

## Rules for Commit Messages

1. Do not use an em dash in any commit message.
2. Do not add a "Co-Authored-By" line to any commit in this repository.
3. Write a short summary line. Add more detail below it if needed.

## Rules for Writing

1. Do not use an em dash anywhere in this repository. Use a comma or a
   period instead.
2. Write short sentences. Give one instruction per sentence.
3. Use the same term every time for the same idea. For example, always
   write "addon", never "add-on" or "plugin".

## License

Do not copy code from other addons unless you know its license allows it.
This repository uses the MIT License. The addon template we studied for
structure ideas uses the GPLv3 License. Do not copy its code or its text
into this repository.

## Adding or Fixing a Registry Item

See `docs/registry_schema.md` for the JSON format. Most contributions to
this addon are new or fixed registry items, so this is the easiest way to
help.

## Installing a Local Copy for Testing

Always test with the built zip file, not with a raw copy of this
repository folder. Run this command from the repository root, then install
the zip file from the `dist` folder through Blender's Add-ons preferences.

```
python scripts/build_addon.py
```
