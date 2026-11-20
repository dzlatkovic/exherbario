"""Authorize draft edits and commit immutable public versions."""

from datetime import datetime, timezone
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import lock_for_update, new_id

from .models import Deposition, DepositionArticle, DepositionFile, DepositionVersion, DepositionWithdrawal
from .snapshot import build_snapshot, snapshot_digest, version_url


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
        }

    def create(self, data, actor):
        if data.correction_reason is not None:
            raise HTTPException(409, "A correction requires a published version.")
        deposition = Deposition(institution=data.institution, owner_id=actor.user_id,
                                draft=data.dict(exclude={"institution"}), draft_revision=new_id())
        self.db.add(deposition)
        self.db.commit()
        return self._draft_summary(deposition)

    def get_draft(self, deposition_id, actor):
        return self._draft_summary(self._deposition(deposition_id, actor))

    def edit(self, deposition_id, data, actor):
        deposition = self._deposition(deposition_id, actor, for_update=True)
        if deposition.draft_revision != data.expected_revision:
            raise HTTPException(409, "The draft revision changed. Reload the draft.")
        if deposition.latest_version and not data.correction_reason:
            raise HTTPException(409, "Supply a correction reason for a new version of a published deposition.")
        if not deposition.latest_version and data.correction_reason:
            raise HTTPException(409, "A correction requires a published version.")
        deposition.draft = data.dict(exclude={"expected_revision"})
        deposition.draft_revision = new_id()
        self.db.commit()
        return self._draft_summary(deposition)

    def preview(self, deposition_id, actor):
        deposition = self._deposition(deposition_id, actor)
        if deposition.draft is None:
            raise HTTPException(409, "Create a draft before previewing.")
        snapshot, _ = build_snapshot(self.db, deposition)
        return {"draft_revision": deposition.draft_revision, "snapshot": snapshot,
                "snapshot_sha256": snapshot_digest(snapshot)}

    @staticmethod
    def _version_identity(deposition, version):
        return {
            "institution": deposition.institution, "accession": deposition.accession, "version": version.number,
            "url": version_url(deposition, version.number), "published_at": version.published_at.isoformat() + "Z",
            "snapshot_sha256": version.snapshot_sha256,
        }

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
        snapshot, files = build_snapshot(self.db, deposition)
        digest = snapshot_digest(snapshot)
        if digest != data.snapshot_sha256:
            raise HTTPException(409, "The linked records or files changed. Review a new preview.")
        version = DepositionVersion(
            deposition_id=deposition.id, number=snapshot["version"], draft_revision=data.draft_revision,
            published_by=actor.user_id, published_at=utc_now(), snapshot=snapshot, snapshot_sha256=digest,
        )
        deposition.latest_version = version.number
        deposition.draft = None
        deposition.draft_revision = None
        self.db.add(version)
        self.db.flush()
        self.db.add_all(DepositionFile(deposition_id=deposition.id, version=version.number,
                                       profile_id=profile_id, content=content)
                        for profile_id, content in files.items())
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
        return {"doi": doi, "url": version_url(deposition, number)}

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
        if notice:
            return 410, {**metadata, "status": "withdrawn", "withdrawal": self._notice(notice)}
        return 200, {
            **metadata, "status": "superseded" if number < deposition.latest_version else "published",
            "latest_version_url": version_url(deposition, deposition.latest_version),
            "snapshot": version.snapshot,
        }

    def public_file(self, institution, accession, number, profile_id):
        deposition, version, notice = self._public_version(institution, accession, number)
        if notice:
            raise HTTPException(410, f"This version was withdrawn. See {version_url(deposition, number)}.")
        metadata = next((profile["file"] for profile in version.snapshot["profiles"] if profile["id"] == profile_id),
                        None)
        if metadata is None:
            raise HTTPException(404, "Version file not found.")
        stored = self.db.get(DepositionFile, (deposition.id, number, profile_id))
        if (stored is None or len(stored.content) != metadata["size"]
                or sha256(stored.content).hexdigest() != metadata["sha256"]):
            raise HTTPException(503, "The stored deposition file failed verification.")
        return stored.content, metadata
