"""Add holding and attribution metadata while keeping existing voucher IDs."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

HOLDING_COLUMNS = {
    "holding_type": sa.String(8),
    "holding_institution": sa.String(120),
    "collection": sa.String(120),
    "accession": sa.String(100),
    "verbatim_label": sa.Text(),
    "collector_name": sa.String(200),
    "verifier_name": sa.String(200),
    "determiner_name": sa.String(200),
    "determination_date": sa.Date(),
}


def upgrade():
    with op.batch_alter_table("specimen") as batch:
        batch.alter_column("reg_no", existing_type=sa.String(10), nullable=True)
        for name, kind in HOLDING_COLUMNS.items():
            batch.add_column(sa.Column(name, kind))
        batch.create_unique_constraint("uq_specimen_holding_accession", ["holding_institution", "collection", "accession"])
    op.add_column("revision", sa.Column("prev_determiner_name", sa.String(200)))
    op.add_column("revision", sa.Column("prev_determination_date", sa.Date()))


def downgrade():
    specimens = sa.table("specimen", sa.column("reg_no"))
    if op.get_bind().scalar(sa.select(sa.literal(1)).where(specimens.c.reg_no.is_(None)).limit(1)):
        raise RuntimeError("Downgrade requires a pre-upgrade snapshot when vouchers lack legacy registration numbers.")
    op.drop_column("revision", "prev_determination_date")
    op.drop_column("revision", "prev_determiner_name")
    with op.batch_alter_table("specimen") as batch:
        batch.drop_constraint("uq_specimen_holding_accession", type_="unique")
        for name in HOLDING_COLUMNS:
            batch.drop_column(name)
        batch.alter_column("reg_no", existing_type=sa.String(10), nullable=False)
