"""Routes for studies, chemical profiles, and PCA."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.chemistry.controller import ChemistryController
from app.chemistry.repository import ChemistryRepository
from app.chemistry.schemas import Basis, PCAIn, PreparationIn, PublicState, SampleIn, StudyIn, VoucherLinkIn
from app.chemistry.services import ChemistryService
from app.db import get_db
from app.users.controller import JWTBearer
from app.users.models import User


def get_chemistry_controller(db: Session = Depends(get_db)) -> ChemistryController:
    return ChemistryController(ChemistryService(ChemistryRepository(db)))


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
                   actor: User = Depends(authenticated),
                   controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.import_profile(
        preparation_id, file, run_code, analytical_method, measurement_basis, unit, actor,
    )


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


@chemistry_router.post("/studies/{study_id}/pca", status_code=201)
def run_pca(study_id: str, data: PCAIn, actor: User = Depends(authenticated),
            controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.run_pca(study_id, data, actor)


@chemistry_router.get("/studies/{study_id}/pca/{analysis_id}")
def get_pca(study_id: str, analysis_id: str, actor: User = Depends(authenticated),
            controller: ChemistryController = Depends(get_chemistry_controller)):
    return controller.get_pca(study_id, analysis_id, actor)


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
