from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.users.controller import JWTBearer
from app.users.models import User

from .schemas import ArticleLink, CreateDeposition, EditDraft, PublishDraft, WithdrawVersion
from .services import DepositionService


router = APIRouter(prefix="/api/depositions", tags=["Depositions"])
researcher = JWTBearer()
curator = JWTBearer("super_user")


def get_service(db: Session = Depends(get_db)):
    return DepositionService(db)


@router.post("", status_code=201)
def create_deposition(data: CreateDeposition, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.create(data, actor)


@router.get("/{deposition_id}/draft")
def get_draft(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.get_draft(deposition_id, actor)


@router.put("/{deposition_id}/draft")
def edit_draft(deposition_id: str, data: EditDraft, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.edit(deposition_id, data, actor)


@router.get("/{deposition_id}/draft/preview")
def preview_draft(deposition_id: str, actor: User = Depends(researcher), service=Depends(get_service)):
    return service.preview(deposition_id, actor)


@router.post("/{deposition_id}/publish")
def publish_draft(deposition_id: str, data: PublishDraft, actor: User = Depends(curator), service=Depends(get_service)):
    return service.publish(deposition_id, data, actor)


@router.put("/{deposition_id}/versions/{number}/article-doi")
def link_article(deposition_id: str, data: ArticleLink, number: int = Path(ge=1, le=2_147_483_647),
                 actor: User = Depends(curator), service=Depends(get_service)):
    return service.link_article(deposition_id, number, data.doi, actor)


@router.post("/{deposition_id}/versions/{number}/withdraw")
def withdraw_version(deposition_id: str, data: WithdrawVersion, number: int = Path(ge=1, le=2_147_483_647),
                     actor: User = Depends(curator), service=Depends(get_service)):
    return service.withdraw(deposition_id, number, data.reason, actor)


@router.get("/public/{institution}/{accession}/versions/{number}")
def public_version(institution: str, accession: str, number: int = Path(ge=1, le=2_147_483_647),
                   service=Depends(get_service)):
    status, metadata = service.public_version(institution, accession, number)
    return JSONResponse(metadata, status_code=status)


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
