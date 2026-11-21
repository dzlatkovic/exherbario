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


def test_research_workspace_requires_sign_in_and_assets_are_served():
    screen = client.get("/researcher", follow_redirects=False)
    assert screen.status_code == 303 and screen.headers["location"] == "/sign-in?next=%2Fresearcher"
    assert "Sign in" in client.get("/sign-in").text
    for asset in ("herbar.css", "js/core.js", "js/mywork.js", "js/study.js", "js/import.js", "js/deposition.js",
                  "js/profile.js", "js/specimen.js", "fonts/fonts.css", "fonts/fira-sans-latin-400-normal.woff2",
                  "fonts/fira-mono-greek-400-normal.woff2", "fonts/OFL.txt"):
        assert client.get(f"/assets/herbar/{asset}").status_code == 200, asset
