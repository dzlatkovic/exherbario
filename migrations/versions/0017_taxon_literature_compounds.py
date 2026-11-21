"""Compounds reported in the literature for a taxon (LOTUS via Wikidata), published by a curator."""

from alembic import op
import sqlalchemy as sa

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "taxon_literature_compound",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("taxon_id", sa.String(50), sa.ForeignKey("taxonomy.taxon_id"), nullable=False),
        sa.Column("wikidata_id", sa.String(20), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("inchikey", sa.String(27)),
        sa.Column("cid", sa.Integer()),
        sa.Column("references", sa.JSON(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("taxon_id", "wikidata_id", name="uq_taxon_literature_compound"),
    )
    op.create_index("ix_taxon_literature_compound_taxon_id", "taxon_literature_compound", ["taxon_id"])


def downgrade():
    # Only a copy of provider data that a curator can publish again; dropping it loses no measurements.
    op.drop_index("ix_taxon_literature_compound_taxon_id", table_name="taxon_literature_compound")
    op.drop_table("taxon_literature_compound")
