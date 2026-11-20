"""Curator approval for voucher and photograph publication."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy.orm import Session

from app.db import get_db, lock_for_update
from app.image.exceptions import InvalidImageFileException
from app.image.models import Image
from app.image.services import ImageService
from app.specimen.models import Specimen
from app.users.controller import JWTBearer


router = APIRouter(tags=["Visibility"], dependencies=[Depends(JWTBearer("super_user"))])


class PhotoVisibility(BaseModel):
    is_public: StrictBool

    model_config = ConfigDict(extra="forbid")


class VoucherVisibility(PhotoVisibility):
    public_location: Literal["withheld", "region"]


@router.put("/api/specimen/{specimen_id}/visibility", response_model=VoucherVisibility)
def set_voucher_visibility(specimen_id: str, state: VoucherVisibility, db: Session = Depends(get_db)):
    specimen = lock_for_update(db, db.query(Specimen).filter_by(specimen_id=specimen_id)).first()
    if specimen is None:
        raise HTTPException(404, "Specimen not found.")
    specimen.is_public = state.is_public
    specimen.public_location = state.public_location
    db.commit()
    return state


@router.put("/api/image/{image_id}/visibility", response_model=PhotoVisibility)
def set_photo_visibility(image_id: str, state: PhotoVisibility, db: Session = Depends(get_db)):
    image = lock_for_update(db, db.query(Image).filter_by(image_id=image_id)).first()
    if image is None:
        raise HTTPException(404, "Image not found.")
    if state.is_public:
        if not image.specimen_id or not image.file_path:
            raise HTTPException(409, "The photo needs a linked voucher and an original file.")
        try:
            ImageService.public_jpeg(image.file_path)
        except InvalidImageFileException as error:
            raise HTTPException(409, "A public copy could not be generated.") from error
    image.is_public = state.is_public
    db.commit()
    return state
