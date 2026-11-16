"""Back up or restore the SQLite database and specimen photos together."""

import sqlite3
from argparse import ArgumentParser
from contextlib import closing
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory


def _copy_archive(database: Path, images: Path, destination: Path) -> Path:
    database = database.resolve()
    images = images.resolve()
    destination = destination.resolve()
    if not database.is_file():
        raise FileNotFoundError(f"Database file not found: {database}")
    if destination.exists():
        raise FileExistsError(f"Choose a new destination directory: {destination}")
    if destination.is_relative_to(images):
        raise ValueError("Choose a destination outside the source images directory.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent, prefix=".herbar-backup-") as scratch:
        archive = Path(scratch) / "archive"
        archive.mkdir()
        database_copy = archive / "herbar.db"
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(database_copy)) as target:
                source.backup(target)
                if target.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise ValueError("SQLite could not verify the copied database.")

        if images.exists():
            copytree(images, archive / "images", symlinks=True)
        else:
            (archive / "images").mkdir()
        archive.rename(destination)
    return destination


def backup_archive(database: Path, images: Path, destination: Path) -> Path:
    """Create a snapshot directory while the API and other writers are stopped."""
    return _copy_archive(database, images, destination)


def restore_archive(snapshot: Path, destination: Path) -> Path:
    """Copy a snapshot to a new directory for verification or deployment."""
    if not (snapshot / "images").is_dir():
        raise FileNotFoundError(f"Snapshot images directory not found: {snapshot / 'images'}")
    return _copy_archive(snapshot / "herbar.db", snapshot / "images", destination)


def main():
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup", help="Take a snapshot while the API is stopped.")
    backup.add_argument("destination", type=Path)
    restore = commands.add_parser("restore", help="Restore a snapshot to a new directory.")
    restore.add_argument("snapshot", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "backup":
            from app.db.database import DATABASE_URL
            from app.image.services.image_services import IMAGE_ROOT

            if (DATABASE_URL.get_backend_name() != "sqlite"
                    or DATABASE_URL.database in (None, "", ":memory:")
                    or "uri" in DATABASE_URL.query):
                raise ValueError("Backup requires a file-based SQLite DATABASE_URL.")
            destination = backup_archive(Path(DATABASE_URL.database), IMAGE_ROOT, args.destination)
        else:
            destination = restore_archive(args.snapshot, args.destination)
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(destination)


if __name__ == "__main__":
    main()
