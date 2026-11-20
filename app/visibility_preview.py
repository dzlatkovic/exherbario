"""Summarize the visibility changes migration 0004 would make."""

import json
from pathlib import Path

from sqlalchemy import func, inspect, select, text
from sqlalchemy.engine import Connection

from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.db.database import engine
from app.image.models import Image
from app.specimen.models import Specimen


def preview(connection: Connection) -> dict:
    if not inspect(connection).has_table("alembic_version"):
        raise ValueError("Visibility preview requires an Alembic-managed database at revision 0003.")
    revisions = connection.scalars(text("SELECT version_num FROM alembic_version")).all()
    if revisions != ["0003"]:
        raise ValueError("Run the visibility preview against revision 0003 before upgrading to 0004.")

    profile = Profile.__table__
    preparation = Preparation.__table__
    sample = LabSample.__table__
    study = Study.__table__
    profiles = (
        select(profile.c.id)
        .join(preparation, preparation.c.id == profile.c.preparation_id)
        .join(sample, sample.c.id == preparation.c.sample_id)
        .join(study, study.c.id == sample.c.study_id)
        .where(study.c.is_public.is_(True), profile.c.is_public.is_(True))
        .subquery()
    )
    return {
        "vouchers_withheld": connection.scalar(select(func.count(Specimen.__table__.c.specimen_id))),
        "photo_records_withheld": connection.scalar(select(func.count(Image.__table__.c.image_id))),
        "public_studies_withheld": connection.scalar(
            select(func.count(study.c.id)).where(study.c.is_public.is_(True))
        ),
        "public_profiles_withheld": connection.scalar(select(func.count()).select_from(profiles)),
    }


def main():
    try:
        database = engine.url.database
        if (engine.dialect.name == "sqlite" and database not in (None, "", ":memory:")
                and "uri" not in engine.url.query and not Path(database).is_file()):
            raise ValueError("The configured SQLite database does not exist.")
        with engine.connect() as connection:
            print(json.dumps(preview(connection), indent=2))
    except ValueError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
