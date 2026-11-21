"""Public catalog pages: search, results and specimen records, rendered from public projections only."""

from datetime import date
from math import ceil
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app import catalog
from app.chemistry import lotus
from app.chemistry.repository import ChemistryRepository
from app.db import get_db
from app.deposition.services import DepositionService

router = APIRouter(include_in_schema=False)
PAGE_SIZE = 20
FILTERS = ("q", "holding_institution", "collection", "region", "start_date", "end_date")


def _date(value: str):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return False


def _query(values: dict, **changes) -> str:
    merged = {key: value for key, value in {**values, **changes}.items() if value not in (None, "", 1)}
    return "?" + urlencode(merged) if merged else ""


def render(request, *args, **kwargs):
    from .routes import render as render_page  # routes imports this module
    return render_page(request, *args, **kwargs)


@router.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    facets = catalog.public_facets(db)
    return render(request, "home.html", released=facets["total"])


@router.get("/depositions")
def depositions(request: Request, q: str = Query("", max_length=200), page: int = Query(1, ge=1, le=100_000),
                db: Session = Depends(get_db)):
    values = {"q": q.strip()}
    results = DepositionService(db).list_public(q=values["q"], page=page, size=PAGE_SIZE)
    pages = max(1, ceil(results["total"] / PAGE_SIZE))
    return render(request, "depositions.html", values=values, results=results, page=page, pages=pages,
                  previous_url=_query(values, page=page - 1) if page > 1 else None,
                  next_url=_query(values, page=page + 1) if page < pages else None)


@router.get("/specimens")
def specimens(request: Request, q: str = Query("", max_length=150),
              holding_institution: str = Query("", max_length=120), collection: str = Query("", max_length=120),
              region: str = Query("", max_length=80), start_date: str = Query("", max_length=10),
              end_date: str = Query("", max_length=10), page: int = Query(1, ge=1, le=100_000),
              db: Session = Depends(get_db)):
    values = {"q": q.strip(), "holding_institution": holding_institution.strip(), "collection": collection.strip(),
              "region": region.strip(), "start_date": start_date.strip(), "end_date": end_date.strip()}
    start, end = _date(values["start_date"]), _date(values["end_date"])
    problem = None
    if start is False or end is False:
        problem, start, end = "Enter dates as YYYY-MM-DD.", None, None
    elif start and end and start > end:
        problem, start, end = "The start date must come before the end date.", None, None
    results = catalog.find_specimens(
        db, q=values["q"], holding_institution=values["holding_institution"], collection=values["collection"],
        region=values["region"], start_date=start or None, end_date=end or None, page=page, size=PAGE_SIZE)
    facets = catalog.public_facets(db)
    pages = max(1, ceil(results["total"] / PAGE_SIZE))
    filtered = any(values.values())
    advanced = any(values[key] for key in FILTERS if key != "q")
    return render(
        request, "specimens.html", values=values, results=results, facets=facets, problem=problem,
        filtered=filtered, advanced=advanced, page=page, pages=pages,
        previous_url=_query(values, page=page - 1) if page > 1 else None,
        next_url=_query(values, page=page + 1) if page < pages else None,
        clear_url="/specimens", export_url="/api/specimen/export" + _query(values))


@router.get("/specimens/{specimen_id}")
def specimen(request: Request, specimen_id: str, db: Session = Depends(get_db)):
    record = catalog.specimen_details(db, specimen_id[:50])
    if record is None:
        # Unknown and unreleased records look the same.
        return render(request, "specimen.html", status=404, record=None)
    repository = ChemistryRepository(db)
    profiles = repository.list_released_specimen_profiles(specimen_id)
    studies = {study.id: study for study in (repository.get_study(sample.study_id) for _, _, sample in profiles)}
    return render(
        request, "specimen.html", record=record, specimen=record["specimen"], taxon=record["taxon"],
        location=record["location"], photos=catalog.specimen_photos(db, specimen_id),
        revisions=catalog.specimen_revisions(db, specimen_id),
        publications=catalog.specimen_publications(db, specimen_id),
        profiles=profiles, studies=studies, literature=lotus.published(db, record["specimen"].taxon_id))
