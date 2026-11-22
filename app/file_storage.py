"""File storage shared by scientific uploads and archive verification."""

from contextlib import contextmanager
from hashlib import file_digest
from os import fsync
from pathlib import Path, PurePosixPath, PureWindowsPath


from app.config import settings

DATA_ROOT = Path(settings.DATA_DIR)
FILES_ROOT = DATA_ROOT / "files"


def stored_file_path(name: str) -> str:
    """The path recorded for a new upload: relative to DATA_DIR, so records stay valid if the folder moves."""
    return f"{FILES_ROOT.name}/{name}"


def archive_member(root: Path, stored_path: str | None) -> Path:
    """Resolve a portable archive path without following filesystem links."""
    if root.is_symlink() or root.is_junction():
        raise ValueError("Archive roots cannot be filesystem links.")
    if not isinstance(stored_path, str) or not stored_path or PureWindowsPath(stored_path).drive:
        raise ValueError("Expected a relative archive path.")
    relative = PurePosixPath(stored_path.replace("\\", "/"))
    if relative.is_absolute() or len(relative.parts) < 2 or relative.parts[0] != root.name:
        raise ValueError(f"Expected a path under {root.name}/.")
    path = root
    for part in relative.parts[1:]:
        if part.endswith((".", " ")) or ":" in part or PureWindowsPath(part).is_reserved():
            raise ValueError("Archive path contains an unsafe component.")
        path /= part
        if path.is_symlink() or path.is_junction():
            raise ValueError("Archive entries cannot refer to filesystem links.")
    return path


def sha256_file(path: Path) -> str:
    with path.open("rb") as data:
        return file_digest(data, "sha256").hexdigest()


@contextmanager
def store_upload(path: Path, content: bytes):
    """Remove a newly written file if the database transaction fails."""
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with path.open("xb") as output:
            created = True
            output.write(content)
            output.flush()
            fsync(output.fileno())
        yield
    except Exception:
        if created:
            path.unlink(missing_ok=True)
        raise
