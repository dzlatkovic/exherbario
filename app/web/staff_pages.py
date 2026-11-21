"""Signed-in specimen record: the full archive view with curator actions beside the data they change."""

import qrcode
from fastapi import APIRouter, Depends, Request
from markupsafe import Markup
from qrcode.image.svg import SvgPathImage
from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app import catalog
from app.chemistry.models import LabSample, SampleVoucher, Study
from app.config import settings
from app.db import get_db
from app.image.models import Image
from app.specimen.models import Revision, Specimen
from app.storage.models import Storage
from app.taxonomy.models import Taxonomy
from app.users.models import User

router = APIRouter(include_in_schema=False)


def qr_svg(text: str) -> Markup:
    """An inline SVG QR code, so the label prints without loading anything else."""
    image = qrcode.make(text, image_factory=SvgPathImage, box_size=10, border=2)
    return Markup(image.to_string(encoding="unicode"))


def _web():
    from . import routes  # routes imports this module
    return routes


def _person(db: Session, user_id: str | None, recorded: str | None = None):
    if recorded:
        return recorded
    user = db.get(User, user_id) if user_id else None
    return f"{user.name} {user.surname}".strip() if user else None


def _record(db: Session, specimen_id: str, viewer: dict):
    specimen = db.get(Specimen, specimen_id[:50])
    if specimen is None:
        return None
    taxon = db.get(Taxonomy, specimen.taxon_id) if specimen.taxon_id else None
    revisions = db.execute(
        select(Revision, Taxonomy.taxon_name).outerjoin(Taxonomy, Taxonomy.taxon_id == Revision.prev_taxon_id)
        .where(Revision.specimen_id == specimen.specimen_id).order_by(Revision.timestamp.desc())).all()
    photos = db.scalars(select(Image).where(Image.specimen_id == specimen.specimen_id)
                        .order_by(Image.upload_date, Image.image_id)).all()
    studies = db.execute(
        select(Study.id, Study.title, SampleVoucher.role, LabSample.code).join(LabSample, LabSample.study_id == Study.id)
        .join(SampleVoucher, SampleVoucher.sample_id == LabSample.id)
        .where(SampleVoucher.specimen_id == specimen.specimen_id,
               # Other researchers' studies stay private; curators see every study.
               true() if viewer["curator"] else Study.owner_id == viewer["id"])
        .order_by(Study.title, LabSample.code)).all()
    return {
        "specimen": specimen, "taxon": taxon, "location": specimen.field_loc,
        "storage": db.get(Storage, specimen.storage_id) if specimen.storage_id else None,
        "name": (taxon.taxon_name if taxon else None) or specimen.subnomen or "Unidentified specimen",
        "collector": _person(db, specimen.collected_by, specimen.collector_name),
        "verifier": _person(db, specimen.verified_by, specimen.verifier_name),
        "revisions": revisions, "photos": photos, "studies": studies,
        "publications": catalog.specimen_publications_any(db, specimen.specimen_id),
    }


@router.get("/researcher/specimens/{specimen_id}")
def staff_specimen(request: Request, specimen_id: str, db: Session = Depends(get_db)):
    web = _web()
    viewer = web.viewer(request)
    if viewer is None:
        return web.sign_in_redirect(request)
    record = _record(db, specimen_id, viewer)
    if record is None:
        return web.render(request, "staff-specimen.html", status=404, record=None)
    return web.render(request, "staff-specimen.html", record=record, curator=viewer["curator"])


@router.get("/researcher/specimens/{specimen_id}/label")
def staff_label(request: Request, specimen_id: str, db: Session = Depends(get_db)):
    web = _web()
    viewer = web.viewer(request)
    if viewer is None:
        return web.sign_in_redirect(request)
    record = _record(db, specimen_id, viewer)
    if record is None:
        return web.render(request, "staff-specimen.html", status=404, record=None)
    public_url = settings.PUBLIC_BASE_URL.rstrip("/") + f"/specimens/{record['specimen'].specimen_id}"
    return web.render(request, "label.html", record=record, public_url=public_url, qr_svg=qr_svg(public_url))
