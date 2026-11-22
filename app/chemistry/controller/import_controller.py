"""HTTP responses for spreadsheet imports and their templates."""

from fastapi import UploadFile

from app.chemistry.schemas.import_schemas import AssignmentIn, RowReviewIn
from app.chemistry.services.imports import ImportService, review_summary
from app.users.models import User

from .chemistry_controller import _profile_summary


def import_summary(record):
    return {
        "id": record.id, "study_id": record.study_id, "status": record.status, "source_name": record.source_name,
        "source_kind": record.source_kind, "source_sha256": record.source_sha256, "created_at": record.created_at,
        "confirmed_at": record.confirmed_at, "assignment": record.assignment,
    }


def _sheets(sheets):
    return [{"name": name, "rows": rows} for name, rows in sheets.items()]


class ImportController:
    def __init__(self, service: ImportService):
        self.service = service

    def create(self, study_id: str, file: UploadFile, actor: User):
        record, sheets = self.service.create(study_id, file.file, file.filename, actor)
        return {**import_summary(record), "sheets": _sheets({name: rows[:20] for name, rows in sheets.items()})}

    def list_for_study(self, study_id: str, actor: User):
        return [import_summary(record) for record in self.service.list_for_study(study_id, actor)]

    def get(self, import_id: str, actor: User):
        record, sheets = self.service.sheet_preview(import_id, actor)
        _, preview = self.service.preview(import_id, actor)
        return {**import_summary(record), "sheets": _sheets(sheets), "preview": preview,
                "review": review_summary(record.review)}

    def assign(self, import_id: str, data: AssignmentIn, actor: User):
        record, preview = self.service.assign(import_id, data, actor)
        return {**import_summary(record), "preview": preview, "review": review_summary(record.review)}

    def match(self, import_id: str, actor: User, limit: int = 25, retry_unmatched: bool = False):
        return self.service.match_pending(import_id, actor, limit, retry_unmatched)

    def review_row(self, import_id: str, row: int, data: RowReviewIn, actor: User):
        return self.service.review_row(import_id, row, data, actor)

    def confirm(self, import_id: str, actor: User):
        return {"profiles": [_profile_summary(profile) for profile in self.service.confirm(import_id, actor)]}

    def list_templates(self, actor: User):
        return [{"id": template.id, "name": template.name, "created_at": template.created_at,
                 "layout": template.layout} for template in self.service.list_templates(actor)]

    def apply_template(self, import_id: str, template_id: str, sheet: str | None, actor: User):
        return self.service.apply_template(import_id, template_id, sheet, actor)
