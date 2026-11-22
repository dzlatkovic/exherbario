"""Mirror one published HERBAR version to Zenodo and record the dataset DOI it receives.

The ZIP sent to Zenodo is the same byte-identical archive served by HERBAR, so anyone can check
the Zenodo copy with ``python -m app.deposition.verify_archive``. Rehearse against
https://sandbox.zenodo.org by setting ZENODO_URL before mirroring real records.

    python -m app.deposition.mirror_zenodo EXU <accession> 1 --curator curator@example.org
"""

import argparse
import re

import requests
from fastapi import HTTPException

from app.config import settings
from app.db import SessionLocal
from app.users.models import User

from .models import Deposition, DepositionDOI, DepositionVersion
from .schemas import DatasetDOI
from .services import DepositionService

# Zenodo license identifiers for the licenses researchers most often enter.
LICENSES = {
    "ccby4.0": "cc-by-4.0", "ccbysa4.0": "cc-by-sa-4.0", "ccbync4.0": "cc-by-nc-4.0",
    "ccbynd4.0": "cc-by-nd-4.0", "ccbyncsa4.0": "cc-by-nc-sa-4.0", "ccbyncnd4.0": "cc-by-nc-nd-4.0",
    "cc01.0": "cc0-1.0", "cc0": "cc0-1.0", "odcby1.0": "odc-by-1.0", "odbl1.0": "odbl-1.0",
    "pddl1.0": "pddl-1.0",
}


def zenodo_license(value):
    key = re.sub(r"[\s_\-]|license|international|public|domain|dedication", "", value.lower())
    for words, short in (("creativecommons", "cc"), ("attribution", "by"), ("noncommercial", "nc"),
                         ("sharealike", "sa"), ("noderivatives", "nd")):
        key = key.replace(words, short)
    if key not in LICENSES:
        raise ValueError(f"Map the license {value!r} to a Zenodo license ID with --license, e.g. cc-by-4.0.")
    return LICENSES[key]


def zenodo_metadata(snapshot, published_at, digest, article_dois, license_id=None):
    creators = []
    for contributor in snapshot["contributors"]:
        creator = {"name": contributor["name"]}
        if contributor.get("orcid"):
            creator["orcid"] = contributor["orcid"]
        creators.append(creator)
    related = [{"identifier": snapshot["identifier"], "relation": "isIdenticalTo", "scheme": "url"}]
    related += [{"identifier": doi, "relation": "isSupplementTo", "scheme": "doi"} for doi in article_dois]
    notes = (f"Mirrored from {snapshot['identifier']} ({snapshot['institution']} {snapshot['accession']}, "
             f"version {snapshot['version']}). Snapshot SHA-256 {digest}.")
    return {
        "upload_type": "dataset", "title": snapshot["title"], "creators": creators,
        "description": snapshot.get("description") or snapshot["title"],
        "publication_date": published_at.date().isoformat(), "version": str(snapshot["version"]),
        "access_right": "open", "license": license_id or zenodo_license(snapshot["license"]),
        "related_identifiers": related, "notes": notes,
    }


class ZenodoClient:
    def __init__(self, base_url, token, session=None):
        self.base = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.headers = {"Authorization": f"Bearer {token}"}

    def _check(self, response):
        if response.status_code >= 400:
            raise RuntimeError(f"Zenodo returned HTTP {response.status_code}: {response.text[:500]}")
        return response.json() if response.content else {}

    def publish(self, filename, content, metadata):
        draft = self._check(self.session.post(f"{self.base}/api/deposit/depositions", json={},
                                              headers=self.headers, timeout=60))
        try:
            self._check(self.session.put(f"{draft['links']['bucket']}/{filename}", data=content,
                                         headers=self.headers, timeout=300))
            self._check(self.session.put(f"{self.base}/api/deposit/depositions/{draft['id']}",
                                         json={"metadata": metadata}, headers=self.headers, timeout=60))
            record = self._check(self.session.post(
                f"{self.base}/api/deposit/depositions/{draft['id']}/actions/publish", headers=self.headers, timeout=120))
        except Exception as error:
            raise RuntimeError(f"{error} The unpublished Zenodo draft {draft['id']} can be reviewed or deleted "
                               "in the Zenodo upload list.") from error
        return record["doi"], record.get("links", {}).get("html")


def mirror(institution, accession, number, curator_email, *, license_id=None, dry_run=False, session=None):
    with SessionLocal() as db:
        curator = db.query(User).filter_by(email=curator_email).first()
        if curator is None or not curator.is_active or not curator.is_superuser:
            raise ValueError("Name an active curator account with --curator.")
        service = DepositionService(db)
        try:
            content, digest, filename = service.public_archive(institution, accession, number)
            articles = service.public_version(institution, accession, number)[1]["article_dois"]
        except HTTPException as error:
            raise ValueError(error.detail) from error
        deposition = db.query(Deposition).filter_by(institution=institution.upper(), accession=accession).one()
        version = db.get(DepositionVersion, (deposition.id, number))
        if version.snapshot["schema_version"] < 2:
            raise ValueError("Only versions published with absolute identifiers can be mirrored. Publish a new version.")
        existing = db.get(DepositionDOI, (deposition.id, number))
        if existing is not None:
            raise ValueError(f"Version {number} already has the dataset DOI {existing.doi}.")
        metadata = zenodo_metadata(version.snapshot, version.published_at, digest, articles, license_id)
        if dry_run:
            return {"metadata": metadata, "filename": filename, "bytes": len(content)}
        if not settings.ZENODO_TOKEN:
            raise ValueError("Set ZENODO_TOKEN to a Zenodo token with deposit:write and deposit:actions scopes.")
        doi, record_url = ZenodoClient(settings.ZENODO_URL, settings.ZENODO_TOKEN, session).publish(
            filename, content, metadata)
        registered = service.register_doi(deposition.id, number, DatasetDOI(
            doi=doi, agency="zenodo", record_url=record_url), curator)
        return registered


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("institution")
    parser.add_argument("accession")
    parser.add_argument("version", type=int)
    parser.add_argument("--curator", required=True, help="Email of the curator recording the DOI.")
    parser.add_argument("--license", help="Zenodo license ID when the deposition license is not recognised.")
    parser.add_argument("--dry-run", action="store_true", help="Show the Zenodo metadata without uploading.")
    args = parser.parse_args()
    if settings.DEMO_MODE:
        raise SystemExit("A demonstration instance does not mirror its synthetic depositions to Zenodo.")
    try:
        result = mirror(args.institution, args.accession, args.version, args.curator,
                        license_id=args.license, dry_run=args.dry_run)
    except (ValueError, RuntimeError, requests.RequestException) as error:
        parser.exit(1, f"Mirroring failed: {error}\n")
    if args.dry_run:
        print(f"Would upload {result['filename']} ({result['bytes']} bytes) with metadata:")
        print(result["metadata"])
    else:
        print(f"Registered {result['doi']} ({result['record_url'] or result['url']}).")


if __name__ == "__main__":
    main()
