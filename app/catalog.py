"""Read models for the public herbarium catalog."""

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from app.field_loc.models import FieldLoc
from app.image.models import Image
from app.publication.models import Publication
from app.specimen.models import Revision, Specimen, SpecimenPublication
from app.storage.models import Storage
from app.taxonomy.models import Taxonomy
from app.users.models import User


def find_specimens(db: Session, *, q="", reg_no="", taxon="", region="", box="",
                   start_date: date | None = None, end_date: date | None = None,
                   page=1, size=12):
    query = (
        select(Specimen, Taxonomy.taxon_name, Taxonomy.common_name,
               FieldLoc.locality, FieldLoc.region, FieldLoc.country)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
        .outerjoin(FieldLoc, FieldLoc.field_loc_id == Specimen.field_loc_id)
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
        query = query.where(FieldLoc.region.icontains(region, autoescape=True))
    if box:
        query = query.join(Storage, Storage.storage_id == Specimen.storage_id).where(Storage.box == box)
    if start_date:
        query = query.where(Specimen.collection_date >= start_date)
    if end_date:
        query = query.where(Specimen.collection_date <= end_date)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(Specimen.reg_no, Specimen.specimen_id).offset((page - 1) * size).limit(size)
    entries = []
    for specimen, taxon_name, common_name, locality, region_name, country in db.execute(query):
        entries.append({
            "specimen_id": specimen.specimen_id,
            "reg_no": specimen.reg_no,
            "name": taxon_name or specimen.subnomen or "Unidentified specimen",
            "common_name": common_name,
            "subnomen": specimen.subnomen,
            "collection_date": specimen.collection_date,
            "locality": locality,
            "region": region_name,
            "country": country,
        })
    return {"items": entries, "total": total, "page": page, "size": size}


def specimen_details(db: Session, specimen_id: str):
    collector = aliased(User)
    verifier = aliased(User)
    record = db.execute(
        select(Specimen, Taxonomy, FieldLoc, collector.name, collector.surname,
               verifier.name, verifier.surname)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
        .outerjoin(FieldLoc, FieldLoc.field_loc_id == Specimen.field_loc_id)
        .outerjoin(collector, collector.user_id == Specimen.collected_by)
        .outerjoin(verifier, verifier.user_id == Specimen.verified_by)
        .where(Specimen.specimen_id == specimen_id)
    ).first()
    if record is None:
        return None
    specimen, taxon, location, first, last, verifier_first, verifier_last = record
    return {
        "specimen": specimen, "taxon": taxon, "location": location,
        "collector": display_name(first, last), "verifier": display_name(verifier_first, verifier_last),
        "name": (taxon.taxon_name if taxon else specimen.subnomen) or "Unidentified specimen",
    }


def display_name(first, last):
    return " ".join(part for part in (first, last) if part)


def specimen_photos(db: Session, specimen_id: str):
    return db.scalars(
        select(Image).where(Image.specimen_id == specimen_id)
        .order_by(Image.upload_date, Image.image_id)
    ).all()


def specimen_revisions(db: Session, specimen_id: str):
    query = (
        select(Revision.revision_id, Revision.timestamp, Revision.prev_subnomen,
               Taxonomy.taxon_name, User.name, User.surname)
        .outerjoin(Taxonomy, Taxonomy.taxon_id == Revision.prev_taxon_id)
        .outerjoin(User, User.user_id == Revision.revised_by)
        .where(Revision.specimen_id == specimen_id)
        .order_by(Revision.timestamp.desc(), Revision.revision_id.desc())
    )
    return [
        {"revision_id": revision_id, "timestamp": timestamp, "previous_name": taxon_name,
         "previous_subnomen": subnomen, "revised_by": display_name(first, last)}
        for revision_id, timestamp, subnomen, taxon_name, first, last in db.execute(query)
    ]


def specimen_publications(db: Session, specimen_id: str):
    return db.scalars(
        select(Publication)
        .join(SpecimenPublication, SpecimenPublication.publication_id == Publication.pub_id)
        .where(SpecimenPublication.specimen_id == specimen_id)
        .order_by(Publication.year.desc(), Publication.pub_id)
    ).all()
