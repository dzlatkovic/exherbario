"""Version 1 of the portable HERBAR deposition ZIP format."""

import json
import re
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile, ZipInfo


MANIFEST_NAME = "manifest.json"
SNAPSHOT_NAME = "deposition.json"
MAX_SOURCE_BYTES = 512 * 1024
MAX_SNAPSHOT_BYTES = 96 * 1024 * 1024
MAX_MANIFEST_BYTES = 128 * 1024
SCHEMA_VERSION = 2
MAX_PROFILES = 50
MAX_VOUCHERS = 250


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def snapshot_digest(snapshot) -> str:
    return sha256(canonical_json(snapshot)).hexdigest()


def manifest_for(snapshot, encoded: bytes) -> dict:
    schema = snapshot["schema_version"]
    if schema not in (1, 2):
        raise ValueError("Unsupported deposition snapshot version.")
    profiles = snapshot["profiles"]
    if schema == 1:
        if not isinstance(profiles, list) or not 1 <= len(profiles) <= MAX_PROFILES:
            raise ValueError("The snapshot must list between one and 50 profiles.")
    else:
        # Version 2 lists every voucher, so a deposition may describe vouchers without analytical files.
        vouchers = snapshot["vouchers"]
        if not isinstance(profiles, list) or len(profiles) > MAX_PROFILES:
            raise ValueError("The snapshot may list at most 50 profiles.")
        if not isinstance(vouchers, list) or not 1 <= len(vouchers) <= MAX_VOUCHERS:
            raise ValueError("The snapshot must list between one and 250 vouchers.")
        voucher_ids = [voucher["id"] for voucher in vouchers]
        if len(set(voucher_ids)) != len(voucher_ids) or not all(
                isinstance(voucher_id, str) and voucher_id for voucher_id in voucher_ids):
            raise ValueError("Invalid or duplicate voucher ID in the snapshot.")
        if any(profile["voucher"]["id"] not in voucher_ids for profile in profiles):
            raise ValueError("Each profile's voucher must be listed in the snapshot.")
    digest = sha256(encoded).hexdigest()
    entries = [{"path": SNAPSHOT_NAME, "size": len(encoded), "sha256": digest}]
    profile_ids = set()
    for index, profile in enumerate(profiles, 1):
        profile_id = profile["id"]
        if not isinstance(profile_id, str) or not profile_id or profile_id in profile_ids:
            raise ValueError("Invalid or duplicate profile ID in the snapshot.")
        profile_ids.add(profile_id)
        file = profile["file"]
        if (type(file["size"]) is not int or not 1 <= file["size"] <= MAX_SOURCE_BYTES
                or not re.fullmatch(r"[0-9a-f]{64}", file["sha256"])):
            raise ValueError(f"Invalid frozen file metadata for profile {profile_id}.")
        entries.append({"path": f"files/{index:03d}.csv", "profile_id": profile_id,
                        "size": file["size"], "sha256": file["sha256"]})
    return {
        "format": "herbar-deposition",
        "format_version": 1,
        "identity": {key: snapshot[key] for key in ("institution", "accession", "version")},
        "snapshot_sha256": digest,
        "entries": entries,
    }


def build_archive(snapshot, files: dict[str, bytes]) -> bytes:
    encoded = canonical_json(snapshot)
    manifest = manifest_for(snapshot, encoded)
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        # ZIP_STORED and fixed metadata keep the bytes independent of the clock and compressor.
        entries = [(MANIFEST_NAME, canonical_json(manifest)), (SNAPSHOT_NAME, encoded)]
        entries.extend((entry["path"], files[entry["profile_id"]]) for entry in manifest["entries"][1:])
        for name, data in entries:
            member = ZipInfo(name)
            member.create_system = 3
            member.external_attr = 0o100644 << 16
            archive.writestr(member, data)
    return output.getvalue()
