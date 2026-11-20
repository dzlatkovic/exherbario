"""Routes for studies, samples, chemical profiles, compounds, imports and exports."""

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.chemistry.controller import ChemistryController
from app.chemistry.controller.import_controller import ImportController
from app.chemistry.repository import ChemistryRepository
from app.chemistry.pubchem import PubChemClient
from app.chemistry.schemas import (Basis, CompoundCorrectionIn, PreparationIn, PublicState, SampleIn, StudyIn,
                                   Technique, VoucherLinkIn)
from app.chemistry.services import ChemistryService
from app.chemistry.schemas.import_schemas import AssignmentIn, RowReviewIn
from app.chemistry.services.compounds import CompoundRegistry
from app.chemistry.services.export import ExportService
from app.chemistry.services.imports import ImportService
from app.db import get_db
from app.users.controller import JWTBearer
from app.users.models import User


def get_pubchem() -> PubChemClient:
    """Overridden in tests with a client that serves recorded PubChem responses."""
    return PubChemClient()


def get_chemistry_controller(db: Session = Depends(get_db),
                             pubchem: PubChemClient = Depends(get_pubchem)) -> ChemistryController:
    return ChemistryController(ChemistryService(ChemistryRepository(db), CompoundRegistry(db, pubchem)))


def get_import_controller(db: Session = Depends(get_db),
                          pubchem: PubChemClient = Depends(get_pubchem)) -> ImportController:
    registry = CompoundRegistry(db, pubchem)
    return ImportController(ImportService(ChemistryService(ChemistryRepository(db), registry), registry))


chemistry_router = APIRouter(prefix="/api/chemistry", tags=["Chemistry"])
authenticated = JWTBearer()
administrator = JWTBearer("super_user")


