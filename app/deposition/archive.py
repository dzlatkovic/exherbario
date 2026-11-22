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
# Version 3 lists every voucher linked to each profile's sample, with its role.
# Version 4 adds the technique, run metadata, identification evidence, compounds and compound corrections.
# 5: isolation profiles, co-injection and structure-elucidation evidence, author-supplied structures.
# 6: samples and preparations deposited without analytical runs ("preparations").
SCHEMA_VERSION = 6
MAX_PROFILES = 50
MAX_PREPARATIONS = 50
MAX_VOUCHERS = 250


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def snapshot_digest(snapshot) -> str:
    return sha256(canonical_json(snapshot)).hexdigest()


def manifest_for(snapshot, encoded: bytes) -> dict:
    schema = snapshot["schema_version"]
    if schema not in (1, 2, 3, 4, 5, 6):
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
        if schema == 2 and any(profile["voucher"]["id"] not in voucher_ids for profile in profiles):
            raise ValueError("Each profile's voucher must be listed in the snapshot.")
        if schema >= 3 and not all(
                profile["sample"]["vouchers"] and all(link["id"] in voucher_ids for link in profile["sample"]["vouchers"])
                for profile in profiles):
            raise ValueError("Each voucher linked to a profile's sample must be listed in the snapshot.")
        if schema >= 6:
            preparations = snapshot["preparations"]
            if not isinstance(preparations, list) or len(preparations) > MAX_PREPARATIONS:
                raise ValueError("The snapshot may list at most 50 preparations without runs.")
            preparation_ids = [preparation["id"] for preparation in preparations]
            if len(set(preparation_ids)) != len(preparation_ids) or not all(
                    isinstance(preparation_id, str) and preparation_id for preparation_id in preparation_ids):
                raise ValueError("Invalid or duplicate preparation ID in the snapshot.")
            if not all(preparation["sample"]["vouchers"] and all(
                    link["id"] in voucher_ids for link in preparation["sample"]["vouchers"]) for preparation in preparations):
                raise ValueError("Each voucher linked to a preparation's sample must be listed in the snapshot.")
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
