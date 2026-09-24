#!/usr/bin/env python3
"""Build an installable zip file for the Blender Search addon."""

import zipfile
from pathlib import Path

ADDON_MODULE_NAME = "blender_search_addon"

SKIP_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".git",
    ".gitignore",
    ".github",
    ".vscode",
    ".idea",
    "dist",
    "build",
    "scripts",
    "tests",
}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def _should_skip(relative_path: Path) -> bool:
    if relative_path.suffix in SKIP_SUFFIXES:
        return True
    return any(part in SKIP_NAMES for part in relative_path.parts)


def build(repo_root: Path) -> Path:
    version = (repo_root / "VERSION").read_text(encoding="utf-8").strip()
    dist_dir = repo_root / "dist"
    dist_dir.mkdir(exist_ok=True)
    zip_path = dist_dir / f"{ADDON_MODULE_NAME}-{version}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(repo_root.rglob("*")):
            if path.is_dir():
                continue
            relative = path.relative_to(repo_root)
            if _should_skip(relative):
                continue
            arcname = "/".join((ADDON_MODULE_NAME, *relative.parts))
            archive.write(path, arcname)

    return zip_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    result = build(root)
    print(f"Built {result}")
