"""Remove saved PCA analyses; HERBAR exports analysis-ready CSV instead."""

from alembic import op
import sqlalchemy as sa

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().scalar(sa.select(sa.literal(1)).select_from(sa.table("chemistry_pca")).limit(1)):
        raise RuntimeError("Saved PCA analyses exist. Export them first with "
                           "`python -m app.db.export_pca <directory> --remove-exported`, then upgrade again.")
    op.drop_table("chemistry_pca")


def downgrade():
    op.create_table(
        "chemistry_pca",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("study_id", sa.String(50), nullable=False),
        sa.Column("created_by", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("profile_ids", sa.JSON(), nullable=False),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["study_id"], ["chemistry_study.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
