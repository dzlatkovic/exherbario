from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.users.controller import JWTBearer
from app.users.models import User

from .schemas import ArticleLink, CreateDeposition, DatasetDOI, EditDraft, PublishDraft, RegisterInstitution, WithdrawVersion
from .services import DepositionService


router = APIRouter(prefix="/api/depositions", tags=["Depositions"])
institution_router = APIRouter(prefix="/api/institutions", tags=["Depositions"])
researcher = JWTBearer()
curator = JWTBearer("super_user")


def get_service(db: Session = Depends(get_db)):
    return DepositionService(db)


@institution_router.get("")
def list_institutions(service=Depends(get_service)):
    return service.list_institutions()


@institution_router.get("/lookup")
def lookup_institutions(q: str = Query(..., min_length=2, max_length=200), _actor: User = Depends(curator),
                        service=Depends(get_service)):
    """Search ROR and Index Herbariorum to fill the registration form. Each result says if it is already
    registered here (`registered_code`); `errors` names a registry that could not be reached. Nothing is saved:
    register with the chosen values and their `sources`."""
    return service.lookup_institutions(q)


@institution_router.post("", status_code=201)
def register_institution(data: RegisterInstitution, actor: User = Depends(curator), service=Depends(get_service)):
    return service.register_institution(data, actor)


@router.post("", status_code=201)
def create_deposition(data: CreateDeposition, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.create(data, actor)


@router.get("")
def list_depositions(actor: User = Depends(researcher), service=Depends(get_service)):
    """The signed-in account's depositions and drafts."""
    return service.list_for_owner(actor)


@router.get("/public")
def list_public_depositions(q: str = Query("", max_length=200), page: int = Query(1, ge=1, le=1_000_000),
                            size: int = Query(20, ge=1, le=100), service=Depends(get_service)):
    """Published depositions at their latest version. Drafts are never listed."""
    return service.list_public(q=q, page=page, size=size)


@router.get("/review")
def review_queue(actor: User = Depends(curator), service=Depends(get_service)):
    """Drafts their owners submitted for curator review, oldest first."""
    return service.list_review()


@router.post("/{deposition_id}/submission")
def submit_for_review(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.submit(deposition_id, actor)


@router.delete("/{deposition_id}/submission")
def withdraw_submission(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.withdraw_submission(deposition_id, actor)


@router.get("/{deposition_id}/draft")
def get_draft(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.get_draft(deposition_id, actor)


@router.delete("/{deposition_id}/draft", status_code=204)
def discard_draft(deposition_id: str, expected_revision: str = Query(min_length=1, max_length=50),
                  actor: User = Depends(researcher), service=Depends(get_service)):
    service.discard_draft(deposition_id, expected_revision, actor)


@router.put("/{deposition_id}/draft")
def edit_draft(deposition_id: str, data: EditDraft, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.edit(deposition_id, data, actor)


@router.get("/{deposition_id}/draft/preview")
def preview_draft(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.preview(deposition_id, actor)


@router.get("/{deposition_id}/draft/inputs")
def draft_inputs(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.draft_inputs(deposition_id, actor)


@router.post("/{deposition_id}/publish")
def publish_draft(deposition_id: str, data: PublishDraft, actor: User = Depends(curator), service=Depends(get_service)):
    return service.publish(deposition_id, data, actor)


@router.put("/{deposition_id}/versions/{number}/article-doi")
def link_article(deposition_id: str, data: ArticleLink, number: int = Path(ge=1, le=2_147_483_647),
                 actor: User = Depends(curator), service=Depends(get_service)):
    return service.link_article(deposition_id, number, data.doi, actor)


@router.put("/{deposition_id}/versions/{number}/doi")
def register_dataset_doi(deposition_id: str, data: DatasetDOI, number: int = Path(ge=1, le=2_147_483_647),
                         actor: User = Depends(curator), service=Depends(get_service)):
    return service.register_doi(deposition_id, number, data, actor)


@router.post("/{deposition_id}/versions/{number}/withdraw")
def withdraw_version(deposition_id: str, data: WithdrawVersion, number: int = Path(ge=1, le=2_147_483_647),
                     actor: User = Depends(curator), service=Depends(get_service)):
    return service.withdraw(deposition_id, number, data.reason, actor)


@router.get("/public/{institution}/{accession}/versions/{number}")
def public_version(institution: str, accession: str, number: int = Path(ge=1, le=2_147_483_647),
                   service=Depends(get_service)):
    status, metadata = service.public_version(institution, accession, number)
    return JSONResponse(metadata, status_code=status)


@router.get("/public/{institution}/{accession}/versions/{number}/datacite.json")
def public_datacite(institution: str, accession: str, number: int = Path(ge=1, le=2_147_483_647),
                    service=Depends(get_service)):
    return service.public_datacite(institution, accession, number)


@router.get("/public/{institution}/{accession}/versions/{number}/archive.zip", response_class=Response,
            responses={200: {"content": {"application/zip": {}}}})
def download_archive(institution: str, accession: str, number: int = Path(ge=1, le=2_147_483_647),
                     service=Depends(get_service)):
    content, digest, filename = service.public_archive(institution, accession, number)
    return Response(content, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Content-Type-Options": "nosniff",
        "X-HERBAR-Snapshot-SHA256": digest,
    })


@router.get("/public/{institution}/{accession}/versions/{number}/files/{profile_id}",
            response_class=Response, responses={200: {"content": {"text/csv": {}}}})
def public_file(institution: str, accession: str, profile_id: str, number: int = Path(ge=1, le=2_147_483_647),
                service=Depends(get_service)):
    content, metadata = service.public_file(institution, accession, number, profile_id)
    return Response(content, media_type="text/csv", headers={
        "Content-Disposition": 'attachment; filename="profile-source.csv"',
        "X-Content-Type-Options": "nosniff",
        "X-HERBAR-SHA256": metadata["sha256"],
        "X-HERBAR-Source-Fidelity": metadata["source_fidelity"],
    })
