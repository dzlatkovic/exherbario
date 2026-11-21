"""Cache external registry answers and record values curators accept from them."""

from alembic import op
import sqlalchemy as sa

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_lookup_cache",
        sa.Column("provider", sa.String(40), primary_key=True),
        sa.Column("key_digest", sa.String(64), primary_key=True),
        sa.Column("lookup_key", sa.Text(), nullable=False),
        sa.Column("found", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "external_import",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_id", sa.String(300), nullable=False),
        sa.Column("record_type", sa.String(20), nullable=False),
        sa.Column("record_id", sa.String(50), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime()),
        sa.Column("confirmed_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_external_import_record", "external_import", ["record_type", "record_id"])


def downgrade():
    # The cache can be rebuilt; the import log cannot, so refuse to drop it while it holds entries.
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM external_import LIMIT 1")).first():
        raise RuntimeError("external_import holds curator-confirmed provenance. Export it before downgrading.")
    op.drop_index("ix_external_import_record", table_name="external_import")
    op.drop_table("external_import")
    op.drop_table("external_lookup_cache")
