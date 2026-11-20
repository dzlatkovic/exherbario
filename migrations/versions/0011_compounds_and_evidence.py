"""Add the PubChem compound registry, author aliases, compound corrections and identification evidence."""

from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

EVIDENCE = (
    ("compound_match", sa.String(30)), ("rt_min", sa.Double()), ("id_basis", sa.String(60)),
    ("id_level", sa.Integer()), ("qualifier", sa.String(10)), ("sd", sa.Double()), ("n", sa.Integer()),
    ("ri_exp", sa.Double()), ("ri_ref", sa.Double()), ("ri_ref_source", sa.String(200)),
    ("ri_ref_polarity", sa.String(12)), ("library_match", sa.String(200)), ("library_score", sa.Double()),
    ("mz_obs", sa.Double()), ("adduct", sa.String(40)), ("mass_error_ppm", sa.Double()),
    ("msms_match", sa.String(200)),
)
ADDED = {
    "chemistry_profile": (("technique", sa.String(20)), ("run_metadata", sa.JSON())),
    "chemistry_preparation": (("plant_material_mass_g", sa.Double()), ("method_parameters", sa.String(1000)),
                              ("yield_percent", sa.Double())),
    "chemistry_measurement": (("cid", sa.Integer()), *EVIDENCE),
}


def upgrade():
    op.create_table(
        "compound",
        sa.Column("cid", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("iupac_name", sa.Text()),
        sa.Column("molecular_formula", sa.String(100)),
        sa.Column("monoisotopic_mass", sa.Double()),
        sa.Column("inchi", sa.Text()),
        sa.Column("inchikey", sa.String(27)),
        sa.Column("smiles", sa.Text()),
        sa.Column("synonyms", sa.JSON(), nullable=False),
        sa.Column("cas_numbers", sa.JSON(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_compound_inchikey", "compound", ["inchikey"])
    op.create_table(
        "compound_name",
        sa.Column("cid", sa.Integer(), sa.ForeignKey("compound.cid"), primary_key=True, autoincrement=False),
        sa.Column("name_key", sa.String(300), primary_key=True),
        sa.Column("is_title", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_compound_name_key", "compound_name", ["name_key"])
    op.create_table(
        "compound_alias",
        sa.Column("owner_id", sa.String(50), sa.ForeignKey("users.user_id"), primary_key=True),
        sa.Column("name_key", sa.String(160), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("cid", sa.Integer(), sa.ForeignKey("compound.cid"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    for table, columns in ADDED.items():
        with op.batch_alter_table(table) as batch:
            for name, kind in columns:
                batch.add_column(sa.Column(name, kind))
            if table == "chemistry_measurement":
                batch.create_foreign_key("fk_chemistry_measurement_compound", "compound", ["cid"], ["cid"])
    op.create_table(
        "chemistry_measurement_correction",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("profile_id", sa.String(50), nullable=False),
        sa.Column("feature", sa.String(160), nullable=False),
        sa.Column("old_cid", sa.Integer()),
        sa.Column("new_cid", sa.Integer()),
        sa.Column("actor_id", sa.String(50), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("corrected_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id", "feature"],
                                ["chemistry_measurement.profile_id", "chemistry_measurement.feature"]),
    )


def downgrade():
    connection = op.get_bind()
    for table in ("compound", "compound_name", "compound_alias", "chemistry_measurement_correction"):
        if connection.scalar(sa.select(sa.literal(1)).select_from(sa.table(table)).limit(1)):
            raise RuntimeError(f"Downgrade would remove {table} records. Restore a verified pre-upgrade snapshot.")
    for table, columns in ADDED.items():
        values = sa.table(table, *(sa.column(name) for name, _ in columns))
        if connection.scalar(sa.select(sa.literal(1)).where(
                sa.or_(*(values.c[name].is_not(None) for name, _ in columns))).limit(1)):
            raise RuntimeError(f"Downgrade would remove recorded {table} details. Restore a verified pre-upgrade snapshot.")
    op.drop_table("chemistry_measurement_correction")
    for table, columns in ADDED.items():
        with op.batch_alter_table(table) as batch:
            if table == "chemistry_measurement":
                batch.drop_constraint("fk_chemistry_measurement_compound", type_="foreignkey")
            for name, _ in reversed(columns):
                batch.drop_column(name)
    op.drop_table("compound_alias")
    op.drop_index("ix_compound_name_key", "compound_name")
    op.drop_table("compound_name")
    op.drop_index("ix_compound_inchikey", "compound")
    op.drop_table("compound")
