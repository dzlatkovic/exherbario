"""Signed-in work pages: My work, studies, private profiles, imports and depositions.

Data comes from the same services as the API, so ownership checks stay in one place.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi import HTTPException
from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, Measurement, Preparation, Profile, SpreadsheetImport, Study
from app.chemistry.repository import ChemistryRepository
from app.chemistry.sample_links import redetermined
from app.chemistry.services import ChemistryService
from app.chemistry.services.compounds import CompoundRegistry
from app.db import get_db
from app.deposition.services import DepositionService
from app.users import orcid
from app.users.models import User

from .chemistry_pages import NoPubChem, ROLE_LABELS, RUN_LABELS, has_values

# Shared with docs/ai-extraction.md, which links to it.
AI_PROMPT = Path(__file__).resolve().parents[1] / "chemistry" / "ai_extraction_prompt.md"

router = APIRouter(include_in_schema=False)
PUBCHEM_IMAGES = ("default-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; "
                  "img-src 'self' https://pubchem.ncbi.nlm.nih.gov")


def _web():
    from . import routes  # routes imports this module
    return routes


def _actor(request: Request, db: Session):
    web = _web()
    viewer = web.viewer(request)
    return (db.get(User, viewer["id"]), viewer) if viewer else (None, None)


def _service(db: Session) -> ChemistryService:
    return ChemistryService(ChemistryRepository(db), CompoundRegistry(db, NoPubChem()))


def _not_found(request, what):
    return _web().render(request, "work-missing.html", status=404, what=what)


@router.get("/researcher")
def my_work(request: Request, db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    studies = _service(db).list_studies(actor)
    ids = [study.id for study in studies]
    samples = dict(db.execute(select(LabSample.study_id, func.count()).where(LabSample.study_id.in_(ids))
                              .group_by(LabSample.study_id)).all()) if ids else {}
    profiles = dict(db.execute(select(LabSample.study_id, func.count(Profile.id)).join(Preparation, Preparation.sample_id == LabSample.id)
                               .join(Profile, Profile.preparation_id == Preparation.id).where(LabSample.study_id.in_(ids))
                               .group_by(LabSample.study_id)).all()) if ids else {}
    imports = db.execute(select(SpreadsheetImport, Study.title).join(Study, Study.id == SpreadsheetImport.study_id)
                         .where(SpreadsheetImport.owner_id == actor.user_id, SpreadsheetImport.status == "draft")
                         .order_by(SpreadsheetImport.created_at.desc()).limit(10)).all()
    return _web().render(request, "mywork.html", studies=studies, sample_counts=samples, profile_counts=profiles,
                         depositions=DepositionService(db).list_for_owner(actor), imports=imports,
                         curator=viewer["curator"], account=actor, orcid_enabled=orcid.enabled())


def results_tables(db: Session, study_id: str, profiles):
    """Confirmed spreadsheet imports of a study, each with the profiles derived from it.

    The method is read from the derived runs: the import itself does not record one.
    """
    records = db.scalars(select(SpreadsheetImport).where(
        SpreadsheetImport.study_id == study_id, SpreadsheetImport.status == "confirmed")
        .order_by(SpreadsheetImport.confirmed_at.desc(), SpreadsheetImport.created_at.desc())).all()
    if not records:
        return []
    derived = {}
    for profile, preparation, sample in profiles:
        if profile.import_id:
            derived.setdefault(profile.import_id, []).append((profile, preparation, sample))
    compounds = dict(db.execute(
        # Compounds are the table's rows, recorded once per run under the same feature name.
        select(Profile.import_id, func.count(func.distinct(Measurement.feature)))
        .join(Measurement, Measurement.profile_id == Profile.id)
        .where(Profile.import_id.in_([record.id for record in records])).group_by(Profile.import_id)).all())
    tables = []
    for record in records:
        rows = derived.get(record.id, [])
        methods = sorted({profile.technique or profile.analytical_method for profile, _, _ in rows} - {None, ""})
        tables.append({
            "record": record, "profiles": len(rows), "samples": len({sample.id for _, _, sample in rows}),
            "preparations": len({preparation.id for _, preparation, _ in rows}),
            "compounds": compounds.get(record.id, 0),
            "method": methods[0] if len(methods) == 1 else ("mixed: " + ", ".join(methods) if methods else None),
        })
    return tables


@router.get("/researcher/studies/{study_id}")
def study(request: Request, study_id: str, table: str = "", db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    try:
        record, samples, links, preparations, profiles = _service(db).get_study(study_id[:50], actor)
    except ChemistryError:
        return _not_found(request, "Study")
    tables = results_tables(db, record.id, profiles)
    shown_table = next((item for item in tables if item["record"].id == table[:50]), None) if table else None
    all_samples, all_preparations, all_profiles = samples, preparations, profiles
    if shown_table:
        # Only the records derived from one results table; nothing else on the page changes.
        profiles = [row for row in profiles if row[0].import_id == shown_table["record"].id]
        kept_preparations = {preparation.id for _, preparation, _ in profiles}
        preparations = [preparation for preparation in preparations if preparation.id in kept_preparations]
        kept_samples = {preparation.sample_id for preparation in preparations}
        samples = [sample for sample in samples if sample.id in kept_samples]
    by_sample = {sample.id: [] for sample in samples}
    for preparation in preparations:
        by_sample[preparation.sample_id].append(preparation)
    runs = {}
    for profile, preparation, _ in profiles:
        runs.setdefault(preparation.id, []).append(profile)
    imports = db.scalars(select(SpreadsheetImport).where(
        SpreadsheetImport.study_id == record.id, SpreadsheetImport.status == "draft",
        true() if viewer["curator"] else SpreadsheetImport.owner_id == actor.user_id)
        .order_by(SpreadsheetImport.created_at.desc())).all()
    import_count = db.scalar(select(func.count()).select_from(SpreadsheetImport).where(
        SpreadsheetImport.study_id == record.id))
    vouchers = {sample_id: [{"id": link.specimen_id, "role": ROLE_LABELS.get(link.role, link.role),
                             "name": taxon_name or voucher.subnomen or "Unidentified specimen",
                             "accession": voucher.accession or voucher.reg_no, "redetermined": redetermined(link, voucher)}
                            for link, voucher, taxon_name in rows] for sample_id, rows in links.items()}
    deposited = ChemistryRepository(db).deposited_preparations([preparation.id for preparation in all_preparations])
    with_runs = {preparation.id for _, preparation, _ in all_profiles}
    progress = {
        "samples": len(all_samples), "preparations": len(all_preparations),
        "without_runs": len([item for item in all_preparations if item.id not in with_runs]),
        "runs": len(all_profiles), "released_runs": len([row for row in all_profiles if row[0].is_public]),
        "tables": len(tables), "unfinished": len(imports), "deposited": len(deposited),
    }
    return _web().render(request, "staff-study.html", study=record, samples=samples, vouchers=vouchers,
                         preparations=by_sample, runs=runs, imports=imports, curator=viewer["curator"],
                         preparation_count=len(all_preparations), run_count=len(all_profiles),
                         import_count=import_count, tables=tables, shown_table=shown_table, progress=progress,
                         ai_prompt=AI_PROMPT.read_text(encoding="utf-8"), deposited_preparations=deposited,
                         has_released_runs=any(profile.is_public or profile.ever_public
                                               for profile, _, _ in all_profiles))


@router.get("/researcher/profiles/{profile_id}")
def profile(request: Request, profile_id: str, db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    service = _service(db)
    try:
        record, measurements, corrections = service.get_profile(profile_id[:50], actor)
    except ChemistryError:
        return _not_found(request, "Profile")
    repository = service.repository
    preparation = repository.get_preparation(record.preparation_id)
    sample = repository.get_sample(preparation.sample_id)
    measurements = sorted(measurements, key=lambda item: (item[0].rt_min is None, item[0].rt_min or 0,
                                                          item[0].feature.casefold()))
    return _web().render(request, "staff-profile.html", profile=record, preparation=preparation, sample=sample,
                         study=repository.get_study(sample.study_id), measurements=measurements,
                         corrections=corrections, run_labels=RUN_LABELS, curator=viewer["curator"],
                         has=has_values(measurements), headers={"Content-Security-Policy": PUBCHEM_IMAGES})


@router.get("/researcher/studies/{study_id}/imports/{import_id}")
def import_page(request: Request, study_id: str, import_id: str, db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    record = db.get(SpreadsheetImport, import_id[:50])
    try:
        study = _service(db)._study_for_actor(study_id[:50], actor)
    except ChemistryError:
        study = None
    if (study is None or record is None or record.study_id != study.id
            or (not viewer["curator"] and record.owner_id != actor.user_id)):
        return _not_found(request, "Import")
    return _web().render(request, "import.html", study=study, record=record,
                         headers={"Content-Security-Policy": PUBCHEM_IMAGES})


@router.get("/researcher/depositions/new")
def new_deposition(request: Request, db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    return _web().render(request, "deposition-edit.html", deposition_id="", curator=viewer["curator"], account=actor)


@router.get("/researcher/depositions/{deposition_id}")
def edit_deposition(request: Request, deposition_id: str, db: Session = Depends(get_db)):
    actor, viewer = _actor(request, db)
    if actor is None:
        return _web().sign_in_redirect(request)
    try:
        DepositionService(db).get_draft(deposition_id[:50], actor)
    except HTTPException:  # unknown and other people's depositions look the same
        return _not_found(request, "Deposition")
    return _web().render(request, "deposition-edit.html", deposition_id=deposition_id, curator=viewer["curator"],
                         account=actor)
