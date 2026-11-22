"""Publish the app's font files alongside the static documentation."""

from pathlib import Path

from mkdocs.structure.files import File


def on_files(files, config):
    font_dir = Path(__file__).resolve().parents[1] / "app" / "web" / "assets" / "fonts"
    for font_file in sorted(font_dir.iterdir()):
        if font_file.suffix == ".woff2" or font_file.name in {"fonts.css", "OFL.txt"}:
            files.append(File.generated(config, f"fonts/{font_file.name}", abs_src_path=str(font_file)))
    return files
