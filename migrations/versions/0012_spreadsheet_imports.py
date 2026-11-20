"""Add spreadsheet imports, saved column-assignment templates and the import link on profiles."""

from alembic import op
import sqlalchemy as sa

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chemistry_import",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("study_id", sa.String(50), sa.ForeignKey("chemistry_study.id"), nullable=False),
        sa.Column("owner_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime()),
        sa.Column("source_name", sa.String(200), nullable=False),
        sa.Column("source_kind", sa.String(10), nullable=False),
        sa.Column("source_path", sa.String(150), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("assignment", sa.JSON()),
        sa.Column("review", sa.JSON()),
    )
    op.create_table(
        "chemistry_import_template",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("owner_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("layout", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("owner_id", "name", name="uq_chemistry_import_template_name"),
    )
    with op.batch_alter_table("chemistry_profile") as batch:
        batch.add_column(sa.Column("import_id", sa.String(50)))
        batch.add_column(sa.Column("import_column", sa.String(200)))
        batch.create_foreign_key("fk_chemistry_profile_import", "chemistry_import", ["import_id"], ["id"])


def downgrade():
    connection = op.get_bind()
    for table in ("chemistry_import", "chemistry_import_template"):
        if connection.scalar(sa.select(sa.literal(1)).select_from(sa.table(table)).limit(1)):
            raise RuntimeError(f"Downgrade would remove {table} records. Restore a verified pre-upgrade snapshot.")
    with op.batch_alter_table("chemistry_profile") as batch:
        batch.drop_constraint("fk_chemistry_profile_import", type_="foreignkey")
        batch.drop_column("import_column")
        batch.drop_column("import_id")
    op.drop_table("chemistry_import_template")
    op.drop_table("chemistry_import")
