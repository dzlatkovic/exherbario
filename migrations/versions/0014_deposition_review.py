"""Record when a researcher submits a deposition draft for curator review."""

from alembic import op
import sqlalchemy as sa

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deposition") as table:
        table.add_column(sa.Column("submitted_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("deposition") as table:
        table.drop_column("submitted_at")
