"""Saved run conditions and preparation methods, reused when entering new results."""

from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chemistry_condition_preset",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("owner_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("owner_id", "kind", "name", name="uq_chemistry_condition_preset_name"),
    )


def downgrade():
    # Presets only prefill forms; recorded results keep their own copy of the conditions.
    op.drop_table("chemistry_condition_preset")
