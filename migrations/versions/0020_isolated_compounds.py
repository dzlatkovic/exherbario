"""Co-injection and isolated-compound evidence, and structures supplied by authors."""

from alembic import op
import sqlalchemy as sa

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None

EVIDENCE = (
    ("standard_source", sa.String(20)), ("standard_reference", sa.String(300)),
    ("nmr_experiments", sa.String(200)), ("nmr_solvent", sa.String(100)), ("purity_percent", sa.Double()),
    ("novelty", sa.String(10)), ("literature_doi", sa.String(200)), ("optical_rotation", sa.String(200)),
    ("ecd", sa.String(300)), ("ccdc", sa.String(20)), ("configuration_type", sa.String(20)),
    ("configuration", sa.String(300)), ("data_accessions", sa.String(500)), ("structure_id", sa.String(50)),
)
CORRECTION = (("old_structure_id", sa.String(50)), ("new_structure_id", sa.String(50)))


def upgrade():
    op.create_table(
        "chemistry_structure",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("inchikey", sa.String(27), nullable=False, unique=True),
        sa.Column("inchi", sa.Text(), nullable=False),
        sa.Column("smiles", sa.Text(), nullable=False),
        sa.Column("molecular_formula", sa.String(100), nullable=False),
        sa.Column("monoisotopic_mass", sa.Double(), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("submitted_by", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
    )
    with op.batch_alter_table("chemistry_measurement") as batch:
        batch.alter_column("id_basis", existing_type=sa.String(60), type_=sa.String(120))
        for name, kind in EVIDENCE:
            batch.add_column(sa.Column(name, kind))
        batch.create_foreign_key("fk_chemistry_measurement_structure", "chemistry_structure", ["structure_id"], ["id"])
    with op.batch_alter_table("chemistry_measurement_correction") as batch:
        for name, kind in CORRECTION:
            batch.add_column(sa.Column(name, kind))
        batch.create_foreign_key("fk_correction_old_structure", "chemistry_structure", ["old_structure_id"], ["id"])
        batch.create_foreign_key("fk_correction_new_structure", "chemistry_structure", ["new_structure_id"], ["id"])


def downgrade():
    connection = op.get_bind()
    if connection.scalar(sa.select(sa.literal(1)).select_from(sa.table("chemistry_structure")).limit(1)):
        raise RuntimeError("Downgrade would remove author-supplied structures. Restore a verified pre-upgrade snapshot.")
    values = sa.table("chemistry_measurement", *(sa.column(name) for name, _ in EVIDENCE), sa.column("id_basis"))
    if connection.scalar(sa.select(sa.literal(1)).where(sa.or_(
            *(values.c[name].is_not(None) for name, _ in EVIDENCE), sa.func.length(values.c.id_basis) > 60)).limit(1)):
        raise RuntimeError("Downgrade would remove recorded identification evidence. Restore a verified pre-upgrade snapshot.")
    with op.batch_alter_table("chemistry_measurement_correction") as batch:
        batch.drop_constraint("fk_correction_new_structure", type_="foreignkey")
        batch.drop_constraint("fk_correction_old_structure", type_="foreignkey")
        for name, _ in reversed(CORRECTION):
            batch.drop_column(name)
    with op.batch_alter_table("chemistry_measurement") as batch:
        batch.drop_constraint("fk_chemistry_measurement_structure", type_="foreignkey")
        for name, _ in reversed(EVIDENCE):
            batch.drop_column(name)
        batch.alter_column("id_basis", existing_type=sa.String(120), type_=sa.String(60))
    op.drop_table("chemistry_structure")
