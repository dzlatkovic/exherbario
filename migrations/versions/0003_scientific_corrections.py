"""Store scientific corrections alongside the existing determination history."""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scientific_correction",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("specimen_id", sa.String(50), sa.ForeignKey("specimen.specimen_id"), index=True),
        sa.Column("field_loc_id", sa.String(50), sa.ForeignKey("field_loc.field_loc_id"), index=True),
        sa.Column("actor_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=False),
        sa.Column("new_values", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "(specimen_id IS NOT NULL AND field_loc_id IS NULL) OR "
            "(specimen_id IS NULL AND field_loc_id IS NOT NULL)",
            name="scientific_correction_one_target",
        ),
        mysql_engine="InnoDB",
    )


def downgrade():
    op.drop_table("scientific_correction")
