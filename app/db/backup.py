"""Back up or restore SQLite, specimen photos, and original analytical files."""

import json
import sqlite3
from argparse import ArgumentParser
from contextlib import closing
from pathlib import Path
from shutil import copyfile, copytree
from tempfile import TemporaryDirectory
from warnings import warn

from app.file_storage import FILES_ROOT, archive_member, sha256_file


MANIFEST = "manifest.json"
MANIFEST_VERSION = 2


def _columns(connection, table):
    return {column[1] for column in connection.execute(f"PRAGMA table_info({table})")}


def _references(connection):
    image_columns = _columns(connection, "image")
    if not image_columns:
        raise ValueError("The database is missing the HERBAR image table.")
    image_digest = "sha256" if "sha256" in image_columns else "NULL"
    for image_id, path, digest in connection.execute(
        f"SELECT image_id, file_path, {image_digest} FROM image ORDER BY image_id"
    ):
        yield f"Image {image_id}", "images", path, digest

    profile_columns = _columns(connection, "chemistry_profile")
    source_columns = {"source_path", "source_sha256"} & profile_columns
    if source_columns and len(source_columns) != 2:
        raise ValueError("The chemistry source schema is incomplete. Finish the migration before backing up.")
    if source_columns:
        for profile_id, path, digest in connection.execute(
            "SELECT id, source_path, source_sha256 FROM chemistry_profile "
            "WHERE source_path IS NOT NULL OR source_sha256 IS NOT NULL ORDER BY id"
        ):
            yield f"Chemistry profile {profile_id}", FILES_ROOT.name, path, digest

    # Original results tables behind spreadsheet imports. Published depositions cite their SHA-256.
    import_columns = _columns(connection, "chemistry_import")
    if import_columns:
        if not {"source_path", "source_sha256"} <= import_columns:
            raise ValueError("The chemistry import schema is incomplete. Finish the migration before backing up.")
        for import_id, path, digest in connection.execute(
            "SELECT id, source_path, source_sha256 FROM chemistry_import ORDER BY id"
        ):
            yield f"Chemistry import {import_id}", FILES_ROOT.name, path, digest


def _verify_files(connection, archive):
    """Hash every referenced file. Returns the hashes and the keys of original import spreadsheets."""
    hashes = {}
    imports = set()
    failures = []
    for label, directory, reference, expected_digest in _references(connection):
        try:
            if directory == FILES_ROOT.name and not expected_digest:
                raise ValueError("Original analytical file has no recorded SHA-256.")
            path = archive_member(archive / directory, reference)
            if not path.is_file():
                raise ValueError(f"Referenced file is missing: {reference}")
            key = path.relative_to(archive).as_posix()
            if key not in hashes:
                hashes[key] = sha256_file(path)
            if expected_digest is not None and hashes[key] != expected_digest:
                raise ValueError(f"SHA-256 mismatch: {key}")
            if label.startswith("Chemistry import "):
                imports.add(key)
        except (OSError, ValueError) as error:
            failures.append(f"{label} — {error}")
    if failures:
        raise ValueError("Archive file verification failed:\n" + "\n".join(failures))
    return hashes, imports


def _reject_links(directory, names):
    for name in names:
        path = Path(directory) / name
        if path.is_symlink() or path.is_junction():
            raise ValueError(f"Archive storage contains a filesystem link: {path}")
    return []


