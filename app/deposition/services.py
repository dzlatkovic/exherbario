"""Authorize draft edits and commit immutable public versions."""

from datetime import datetime, timezone
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, undefer

from app.chemistry.models import Preparation, Profile
from app.config import settings
from app.db import lock_for_update, new_id
from app.external.lookups import parse_retrieved_at, record_import
from app.specimen.models import Specimen

from .archive import build_archive, snapshot_digest
from . import registries
from .datacite import datacite_metadata
from app.users.models import User

from .models import (
    Deposition, DepositionArticle, DepositionDOI, DepositionFile, DepositionVersion, DepositionWithdrawal, Institution,
)
from .snapshot import (build_snapshot, landing_path, registered_institution, release_digest, release_summary, selected_preparations, selected_records, selected_vouchers,
                       version_url)


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DepositionService:
    def __init__(self, db: Session):
        self.db = db

    def _deposition(self, deposition_id, actor, *, for_update=False):
        query = self.db.query(Deposition).filter_by(id=deposition_id)
        deposition = (lock_for_update(self.db, query) if for_update else query).first()
        if deposition is None or (deposition.owner_id != actor.user_id and not actor.is_superuser):
            raise HTTPException(404, "Deposition not found.")
        return deposition

    @staticmethod
    def _draft_summary(deposition):
        return {
            "id": deposition.id, "institution": deposition.institution, "accession": deposition.accession,
            "latest_version": deposition.latest_version or None,
            "draft_revision": deposition.draft_revision, "draft": deposition.draft,
            "submitted_at": deposition.submitted_at.isoformat() + "Z" if deposition.submitted_at else None,
        }

    def list_for_owner(self, actor):
        """The actor's depositions, most recently published first; drafts without a version come first."""
        depositions = self.db.scalars(select(Deposition).where(Deposition.owner_id == actor.user_id)).all()
        numbers = {item.id: item.latest_version for item in depositions if item.latest_version}
        latest = {version.deposition_id: version for version in self.db.scalars(
            select(DepositionVersion).where(DepositionVersion.deposition_id.in_(list(numbers))))
            if version.number == numbers[version.deposition_id]} if numbers else {}
        rows = []
        for item in depositions:
            version = latest.get(item.id)
            title = ((item.draft or {}).get("title") if item.draft else None) or (version.snapshot.get("title") if version else None)
            rows.append({
                "id": item.id, "institution": item.institution, "accession": item.accession,
                "title": title or "Untitled deposition", "latest_version": item.latest_version or None,
                "has_draft": bool(item.draft_revision), "published_at": version.published_at if version else None,
                "in_review": item.submitted_at is not None,
            })
        return sorted(rows, key=lambda row: (row["latest_version"] is not None, -(row["published_at"].timestamp())
                                             if row["published_at"] else 0, row["title"].casefold()))

    def list_public(self, *, q="", page=1, size=20):
        """Published depositions at their latest version, newest first. Drafts never appear here."""
        title = DepositionVersion.snapshot["title"].as_string()
        statement = (
            select(Deposition, DepositionVersion, title, Institution.name, DepositionDOI.doi, DepositionWithdrawal.reason)
            .join(DepositionVersion, (DepositionVersion.deposition_id == Deposition.id)
                  & (DepositionVersion.number == Deposition.latest_version))
            .join(Institution, Institution.code == Deposition.institution)
            .outerjoin(DepositionDOI, (DepositionDOI.deposition_id == Deposition.id)
                       & (DepositionDOI.version == DepositionVersion.number))
            .outerjoin(DepositionWithdrawal, (DepositionWithdrawal.deposition_id == Deposition.id)
                       & (DepositionWithdrawal.version == DepositionVersion.number))
        )
        if q.strip():
            term = q.strip()
            statement = statement.where(or_(title.icontains(term, autoescape=True),
                                            Deposition.accession.icontains(term, autoescape=True),
                                            Institution.name.icontains(term, autoescape=True),
                                            DepositionDOI.doi.icontains(term, autoescape=True)))
        total = self.db.scalar(select(func.count()).select_from(statement.subquery()))
        rows = self.db.execute(statement.order_by(DepositionVersion.published_at.desc(), Deposition.id)
                               .offset((page - 1) * size).limit(size)).all()
        return {"total": total, "page": page, "size": size, "items": [{
            "title": title_text, "institution": deposition.institution, "institution_name": institution_name,
            "accession": deposition.accession, "version": version.number,
            "published_at": version.published_at.isoformat() + "Z",
            "path": f"/depositions/{deposition.institution}/{deposition.accession}/versions/{version.number}",
            "dataset_doi": doi, "status": "withdrawn" if withdrawn else "published",
        } for deposition, version, title_text, institution_name, doi, withdrawn in rows]}

    def submit(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        if deposition.draft is None:
            raise HTTPException(409, "Save a draft before submitting it for review.")
        if deposition.submitted_at is None:
            deposition.submitted_at = utc_now()
            self.db.commit()
        return self._draft_summary(deposition)

    def withdraw_submission(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        deposition.submitted_at = None
        self.db.commit()
        return self._draft_summary(deposition)

    def list_review(self):
        """Drafts submitted for review, oldest first, for curators."""
        rows = self.db.execute(
            select(Deposition, User).join(User, User.user_id == Deposition.owner_id)
            .where(Deposition.submitted_at.is_not(None), Deposition.draft.is_not(None))
            .order_by(Deposition.submitted_at, Deposition.id)
        ).all()
        return [{
            "id": deposition.id, "institution": deposition.institution, "accession": deposition.accession,
            "title": (deposition.draft or {}).get("title") or "Untitled deposition",
            "owner": f"{owner.name} {owner.surname}".strip(), "owner_email": owner.email,
            "submitted_at": deposition.submitted_at.isoformat() + "Z",
            "latest_version": deposition.latest_version or None,
            "correction_reason": (deposition.draft or {}).get("correction_reason"),
        } for deposition, owner in rows]

    def list_institutions(self):
        return [self._institution(row) for row in self.db.scalars(select(Institution).order_by(Institution.code))]

    @staticmethod
    def _institution(row):
        return {
            "code": row.code, "name": row.name, "index_herbariorum_code": row.index_herbariorum_code,
            "ror": f"https://ror.org/{row.ror_id}" if row.ror_id else None,
        }

    def lookup_institutions(self, query):
        return registries.lookup(self.db, query)

    def register_institution(self, data, actor):
        for source in data.sources:
            if source.provider == "ror":
                matches = data.ror_id is not None and registries.ror_id(source.external_id) == data.ror_id.lower()
            else:
                matches = source.external_id.upper() == data.index_herbariorum_code
            if not matches:
                raise HTTPException(422, f"The {source.provider.replace('_', ' ')} source does not match the "
                                         "identifier being registered.")
        existing = self.db.get(Institution, data.code)
        if existing is not None:
            unchanged = (existing.name, existing.index_herbariorum_code, existing.ror_id) == (
                data.name, data.index_herbariorum_code, data.ror_id)
            if not unchanged:
                raise HTTPException(409, f"Institution code {data.code} is already registered.")
            return self._institution(existing)
        for column, value in (("index_herbariorum_code", data.index_herbariorum_code), ("ror_id", data.ror_id)):
            if value and self.db.scalar(select(Institution.code).where(getattr(Institution, column) == value)):
                raise HTTPException(409, f"Another institution code already uses {value}.")
        institution = Institution(**data.model_dump(exclude={"sources"}), registered_by=actor.user_id,
                                  registered_at=utc_now())
        self.db.add(institution)
        for source in data.sources:
            identifier = data.ror_id if source.provider == "ror" else data.index_herbariorum_code
            record_import(self.db, provider=source.provider, external_id=identifier, record_type="institution",
                          record_id=data.code, fields={"name": data.name, "identifier": identifier},
                          confirmed_by=actor.user_id, retrieved_at=parse_retrieved_at(source.retrieved_at))
        self.db.commit()
        return self._institution(institution)

    def create(self, data, actor):
        if data.correction_reason is not None:
            raise HTTPException(409, "A correction requires a published version.")
        lock_for_update(self.db, self.db.query(Institution).filter_by(code=data.institution)).first()
        registered_institution(self.db, data.institution)
        self._check_draft_references(data)
        deposition = Deposition(institution=data.institution, owner_id=actor.user_id,
                                draft=data.model_dump(exclude={"institution"}), draft_revision=new_id())
        self.db.add(deposition)
        self.db.commit()
        return self._draft_summary(deposition)

    def get_draft(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor)
        summary = self._draft_summary(deposition)
        if deposition.latest_version:
            version = self.db.get(DepositionVersion, (deposition.id, deposition.latest_version))
            summary["published"] = {"version": version.number, "page": landing_path(deposition, version.number),
                                    "correction_start": correction_start(version.snapshot)}
        return summary

    def draft_inputs(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor)
        profile_ids = deposition.draft.get("profile_ids", []) if deposition.draft else []
        specimen_ids = deposition.draft.get("specimen_ids", []) if deposition.draft else []
        records = selected_records(self.db, deposition, profile_ids)
        vouchers = selected_vouchers(self.db, specimen_ids)
        preparation_ids = deposition.draft.get("preparation_ids", []) if deposition.draft else []
        preparations = selected_preparations(self.db, deposition, preparation_ids)
        return {
            "vouchers": [
                {
                    "id": voucher.specimen_id, "name": voucher.subnomen or (taxon.taxon_name if taxon else None),
                    "accession": voucher.accession or voucher.reg_no, "is_public": voucher.is_public,
                    "public_location": voucher.public_location,
                }
                for voucher, taxon in (vouchers[specimen_id] for specimen_id in specimen_ids if specimen_id in vouchers)
            ],
            "inputs": [
                {
                    "profile": {"id": profile.id, "name": profile.source_name, "is_public": profile.is_public},
                    "study": {"id": study.id, "title": study.title, "is_public": study.is_public},
                    # Every voucher linked to the profile's sample; all must be released before publication.
                    "vouchers": [{
                        "id": voucher.specimen_id, "role": link.role,
                        "name": voucher.subnomen or taxon_name, "accession": voucher.accession or voucher.reg_no,
                        "is_public": bool(voucher.is_public), "public_location": voucher.public_location,
                    } for link, voucher, taxon_name in links],
                }
                for profile, _, _, study, links in records.values()
            ],
            "preparations": [
                {
                    "preparation": {"id": preparation.id, "batch_code": preparation.batch_code,
                                    "kind": preparation.kind, "sample_code": sample.code},
                    "study": {"id": study.id, "title": study.title, "is_public": study.is_public},
                    "vouchers": [{
                        "id": voucher.specimen_id, "role": link.role,
                        "name": voucher.subnomen or taxon_name, "accession": voucher.accession or voucher.reg_no,
                        "is_public": bool(voucher.is_public), "public_location": voucher.public_location,
                    } for link, voucher, taxon_name in links],
                }
                for preparation, sample, study, links in (preparations[preparation_id] for preparation_id in preparation_ids
                                                          if preparation_id in preparations)
            ],
            "unavailable": len(profile_ids) - len(records) + len(specimen_ids) - len(vouchers)
                           + len(preparation_ids) - len(preparations),
        }

    def edit(self, deposition_id, data, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        if deposition.draft_revision != data.expected_revision:
            raise HTTPException(409, "The draft revision changed. Reload the draft.")
        if deposition.latest_version and not data.correction_reason:
            raise HTTPException(409, "Supply a correction reason for a new version of a published deposition.")
        if not deposition.latest_version and data.correction_reason:
            raise HTTPException(409, "A correction requires a published version.")
        self._check_draft_references(data)
        deposition.draft = data.model_dump(exclude={"expected_revision"})
        deposition.draft_revision = new_id()
        self.db.commit()
        return self._draft_summary(deposition)

    def _check_draft_references(self, data):
        for ids, column, label in ((data.profile_ids, Profile.id, "run"),
                                   (data.preparation_ids, Preparation.id, "preparation"),
                                   (data.specimen_ids, Specimen.specimen_id, "voucher")):
            if ids and len(list(self.db.scalars(select(column).where(column.in_(ids))))) != len(ids):
                raise HTTPException(409, f"A linked {label} no longer exists. Remove it from the draft and save again.")

    def discard_draft(self, deposition_id, expected_revision, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        if deposition.draft is None or deposition.draft_revision != expected_revision:
            raise HTTPException(409, "The draft changed. Reload the deposition before discarding it.")
        if deposition.submitted_at is not None:
            raise HTTPException(409, "Take the draft back from review before discarding it.")
        if deposition.latest_version:
            deposition.draft = None
            deposition.draft_revision = None
        else:
            self.db.delete(deposition)
        self.db.commit()

    def preview(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor)
        if deposition.draft is None:
            raise HTTPException(409, "Create a draft before previewing.")
        releases = {}
        snapshot, _ = build_snapshot(self.db, deposition, releases)
        summary = release_summary(releases)
        return {"draft_revision": deposition.draft_revision, "snapshot": snapshot,
                "snapshot_sha256": snapshot_digest(snapshot), "releases": summary,
                "releases_sha256": release_digest(summary)}

    @staticmethod
    def _version_identity(deposition, version):
        return {
            "institution": deposition.institution, "accession": deposition.accession, "version": version.number,
            "url": version.snapshot.get("url") or version_url(deposition, version.number),
            "identifier": version.snapshot.get("identifier"),
            "published_at": version.published_at.isoformat() + "Z",
            "snapshot_sha256": version.snapshot_sha256,
        }

    def _latest_url(self, deposition):
        latest = self.db.get(DepositionVersion, (deposition.id, deposition.latest_version))
        return (latest.snapshot.get("url") if latest else None) or version_url(deposition, deposition.latest_version)

    def publish(self, deposition_id, data, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        prior = self.db.scalar(select(DepositionVersion).where(
            DepositionVersion.deposition_id == deposition.id, DepositionVersion.draft_revision == data.draft_revision,
        ))
        if prior is not None:
            if prior.snapshot_sha256 != data.snapshot_sha256:
                raise HTTPException(409, "The published version has a different snapshot digest.")
            return self._version_identity(deposition, prior)
        if deposition.draft is None or deposition.draft_revision != data.draft_revision:
            raise HTTPException(409, "The draft revision changed. Review a new preview.")
        releases = {}
        snapshot, files = build_snapshot(self.db, deposition, releases)
        digest = snapshot_digest(snapshot)
        if digest != data.snapshot_sha256:
            raise HTTPException(409, "The linked records or files changed. Review a new preview.")
        if release_digest(release_summary(releases)) != data.releases_sha256:
            raise HTTPException(409, "What publishing would release or make public changed since the preview, "
                                     "or was not approved. Review a new preview.")
        version = DepositionVersion(
            deposition_id=deposition.id, number=snapshot["version"], draft_revision=data.draft_revision,
            published_by=actor.user_id, published_at=utc_now(), snapshot=snapshot, snapshot_sha256=digest,
        )
        deposition.latest_version = version.number
        deposition.draft = None
        deposition.draft_revision = None
        deposition.submitted_at = None
        self.db.add(version)
        self.db.flush()
        self.db.add_all(DepositionFile(deposition_id=deposition.id, version=version.number,
                                       profile_id=profile_id, content=content)
                        for profile_id, content in files.items())
        # Publishing is the curator's approval of everything the version contains: its private records go public
        # with it, in the same transaction. Vouchers keep the public locality setting they have.
        for record in (*releases["studies"], *releases["profiles"], *releases["vouchers"]):
            record.is_public = record.ever_public = True
        self.db.commit()
        return self._version_identity(deposition, version)

    def _existing_version(self, deposition_id, number, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        if self.db.get(DepositionVersion, (deposition.id, number)) is None:
            raise HTTPException(404, "Published version not found.")
        return deposition

    def link_article(self, deposition_id, number, doi, actor):
        deposition = self._existing_version(deposition_id, number, actor)
        if self.db.get(DepositionArticle, (deposition.id, number, doi)) is None:
            self.db.add(DepositionArticle(deposition_id=deposition.id, version=number, doi=doi,
                                          linked_by=actor.user_id, linked_at=utc_now()))
            self.db.commit()
        version = self.db.get(DepositionVersion, (deposition.id, number))
        return {"doi": doi, "url": self._version_identity(deposition, version)["url"]}

    def register_doi(self, deposition_id, number, data, actor):
        if settings.DEMO_MODE:
            raise HTTPException(409, "A demonstration instance does not register DOIs for its synthetic depositions.")
        deposition = self._existing_version(deposition_id, number, actor)
        current = self.db.get(DepositionDOI, (deposition.id, number))
        if current is not None:
            if current.doi != data.doi:
                raise HTTPException(409, f"Version {number} already has the dataset DOI {current.doi}.")
            return self._doi(current)
        if self.db.scalar(select(DepositionDOI.doi).where(DepositionDOI.doi == data.doi)):
            raise HTTPException(409, "That DOI is already registered for another version.")
        record = DepositionDOI(deposition_id=deposition.id, version=number, doi=data.doi, agency=data.agency,
                               record_url=data.record_url, registered_by=actor.user_id, registered_at=utc_now())
        self.db.add(record)
        self.db.commit()
        return self._doi(record)

    @staticmethod
    def _doi(record):
        return {"doi": record.doi, "url": f"https://doi.org/{record.doi}", "agency": record.agency,
                "record_url": record.record_url}

    def withdraw(self, deposition_id, number, reason, actor):
        deposition = self._existing_version(deposition_id, number, actor)
        notice = self.db.get(DepositionWithdrawal, (deposition.id, number))
        if notice is None:
            notice = DepositionWithdrawal(deposition_id=deposition.id, version=number, reason=reason,
                                          withdrawn_by=actor.user_id, withdrawn_at=utc_now())
            self.db.add(notice)
            self.db.commit()
        elif notice.reason != reason:
            raise HTTPException(409, "This version already has a withdrawal notice.")
        return self._notice(notice)

    @staticmethod
    def _notice(notice):
        return {"reason": notice.reason, "withdrawn_at": notice.withdrawn_at.isoformat() + "Z"}

    def _public_version(self, institution, accession, number):
        row = self.db.execute(
            select(Deposition, DepositionVersion)
            .join(DepositionVersion, Deposition.id == DepositionVersion.deposition_id)
            .where(Deposition.institution == institution.upper(), Deposition.accession == accession,
                   DepositionVersion.number == number)
        ).one_or_none()
        if row is None:
            raise HTTPException(404, "Published version not found.")
        deposition, version = row
        if snapshot_digest(version.snapshot) != version.snapshot_sha256:
            raise HTTPException(503, "The stored deposition metadata failed verification.")
        notice = self.db.get(DepositionWithdrawal, (deposition.id, number))
        return deposition, version, notice

    def public_version(self, institution, accession, number):
        deposition, version, notice = self._public_version(institution, accession, number)
        metadata = self._version_identity(deposition, version)
        metadata["title"] = version.snapshot["title"]
        metadata["institution_name"] = version.snapshot["institution_name"]
        metadata["article_dois"] = list(self.db.scalars(
            select(DepositionArticle.doi).filter_by(deposition_id=deposition.id, version=number)
            .order_by(DepositionArticle.doi)
        ))
        metadata["latest_version_url"] = self._latest_url(deposition)
        dataset_doi = self.db.get(DepositionDOI, (deposition.id, number))
        metadata["dataset_doi"] = self._doi(dataset_doi) if dataset_doi else None
        if notice:
            return 410, {**metadata, "status": "withdrawn", "withdrawal": self._notice(notice)}
        return 200, {
            **metadata, "status": "superseded" if number < deposition.latest_version else "published",
            "snapshot": version.snapshot,
        }

    def public_datacite(self, institution, accession, number):
        deposition, version, notice = self._public_version(institution, accession, number)
        if notice:
            raise HTTPException(410, f"This version was withdrawn. See {self._version_identity(deposition, version)['url']}.")
        if version.snapshot["schema_version"] < 2:
            raise HTTPException(404, "DataCite metadata needs a version published with absolute identifiers.")
        dataset_doi = self.db.get(DepositionDOI, (deposition.id, number))
        articles = list(self.db.scalars(
            select(DepositionArticle.doi).filter_by(deposition_id=deposition.id, version=number)
            .order_by(DepositionArticle.doi)
        ))
        return datacite_metadata(version.snapshot, version.published_at, articles,
                                 dataset_doi.doi if dataset_doi else None)

    def public_file(self, institution, accession, number, profile_id):
        deposition, version, notice = self._public_version(institution, accession, number)
        if notice:
            raise HTTPException(410, f"This version was withdrawn. See {self._version_identity(deposition, version)['url']}.")
        metadata = next((profile["file"] for profile in version.snapshot["profiles"] if profile["id"] == profile_id),
                        None)
        if metadata is None:
            raise HTTPException(404, "Version file not found.")
        return self._checked_file(deposition.id, number, profile_id, metadata), metadata

    def _checked_file(self, deposition_id, number, profile_id, metadata):
        stored = self.db.get(DepositionFile, (deposition_id, number, profile_id), options=[undefer(DepositionFile.content)])
        if (stored is None or len(stored.content) != metadata["size"]
                or sha256(stored.content).hexdigest() != metadata["sha256"]):
            raise HTTPException(503, "The stored deposition file failed verification.")
        return stored.content

    def public_archive(self, institution, accession, number):
        deposition, version, notice = self._public_version(institution, accession, number)
        if notice:
            raise HTTPException(410, f"This version was withdrawn. See {self._version_identity(deposition, version)['url']}.")
        files = {profile["id"]: self._checked_file(deposition.id, number, profile["id"], profile["file"])
                 for profile in version.snapshot["profiles"]}
        filename = f"{deposition.institution}-{deposition.accession}-v{version.number}.zip"
        return build_archive(version.snapshot, files), version.snapshot_sha256, filename


def correction_start(snapshot) -> dict:
    """A draft that repeats a published version, as the starting point of a correction."""
    linked = set()
    for profile in snapshot.get("profiles") or []:
        if "voucher" in profile:
            linked.add(profile["voucher"]["id"])
        else:
            linked.update(link["id"] for link in profile["sample"]["vouchers"])
    for preparation in snapshot.get("preparations") or []:
        linked.update(link["id"] for link in preparation["sample"]["vouchers"])
    vouchers = snapshot.get("vouchers") or []
    return {
        "title": snapshot.get("title"), "description": snapshot.get("description") or "",
        "license": snapshot.get("license"), "rights_statement": snapshot.get("rights_statement") or "",
        "contributors": snapshot.get("contributors") or [],
        "profile_ids": [profile["id"] for profile in snapshot.get("profiles") or []],
        "preparation_ids": [preparation["id"] for preparation in snapshot.get("preparations") or []],
        "specimen_ids": [voucher["id"] for voucher in vouchers if voucher["id"] not in linked],
        # The snapshot holds these names only when the version included them.
        "include_collector_names": any("collector_name" in voucher for voucher in vouchers),
        "include_determiner_names": any("determiner_name" in (voucher.get("determination") or {}) for voucher in vouchers),
    }
