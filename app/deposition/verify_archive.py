"""Verify a HERBAR ZIP offline without extracting files or connecting to HERBAR."""

import argparse
import json
from hashlib import file_digest
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from .archive import (
    MANIFEST_NAME, MAX_MANIFEST_BYTES, MAX_SNAPSHOT_BYTES, SNAPSHOT_NAME, canonical_json, manifest_for,
)


def verify_archive(path: Path, expected_digest: str | None = None) -> dict:
    with ZipFile(path) as archive:
        members = archive.infolist()
        names = {member.filename for member in members}
        if len(names) != len(members):
            raise ValueError("The ZIP contains duplicate entry names.")
        if not {MANIFEST_NAME, SNAPSHOT_NAME}.issubset(names):
            raise ValueError("The ZIP is missing the manifest or deposition metadata.")
        if any(member.flag_bits & 1 for member in members):
            raise ValueError("Encrypted entries are unsupported.")
        if (archive.getinfo(MANIFEST_NAME).file_size > MAX_MANIFEST_BYTES
                or archive.getinfo(SNAPSHOT_NAME).file_size > MAX_SNAPSHOT_BYTES):
            raise ValueError("The archive metadata exceeds the format size limit.")
        manifest = json.loads(archive.read(MANIFEST_NAME))
        encoded = archive.read(SNAPSHOT_NAME)
        snapshot = json.loads(encoded)
        if canonical_json(snapshot) != encoded:
            raise ValueError("The deposition metadata is not in canonical form.")
        expected = manifest_for(snapshot, encoded)
        if manifest != expected:
            raise ValueError("The manifest does not match the frozen deposition metadata.")
        if expected_digest is not None and expected_digest.lower() != expected["snapshot_sha256"]:
            raise ValueError("The snapshot SHA-256 does not match the supplied digest.")
        expected_names = {MANIFEST_NAME, *(entry["path"] for entry in expected["entries"])}
        if names != expected_names:
            raise ValueError("ZIP entries differ from the manifest. Missing: "
                             + ", ".join(sorted(expected_names - names)) + ". Unexpected: "
                             + ", ".join(sorted(names - expected_names)) + ".")
        for entry in expected["entries"][1:]:
            name = entry["path"]
            if archive.getinfo(name).file_size != entry["size"]:
                raise ValueError(f"Size mismatch: {name}")
            with archive.open(name) as stream:
                if file_digest(stream, "sha256").hexdigest() != entry["sha256"]:
                    raise ValueError(f"SHA-256 mismatch: {name}")
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--snapshot-sha256", help="Digest from the public deposition page.")
    args = parser.parse_args()
    try:
        manifest = verify_archive(args.archive, args.snapshot_sha256)
    except (BadZipFile, KeyError, NotImplementedError, OSError, RuntimeError, TypeError, ValueError) as error:
        parser.exit(1, f"Verification failed: {error}\n")
    identity = manifest["identity"]
    print(f"Verified {identity['institution']} {identity['accession']} version {identity['version']}.")
    print(f"Snapshot SHA-256: {manifest['snapshot_sha256']}")


if __name__ == "__main__":
    main()
