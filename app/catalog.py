"""Read models for the public herbarium catalog."""

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.field_loc.models import FieldLoc
from app.image.models import Image
from app.publication.models import Publication
from app.specimen.models import Revision, Specimen, SpecimenPublication
from app.taxonomy.models import Taxonomy


def public_specimen(db: Session, specimen_id: str):
    return db.scalar(select(Specimen).where(
        Specimen.specimen_id == specimen_id, Specimen.is_public.is_(True),
    ))


def public_location(specimen, location):
    if location is None or specimen.public_location != "region":
        return None
    return {"region": location.region, "country": location.country}


def find_specimens(db: Session, *, q="", reg_no="", taxon="", region="",
                   start_date: date | None = None, end_date: date | None = None,
                   page=1, size=12):
    query = (
        select(Specimen, Taxonomy.taxon_name, Taxonomy.common_name, FieldLoc)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
        .outerjoin(FieldLoc, FieldLoc.field_loc_id == Specimen.field_loc_id)
        .where(Specimen.is_public.is_(True))
    )
    if q:
        query = query.where(or_(
            Specimen.reg_no.icontains(q, autoescape=True),
            Specimen.subnomen.icontains(q, autoescape=True),
            Taxonomy.taxon_name.icontains(q, autoescape=True),
            Taxonomy.common_name.icontains(q, autoescape=True),
        ))
    if reg_no:
        query = query.where(Specimen.reg_no == reg_no)
    if taxon:
        query = query.where(Taxonomy.taxon_name.icontains(taxon, autoescape=True))
    if region:
        query = query.where(Specimen.public_location == "region",
                            FieldLoc.region.icontains(region, autoescape=True))
    if start_date:
        query = query.where(Specimen.collection_date >= start_date)
    if end_date:
        query = query.where(Specimen.collection_date <= end_date)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(Specimen.reg_no, Specimen.specimen_id).offset((page - 1) * size).limit(size)
    entries = []
    for specimen, taxon_name, common_name, location in db.execute(query):
        visible_location = public_location(specimen, location) or {}
        entries.append({
            "specimen_id": specimen.specimen_id,
            "reg_no": specimen.reg_no,
            "name": taxon_name or specimen.subnomen or "Unidentified specimen",
            "common_name": common_name,
            "subnomen": specimen.subnomen,
            "collection_date": specimen.collection_date,
            "locality": None,
            "region": visible_location.get("region"),
            "country": visible_location.get("country"),
        })
    return {"items": entries, "total": total, "page": page, "size": size}


def specimen_details(db: Session, specimen_id: str):
    record = db.execute(
        select(Specimen, Taxonomy, FieldLoc)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
        .outerjoin(FieldLoc, FieldLoc.field_loc_id == Specimen.field_loc_id)
        .where(Specimen.specimen_id == specimen_id, Specimen.is_public.is_(True))
    ).first()
    if record is None:
        return None
    specimen, taxon, location = record
    return {
        "specimen": specimen, "taxon": taxon, "location": public_location(specimen, location),
        "name": (taxon.taxon_name if taxon else specimen.subnomen) or "Unidentified specimen",
    }


def specimen_photos(db: Session, specimen_id: str):
    return db.scalars(
        select(Image).join(Specimen, Specimen.specimen_id == Image.specimen_id)
        .where(Image.specimen_id == specimen_id, Image.is_public.is_(True), Specimen.is_public.is_(True))
        .order_by(Image.upload_date, Image.image_id)
    ).all()


def specimen_revisions(db: Session, specimen_id: str):
    query = (
        select(Revision.revision_id, Revision.timestamp, Revision.prev_subnomen,
               Taxonomy.taxon_name)
        .join(Specimen, Specimen.specimen_id == Revision.specimen_id)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Revision.prev_taxon_id)
        .where(Revision.specimen_id == specimen_id, Specimen.is_public.is_(True))
        .order_by(Revision.timestamp.desc(), Revision.revision_id.desc())
    )
    return [
        {"revision_id": revision_id, "timestamp": timestamp, "previous_name": taxon_name,
         "previous_subnomen": subnomen}
        for revision_id, timestamp, subnomen, taxon_name in db.execute(query)
    ]


def specimen_publications(db: Session, specimen_id: str):
    return db.scalars(
        select(Publication)
        .join(SpecimenPublication, SpecimenPublication.publication_id == Publication.pub_id)
        .join(Specimen, Specimen.specimen_id == SpecimenPublication.specimen_id)
        .where(SpecimenPublication.specimen_id == specimen_id, Specimen.is_public.is_(True))
        .order_by(Publication.year.desc(), Publication.pub_id)
    ).all()
