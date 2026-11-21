"""Curation area for curators: review queue, vouchers, directories and accounts.

The pages only lay out lists and forms; every change goes through the existing curator API.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deposition.services import DepositionService
from app.field_loc.models import FieldLoc
from app.specimen.schemas.specimen_schemas import TYPE_STATUSES
from app.storage.models import Storage
from app.users.models import User

router = APIRouter(include_in_schema=False)
TABS = (("review", "Review"), ("vouchers", "Vouchers"), ("directories", "Directories"), ("accounts", "Accounts"))
DIRECTORIES = (("institutions", "Institutions"), ("storage", "Storage"), ("locations", "Field locations"),
               ("bibliography", "Bibliography"), ("taxonomy", "Taxonomy"))


def _web():
    from . import routes  # routes imports this module
    return routes


def _curation(request: Request, tab: str, **context):
    web = _web()
    viewer = web.viewer(request)
    if viewer is None:
        return web.sign_in_redirect(request)
    if not viewer["curator"]:
        return web.render(request, "work-missing.html", status=404, what="Page")
    return web.render(request, f"curation-{tab}.html", tabs=TABS, tab=tab, **context)


@router.get("/curation")
def review(request: Request, db: Session = Depends(get_db)):
    viewer = _web().viewer(request)
    queue = DepositionService(db).list_review() if viewer and viewer["curator"] else []
    return _curation(request, "review", queue=queue)


@router.get("/curation/vouchers")
def vouchers(request: Request, db: Session = Depends(get_db)):
    viewer = _web().viewer(request)
    if not viewer or not viewer["curator"]:
        return _curation(request, "vouchers")
    locations = db.scalars(select(FieldLoc).order_by(FieldLoc.country, FieldLoc.region, FieldLoc.locality)).all()
    storage = db.scalars(select(Storage).order_by(Storage.room, Storage.shelf, Storage.box)).all()
    return _curation(request, "vouchers", locations=locations, storage=storage, type_statuses=TYPE_STATUSES)


@router.get("/curation/directories")
@router.get("/curation/directories/{kind}")
def directories(request: Request, kind: str = "institutions"):
    if kind not in dict(DIRECTORIES):
        return _web().render(request, "work-missing.html", status=404, what="Directory")
    return _curation(request, "directories", directories=DIRECTORIES, kind=kind, kind_label=dict(DIRECTORIES)[kind])


@router.get("/curation/accounts")
def accounts(request: Request, db: Session = Depends(get_db)):
    viewer = _web().viewer(request)
    users = db.scalars(select(User).order_by(User.surname, User.name, User.email)).all() if viewer and viewer["curator"] else []
    return _curation(request, "accounts", users=users)