@chemistry_router.get("/studies")
def list_studies(actor: User = Depends(authenticated),
                 controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.list_studies(actor)


@chemistry_router.post("/studies", status_code=201)
def create_study(data: StudyIn, actor: User = Depends(authenticated),
                 controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.create_study(data, actor)


@chemistry_router.get("/studies/{study_id}")
def get_study(study_id: str, actor: User = Depends(authenticated),
              controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_study(study_id, actor)


@chemistry_router.post("/studies/{study_id}/samples", status_code=201)
def create_sample(study_id: str, data: SampleIn, actor: User = Depends(authenticated),
                  controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.create_sample(study_id, data, actor)


@chemistry_router.post("/samples/{sample_id}/vouchers", status_code=201)
def add_sample_voucher(sample_id: str, data: VoucherLinkIn, actor: User = Depends(authenticated),
                       controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.add_sample_voucher(sample_id, data, actor)


@chemistry_router.delete("/samples/{sample_id}/vouchers/{specimen_id}", status_code=204)
def remove_sample_voucher(sample_id: str, specimen_id: str, actor: User = Depends(authenticated),
                          controller: ChemistryController = Depends(get_chemistry_controller)):
    controller.remove_sample_voucher(sample_id, specimen_id, actor)


@chemistry_router.post("/samples/{sample_id}/preparations", status_code=201)
def create_preparation(sample_id: str, data: PreparationIn, actor: User = Depends(authenticated),
                       controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.create_preparation(sample_id, data, actor)


@chemistry_router.post("/preparations/{preparation_id}/profiles", status_code=201)
def import_profile(preparation_id: str, file: UploadFile = File(...),
                   run_code: str = Form(..., min_length=1, max_length=80),
                   analytical_method: str = Form(..., min_length=1, max_length=120),
                   measurement_basis: Basis = Form(...),
                   unit: str = Form(..., min_length=1, max_length=40),
                   technique: Technique = Form(...),
                   run_metadata: str = Form("{}", max_length=10000),
                   actor: User = Depends(authenticated),
                   controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.import_profile(
        preparation_id, file, run_code, analytical_method, measurement_basis, unit, actor, technique, run_metadata,
    )


@chemistry_router.put("/profiles/{profile_id}/measurements/{feature:path}/compound")
def correct_compound(profile_id: str, feature: str, data: CompoundCorrectionIn, actor: User = Depends(authenticated),
                     controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.correct_compound(profile_id, feature, data, actor)


@chemistry_router.post("/studies/{study_id}/imports", status_code=201)
def create_import(study_id: str, file: UploadFile = File(...), actor: User = Depends(authenticated),
                  controller: ImportController = Depends(get_import_controller)):
    return controller.create(study_id, file, actor)


@chemistry_router.get("/imports/{import_id}")
def get_import(import_id: str, actor: User = Depends(authenticated),
               controller: ImportController = Depends(get_import_controller)):
    return controller.get(import_id, actor)


@chemistry_router.put("/imports/{import_id}/assignment")
def assign_import(import_id: str, data: AssignmentIn, actor: User = Depends(authenticated),
                  controller: ImportController = Depends(get_import_controller)):
    return controller.assign(import_id, data, actor)


@chemistry_router.post("/imports/{import_id}/match")
def match_import(import_id: str, actor: User = Depends(authenticated),
                 controller: ImportController = Depends(get_import_controller)):
    return controller.match(import_id, actor)


@chemistry_router.put("/imports/{import_id}/rows/{row}/compound")
def review_import_row(import_id: str, data: RowReviewIn, row: int = Path(ge=1, le=100000),
                      actor: User = Depends(authenticated),
                      controller: ImportController = Depends(get_import_controller)):
    return controller.review_row(import_id, row, data, actor)


@chemistry_router.post("/imports/{import_id}/confirm", status_code=201)
def confirm_import(import_id: str, actor: User = Depends(authenticated),
                   controller: ImportController = Depends(get_import_controller)):
    return controller.confirm(import_id, actor)


@chemistry_router.get("/import-templates")
def list_import_templates(actor: User = Depends(authenticated),
                          controller: ImportController = Depends(get_import_controller)):
    return controller.list_templates(actor)


@chemistry_router.get("/imports/{import_id}/templates/{template_id}")
def apply_import_template(import_id: str, template_id: str, sheet: str | None = Query(None, max_length=100),
                          actor: User = Depends(authenticated),
                          controller: ImportController = Depends(get_import_controller)):
    return controller.apply_template(import_id, template_id, sheet, actor)


@chemistry_router.get("/compounds/search")
def search_compounds(q: str = Query(..., min_length=1, max_length=300),
                     namespace: str = Query("name", pattern="^(name|cas|cid|inchikey)$"),
                     actor: User = Depends(authenticated),
                     controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.search_compounds(q, namespace)


@chemistry_router.get("/compounds/{cid}/parent")
def parent_compound(cid: int = Path(gt=0, lt=2 ** 31), actor: User = Depends(authenticated),
                    controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.parent_compound(cid)


@chemistry_router.get("/public/export", response_class=Response)
def export_profiles(profile_id: list[str] = Query(default_factory=list, max_length=500),
                    study_id: str | None = Query(None, max_length=50),
                    format: str = Query("long", pattern="^(long|wide)$"),
                    db: Session = Depends(get_db)):
    """Released profiles as analysis-ready CSV: one row per measurement (long) or per profile (wide)."""
    service = ExportService(ChemistryRepository(db))
    content = service.long(profile_id, study_id) if format == "long" else service.wide(profile_id, study_id)
    return Response(content, media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="herbar-chemistry-{format}.csv"',
        "X-Content-Type-Options": "nosniff"})


@chemistry_router.get("/public/compounds/{cid}")
def get_public_compound(cid: int = Path(gt=0, lt=2 ** 31),
                        controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_public_compound(cid)


@chemistry_router.get("/profiles/{profile_id}")
def get_profile(profile_id: str, actor: User = Depends(authenticated),
                controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_profile(profile_id, actor)


@chemistry_router.get("/profiles/{profile_id}/source", response_class=Response)
def download_source(profile_id: str, actor: User = Depends(authenticated),
                    controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.download_source(profile_id, actor)


@chemistry_router.put("/studies/{study_id}/visibility")
def set_study_visibility(study_id: str, data: PublicState, actor: User = Depends(administrator),
                         controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.set_study_visibility(study_id, data, actor)


@chemistry_router.put("/profiles/{profile_id}/visibility")
def set_profile_visibility(profile_id: str, data: PublicState, actor: User = Depends(administrator),
                           controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.set_profile_visibility(profile_id, data, actor)


@chemistry_router.get("/public/studies/{study_id}")
def get_public_study(study_id: str, controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_public_study(study_id)


@chemistry_router.get("/public/profiles/{profile_id}")
def get_public_profile(profile_id: str, controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_public_profile(profile_id)


@chemistry_router.get("/public/specimens/{specimen_id}/profiles")
def get_public_specimen_profiles(specimen_id: str,
                                 controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_public_specimen_profiles(specimen_id)
