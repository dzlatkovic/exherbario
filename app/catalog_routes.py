"""Public JSON, CSV, and image endpoints for the herbarium catalog."""

from csv import DictWriter
from datetime import date
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import catalog
from app.db import get_db
from app.image.exceptions import ImageNotFoundException, InvalidImageFileException
from app.image.services import ImageService
from app.specimen.models import Specimen
from app.taxonomy.models import Taxonomy

router = APIRouter()


class Filters:
    def __init__(self, q: str = Query("", max_length=150), reg_no: str = Query("", max_length=10),
                 taxon: str = Query("", max_length=100), region: str = Query("", max_length=80),
                 box: str = Query("", max_length=100), start_date: date | None = None,
                 end_date: date | None = None):
        if start_date and end_date and start_date > end_date:
            raise HTTPException(422, "The collection start date must come before the end date.")
        self.values = {"q": q.strip(), "reg_no": reg_no.strip(), "taxon": taxon.strip(),
                       "region": region.strip(), "box": box.strip(), "start_date": start_date,
                       "end_date": end_date}


@router.get("/api/specimen", tags=["Catalog"])
def list_specimens(filters: Filters = Depends(), page: int = Query(1, ge=1, le=1_000_000),
                   size: int = Query(12, ge=1, le=100), db: Session = Depends(get_db)):
    return catalog.find_specimens(db, page=page, size=size, **filters.values)


@router.get("/api/specimen/export", tags=["Catalog"], response_class=Response)
def export_specimens(filters: Filters = Depends(), db: Session = Depends(get_db)):
    results = catalog.find_specimens(db, size=10_000, **filters.values)
    if results["total"] > 10_000:
        raise HTTPException(422, "Narrow the filters to export at most 10,000 specimens.")
    fields = ("reg_no", "name", "common_name", "subnomen", "collection_date", "locality", "region", "country")
    output = StringIO(newline="")
    writer = DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in results["items"]:
        writer.writerow({field: csv_cell(row[field]) for field in fields})
    return Response(output.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": 'attachment; filename="herbar-specimens.csv"',
        "X-Content-Type-Options": "nosniff",
    })


def csv_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def require_specimen(db, specimen_id):
    if db.get(Specimen, specimen_id) is None:
        raise HTTPException(404, "Specimen not found.")


@router.get("/api/specimen/{specimen_id}", tags=["Catalog"])
def get_specimen_details(specimen_id: str, db: Session = Depends(get_db)):
    record = catalog.specimen_details(db, specimen_id)
    if record is None:
        raise HTTPException(404, "Specimen not found.")
    specimen, taxon, location = record["specimen"], record["taxon"], record["location"]
    return {
        "specimen_id": specimen.specimen_id,
        "reg_no": specimen.reg_no,
        "name": record["name"],
        "subnomen": specimen.subnomen,
        "collection_date": specimen.collection_date,
        "reg_date": specimen.reg_date,
        "collected_by": record["collector"] or None,
        "verified_by": record["verifier"] or None,
        "taxon": {
            "taxon_id": taxon.taxon_id, "name": taxon.taxon_name,
            "common_name": taxon.common_name, "gbif_key": taxon.gbif_key,
        } if taxon else None,
        "location": {
            "locality": location.locality, "region": location.region,
            "country": location.country, "habitat": location.habitat,
        } if location else None,
        "photos": [
            {"image_id": photo.image_id, "image_type": photo.image_type,
             "upload_date": photo.upload_date, "content_url": f"/api/image/{photo.image_id}/content"}
            for photo in catalog.specimen_photos(db, specimen_id)
        ],
    }


@router.get("/api/specimen/{specimen_id}/revisions", tags=["Catalog"])
def list_revisions(specimen_id: str, db: Session = Depends(get_db)):
    require_specimen(db, specimen_id)
    return catalog.specimen_revisions(db, specimen_id)


@router.get("/api/specimen/{specimen_id}/publications", tags=["Catalog"])
def list_publications(specimen_id: str, db: Session = Depends(get_db)):
    require_specimen(db, specimen_id)
    return [{"publication_id": p.pub_id, "title": p.title, "doi": p.doi, "year": p.year,
             "journal": p.journal} for p in catalog.specimen_publications(db, specimen_id)]


@router.get("/api/image/{image_id}/content", tags=["Image"], response_class=FileResponse,
            responses={200: {"content": {"image/jpeg": {}}}})
def image_content(image_id: str):
    try:
        image = ImageService.get_image_by_id(image_id)
        path = ImageService.storage_path(image.file_path)
    except (ImageNotFoundException, InvalidImageFileException, TypeError) as error:
        raise HTTPException(404, "Image file not found.") from error
    if not path.is_file():
        raise HTTPException(404, "Image file not found.")
    return FileResponse(path, media_type="image/jpeg", headers={"X-Content-Type-Options": "nosniff"})


@router.get("/api/taxonomy", tags=["Taxonomy"])
def list_taxa(query: str = Query("", max_length=100), parent_id: str | None = None,
              page: int = Query(1, ge=1, le=1_000_000), size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db)):
    statement = select(Taxonomy)
    if query.strip():
        statement = statement.where(Taxonomy.taxon_name.icontains(query.strip(), autoescape=True))
    if parent_id:
        statement = statement.where(Taxonomy.parent_taxon_key == parent_id)
    elif not query.strip():
        statement = statement.where(Taxonomy.parent_taxon_key.is_(None))
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    taxa = db.scalars(statement.order_by(Taxonomy.taxon_name, Taxonomy.taxon_id)
                     .offset((page - 1) * size).limit(size))
    return {"total": total, "page": page, "size": size, "items": [
        {"taxon_id": taxon.taxon_id, "name": taxon.taxon_name, "rank": taxon.taxon_rank,
         "parent_id": taxon.parent_taxon_key, "gbif_key": taxon.gbif_key} for taxon in taxa
    ]}
