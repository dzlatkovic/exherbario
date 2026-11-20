"""Default vouchers and photos to private pending curator review."""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("specimen", sa.Column("is_public", sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
    op.add_column("specimen", sa.Column("public_location", sa.String(8), nullable=False,
                                       server_default="withheld"))
    op.add_column("image", sa.Column("is_public", sa.Boolean(), nullable=False,
                                    server_default=sa.false()))


def downgrade():
    op.drop_column("image", "is_public")
    op.drop_column("specimen", "public_location")
    op.drop_column("specimen", "is_public")
