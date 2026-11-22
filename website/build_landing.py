"""Assemble the project homepage and the app's fonts for static hosting."""

from pathlib import Path
from shutil import copytree


if __name__ == "__main__":
    website = Path(__file__).resolve().parent
    root = website.parent
    destination = root / "dist" / "landing"
    copytree(website / "landing", destination, dirs_exist_ok=True)
    copytree(root / "app" / "web" / "assets" / "fonts", destination / "fonts", dirs_exist_ok=True)
    print(destination)
