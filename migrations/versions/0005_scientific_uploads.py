"""Track exact original bytes for new photos and chemistry sources."""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("image", sa.Column("sha256", sa.String(64)))
    op.add_column("chemistry_profile", sa.Column("source_path", sa.String(150)))
    op.add_column("chemistry_profile", sa.Column("source_sha256", sa.String(64)))


def downgrade():
    op.drop_column("chemistry_profile", "source_sha256")
    op.drop_column("chemistry_profile", "source_path")
    op.drop_column("image", "sha256")
