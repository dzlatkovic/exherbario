"""Add deposition drafts, frozen versions, files, and public notices."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def _version_key():
    return (
        sa.Column("deposition_id", sa.String(50), primary_key=True),
        sa.Column("version", sa.Integer(), primary_key=True, autoincrement=False),
        sa.ForeignKeyConstraint(
            ["deposition_id", "version"], ["deposition_version.deposition_id", "deposition_version.number"],
        ),
    )


def upgrade():
    op.create_table(
        "deposition",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("institution", sa.String(40), nullable=False),
        sa.Column("accession", sa.String(50), nullable=False),
        sa.Column("owner_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("draft", sa.JSON(none_as_null=True)),
        sa.Column("draft_revision", sa.String(50)),
        sa.Column("latest_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("institution", "accession", name="uq_deposition_accession"),
    )
    op.create_table(
        "deposition_version",
        sa.Column("deposition_id", sa.String(50), sa.ForeignKey("deposition.id"), primary_key=True),
        sa.Column("number", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("draft_revision", sa.String(50), nullable=False),
        sa.Column("published_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("snapshot_sha256", sa.String(64), nullable=False),
        sa.UniqueConstraint("deposition_id", "draft_revision", name="uq_deposition_published_draft"),
    )
    op.create_table(
        "deposition_file", *_version_key(),
        sa.Column("profile_id", sa.String(50), primary_key=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
    )
    op.create_table(
        "deposition_article", *_version_key(),
        sa.Column("doi", sa.String(200), primary_key=True),
        sa.Column("linked_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "deposition_withdrawal", *_version_key(),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("withdrawn_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    depositions = sa.table("deposition", sa.column("id"))
    if op.get_bind().scalar(sa.select(depositions.c.id).limit(1)):
        raise RuntimeError("Downgrade would remove deposition drafts or published records. Restore a verified snapshot.")
    for table in ("deposition_withdrawal", "deposition_article", "deposition_file", "deposition_version", "deposition"):
        op.drop_table(table)