def _copy_archive(database: Path, images: Path, files: Path, destination: Path, expected=None) -> Path:
    database = database.resolve()
    destination = destination.resolve()
    if not database.is_file():
        raise FileNotFoundError(f"Database file not found: {database}")
    if destination.exists():
        raise FileExistsError(f"Choose a new destination directory: {destination}")
    for root in (images, files):
        if root.is_symlink() or root.is_junction():
            raise ValueError(f"Archive storage cannot be a filesystem link: {root}")
        if destination.is_relative_to(root.resolve()):
            raise ValueError(f"Choose a destination outside the source {root.name} directory.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent, prefix=".herbar-backup-") as scratch:
        archive = Path(scratch) / "archive"
        archive.mkdir()
        database_copy = archive / "herbar.db"
        if expected is None:
            with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as source:
                with closing(sqlite3.connect(database_copy)) as target:
                    source.backup(target)
        else:
            # Restore the sealed database itself. Sidecar journals are outside the manifest.
            copyfile(database, database_copy)
            if sha256_file(database_copy) != expected["database_sha256"]:
                raise ValueError("Snapshot database failed SHA-256 verification: herbar.db")

        for source, name in ((images, "images"), (files, FILES_ROOT.name)):
            if source.exists():
                copytree(source, archive / name, ignore=_reject_links)
            else:
                (archive / name).mkdir()
        with closing(sqlite3.connect(database_copy.as_uri() + "?mode=ro&immutable=1", uri=True)) as target:
            if target.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("SQLite could not verify the copied database.")
            broken = target.execute("PRAGMA foreign_key_check").fetchone()
            if broken:
                table, row, parent, _ = broken
                raise ValueError(f"SQLite foreign-key check failed in {table}, row {row}, referencing {parent}.")
            hashes, imports = _verify_files(target, archive)
        if expected is not None:
            expected_files = expected["files"]
            keys = hashes.keys() | expected_files.keys()
            if expected["version"] == 1:
                # Version 1 manifests left out import spreadsheets. They were still checked above against the
                # SHA-256 recorded in the database, whose own digest the manifest seals.
                keys -= imports - expected_files.keys()
            changed = [key for key in sorted(keys) if hashes.get(key) != expected_files.get(key)]
            if changed:
                raise ValueError("Snapshot referenced files differ from the manifest: " + ", ".join(changed))
        manifest = {"version": MANIFEST_VERSION, "database_sha256": sha256_file(database_copy), "files": hashes}
        (archive / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        archive.rename(destination)
    return destination


def backup_archive(database: Path, images: Path, destination: Path, *, files: Path | None = None) -> Path:
    """Create a snapshot directory while the API and other writers are stopped."""
    return _copy_archive(database, images, files if files is not None else images.parent / FILES_ROOT, destination)


def restore_archive(snapshot: Path, destination: Path, *, allow_legacy: bool = False) -> Path:
    """Copy a snapshot to a new directory for verification or deployment."""
    if not (snapshot / "images").is_dir():
        raise FileNotFoundError(f"Snapshot images directory not found: {snapshot / 'images'}")
    manifest_path = snapshot / MANIFEST
    if manifest_path.is_file():
        try:
            expected = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("Cannot read the snapshot manifest.") from error
        if (not isinstance(expected, dict) or expected.get("version") not in (1, MANIFEST_VERSION)
                or not isinstance(expected.get("database_sha256"), str)
                or not isinstance(expected.get("files"), dict)
                or any(not isinstance(value, str) for value in expected["files"].values())):
            raise ValueError("Invalid or unsupported snapshot manifest.")
    elif allow_legacy:
        warn("Legacy snapshot has no manifest. Historical changes to files without upload digests cannot be detected.",
             stacklevel=2)
        expected = None
    else:
        raise ValueError(f"Snapshot has no {MANIFEST}. Use --allow-legacy only for a trusted older snapshot.")
    return _copy_archive(snapshot / "herbar.db", snapshot / "images", snapshot / FILES_ROOT.name,
                         destination, expected)


def main():
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup", help="Take a snapshot while the API is stopped.")
    backup.add_argument("destination", type=Path)
    restore = commands.add_parser("restore", help="Restore a snapshot to a new directory.")
    restore.add_argument("snapshot", type=Path)
    restore.add_argument("destination", type=Path)
    restore.add_argument("--allow-legacy", action="store_true", help="Accept a trusted snapshot without a manifest.")
    args = parser.parse_args()

    try:
        if args.command == "backup":
            from app.db.database import DATABASE_URL
            from app.image.services.image_services import IMAGE_ROOT

            if (DATABASE_URL.get_backend_name() != "sqlite"
                    or DATABASE_URL.database in (None, "", ":memory:")
                    or "uri" in DATABASE_URL.query):
                raise ValueError("Backup requires a file-based SQLite DATABASE_URL.")
            destination = backup_archive(Path(DATABASE_URL.database), IMAGE_ROOT, args.destination, files=FILES_ROOT)
        else:
            destination = restore_archive(args.snapshot, args.destination, allow_legacy=args.allow_legacy)
    except (OSError, sqlite3.Error, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(destination)


if __name__ == "__main__":
    main()
