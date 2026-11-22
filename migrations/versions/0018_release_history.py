"""Remember whether a record has been released."""

from alembic import op
import sqlalchemy as sa

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

TABLES = ("specimen", "image", "chemistry_study", "chemistry_profile")


def upgrade():
    for table in TABLES:
        op.add_column(table, sa.Column("ever_public", sa.Boolean(), nullable=False, server_default=sa.false()))
        op.execute(sa.text(f"UPDATE {table} SET ever_public = 1 WHERE is_public = 1"))
    op.execute(sa.text(
        "UPDATE chemistry_profile SET ever_public = 1 WHERE id IN (SELECT profile_id FROM deposition_file)"
    ))
    op.execute(sa.text(
        "UPDATE chemistry_study SET ever_public = 1 WHERE id IN ("
        "SELECT s.study_id FROM chemistry_profile p JOIN chemistry_preparation b ON b.id = p.preparation_id "
        "JOIN chemistry_sample s ON s.id = b.sample_id "
        "JOIN deposition_file f ON f.profile_id = p.id)"
    ))
    op.execute(sa.text(
        "UPDATE specimen SET ever_public = 1 WHERE specimen_id IN ("
        "SELECT json_extract(v.value, '$.id') FROM deposition_version, json_each(snapshot, '$.vouchers') v "
        "UNION SELECT json_extract(p.value, '$.voucher.id') "
        "FROM deposition_version, json_each(snapshot, '$.profiles') p)"
    ))


def downgrade():
    for table in reversed(TABLES):
        op.drop_column(table, "ever_public")
