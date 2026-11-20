import subprocess
import sys
from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.deposition.archive import build_archive, snapshot_digest
from app.deposition.verify_archive import verify_archive
from app.tests import client


def test_verifier_detects_changed_bytes_and_unexpected_entries(tmp_path):
    source = b"feature,value,confidence\r\nA,100,annotated\r\n"
    snapshot = {
        "schema_version": 1, "institution": "EXU", "accession": "test", "version": 1,
        "profiles": [{"id": "profile", "file": {"size": len(source), "sha256": sha256(source).hexdigest()}}],
    }
    path = tmp_path / "release.zip"
    path.write_bytes(build_archive(snapshot, {"profile": source}))
    digest = snapshot_digest(snapshot)
    assert verify_archive(path, digest)["snapshot_sha256"] == digest
    verified = subprocess.run(
        [sys.executable, "-B", "-S", "-m", "app.deposition.verify_archive", str(path), "--snapshot-sha256", digest],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True, timeout=30,
    )
    assert "Verified EXU test version 1." in verified.stdout
    with pytest.raises(ValueError, match="does not match the supplied digest"):
        verify_archive(path, "f" * 64)

    with ZipFile(path) as archive:
        files = {entry: archive.read(entry) for entry in archive.namelist()}
    with ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, b"A" * len(source) if name.endswith(".csv") else content)
    with pytest.raises(ValueError, match="SHA-256 mismatch: files/001.csv"):
        verify_archive(path)
    with ZipFile(path, "a") as archive:
        archive.writestr("../outside.csv", source)
    with pytest.raises(ValueError, match="Unexpected: ../outside.csv"):
        verify_archive(path)


def test_research_workspace_and_assets_are_served():
    screen = client.get("/researcher")
    assert screen.status_code == 200
    for heading in ("Register a voucher", "Upload a CSV profile", "Validate and preview", "Publish version"):
        assert heading in screen.text
    assert client.get("/assets/herbar/herbar.css").status_code == 200
    assert client.get("/assets/herbar/researcher.js").status_code == 200
