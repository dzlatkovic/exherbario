"""Register deposition institutions and record dataset DOIs for frozen versions."""

import json
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "institution",
        sa.Column("code", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("index_herbariorum_code", sa.String(20), unique=True),
        sa.Column("ror_id", sa.String(9), unique=True),
        sa.Column("registered_by", sa.String(50), sa.ForeignKey("users.user_id")),
        sa.Column("registered_at", sa.DateTime()),
    )
    op.create_table(
        "deposition_doi",
        sa.Column("deposition_id", sa.String(50), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("doi", sa.String(200), nullable=False, unique=True),
        sa.Column("agency", sa.String(20), nullable=False),
        sa.Column("record_url", sa.String(500)),
        sa.Column("registered_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
        ),
    )
    _register_existing_institutions()


def _register_existing_institutions():
    """Keep existing accession namespaces valid, named as their latest frozen version or draft names them."""
    connection = op.get_bind()
    depositions = sa.table("deposition", sa.column("id"), sa.column("institution"), sa.column("draft"),
                           sa.column("latest_version"))
    versions = sa.table("deposition_version", sa.column("deposition_id"), sa.column("number"),
                        sa.column("snapshot"))
    institutions = sa.table("institution", sa.column("code"), sa.column("name"), sa.column("registered_at"))
    names = {}
    for deposition_id, code, draft, latest in connection.execute(sa.select(
            depositions.c.id, depositions.c.institution, depositions.c.draft, depositions.c.latest_version)):
        snapshot = connection.scalar(sa.select(versions.c.snapshot).where(
            versions.c.deposition_id == deposition_id, versions.c.number == latest)) if latest else None
        name = _json(snapshot).get("institution_name") or _json(draft).get("institution_name")
        names[code] = names.get(code) or name or code
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for code, name in sorted(names.items()):
        connection.execute(institutions.insert().values(code=code, name=name[:200], registered_at=now))


def _json(value):
    if isinstance(value, str):
        value = json.loads(value)
    return value if isinstance(value, dict) else {}


def downgrade():
    dois = sa.table("deposition_doi", sa.column("doi"))
    if op.get_bind().scalar(sa.select(dois.c.doi).limit(1)):
        raise RuntimeError("Downgrade would remove registered dataset DOIs. Restore a verified snapshot.")
    op.drop_table("deposition_doi")
    op.drop_table("institution")
