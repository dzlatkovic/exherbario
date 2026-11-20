"""Link lab samples to several vouchers with roles and record structured sample provenance."""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

PLANT_PARTS = ("leaf", "flower", "inflorescence", "aerial parts", "stem", "root", "rhizome", "bark",
               "fruit", "seed", "whole plant", "other")
# Exact matches, ignoring case and surrounding spaces. Anything else becomes "other" with its text kept.
PLANT_PART_SYNONYMS = {
    **{part: part for part in PLANT_PARTS},
    "leaves": "leaf", "flowers": "flower", "inflorescences": "inflorescence", "aerial part": "aerial parts",
    "stems": "stem", "roots": "root", "rhizomes": "rhizome", "fruits": "fruit", "seeds": "seed",
}
LEGACY_ROLES = ("sampled_from_voucher", "collected_alongside")
ADDED_COLUMNS = (
    ("plant_part_note", sa.String(200)),
    ("material_state", sa.String(20)),
    ("collection_date", sa.Date()),
    ("phenological_stage", sa.String(100)),
    ("drying_notes", sa.String(1000)),
    ("storage_notes", sa.String(1000)),
    ("collection_notes", sa.String(200)),
)
# Fields with no place in the previous schema. Downgrade refuses to discard them.
NEW_ONLY = ("material_state", "collection_date", "phenological_stage", "site_specimen_id", "field_loc_id",
            "drying_notes", "storage_notes")


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade():
    op.create_table(
        "chemistry_sample_voucher",
        sa.Column("sample_id", sa.String(50), sa.ForeignKey("chemistry_sample.id"), primary_key=True),
        sa.Column("specimen_id", sa.String(50), sa.ForeignKey("specimen.specimen_id"), primary_key=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.Column("taxon_id_at_link", sa.String(50)),
        sa.Column("taxon_name_at_link", sa.String(255)),
        sa.Column("name_at_link", sa.String(200)),
        sa.Column("determination_date_at_link", sa.Date()),
        sa.Column("determination_recorded", sa.String(20), nullable=False),
    )
    with op.batch_alter_table("chemistry_sample") as batch:
        for name, kind in ADDED_COLUMNS:
            batch.add_column(sa.Column(name, kind))
        batch.add_column(sa.Column("site_specimen_id", sa.String(50)))
        batch.add_column(sa.Column("field_loc_id", sa.String(50)))
        batch.create_foreign_key("fk_chemistry_sample_site_specimen", "specimen",
                                 ["site_specimen_id"], ["specimen_id"])
        batch.create_foreign_key("fk_chemistry_sample_field_loc", "field_loc", ["field_loc_id"], ["field_loc_id"])
    _convert_samples()
    with op.batch_alter_table("chemistry_sample") as batch:
        batch.drop_column("specimen_id")
        batch.drop_column("voucher_relationship")
        batch.drop_column("collection_event")


def _convert_samples():
    connection = op.get_bind()
    samples = sa.table("chemistry_sample", sa.column("id"), sa.column("specimen_id"), sa.column("plant_part"),
                       sa.column("plant_part_note"), sa.column("collection_event"),
                       sa.column("collection_notes"), sa.column("voucher_relationship"))
    specimens = sa.table("specimen", sa.column("specimen_id"), sa.column("taxon_id"), sa.column("subnomen"),
                         sa.column("determination_date"))
    taxa = sa.table("taxonomy", sa.column("taxon_id"), sa.column("taxon_name"))
    links = sa.table("chemistry_sample_voucher", *(sa.column(name) for name in (
        "sample_id", "specimen_id", "role", "linked_at", "taxon_id_at_link", "taxon_name_at_link",
        "name_at_link", "determination_date_at_link", "determination_recorded")))
    now = _now()
    rows = connection.execute(
        sa.select(samples.c.id, samples.c.specimen_id, samples.c.plant_part, samples.c.collection_event,
                  samples.c.voucher_relationship, specimens.c.taxon_id, specimens.c.subnomen,
                  specimens.c.determination_date, taxa.c.taxon_name)
        .join(specimens, specimens.c.specimen_id == samples.c.specimen_id)
        .outerjoin(taxa, taxa.c.taxon_id == specimens.c.taxon_id)
        .order_by(samples.c.id)
    ).all()
    for row in rows:
        text = (row.plant_part or "").strip()
        part = PLANT_PART_SYNONYMS.get(text.casefold())
        connection.execute(samples.update().where(samples.c.id == row.id).values(
            plant_part=part or "other", plant_part_note=None if part else text[:200] or None,
            collection_notes=row.collection_event,
        ))
        connection.execute(links.insert().values(
            sample_id=row.id, specimen_id=row.specimen_id, role=row.voucher_relationship, linked_at=now,
            taxon_id_at_link=row.taxon_id, taxon_name_at_link=row.taxon_name, name_at_link=row.subnomen,
            determination_date_at_link=row.determination_date, determination_recorded="at_migration",
        ))


def downgrade():
    connection = op.get_bind()
    samples = sa.table("chemistry_sample", *(sa.column(name) for name in (
        "id", "plant_part", "plant_part_note", "collection_notes", *NEW_ONLY)))
    links = sa.table("chemistry_sample_voucher", sa.column("sample_id"), sa.column("specimen_id"),
                     sa.column("role"))
    counts = sa.select(links.c.sample_id, sa.func.count().label("n")).group_by(links.c.sample_id).subquery()
    if connection.scalar(sa.select(sa.literal(1)).select_from(samples).outerjoin(
            counts, counts.c.sample_id == samples.c.id).where(sa.func.coalesce(counts.c.n, 0) != 1).limit(1)):
        raise RuntimeError("Downgrade needs exactly one voucher per lab sample. Restore a verified pre-upgrade snapshot.")
    if connection.scalar(sa.select(sa.literal(1)).where(links.c.role.not_in(LEGACY_ROLES)).limit(1)):
        raise RuntimeError("Downgrade would remove voucher roles. Restore a verified pre-upgrade snapshot.")
    if connection.scalar(sa.select(sa.literal(1)).where(sa.or_(
            *(samples.c[name].is_not(None) for name in NEW_ONLY),
            sa.and_(samples.c.plant_part_note.is_not(None), samples.c.plant_part != "other"))).limit(1)):
        raise RuntimeError("Downgrade would remove recorded sample provenance. Restore a verified pre-upgrade snapshot.")

    with op.batch_alter_table("chemistry_sample") as batch:
        batch.add_column(sa.Column("specimen_id", sa.String(50)))
        batch.add_column(sa.Column("collection_event", sa.String(200)))
        batch.add_column(sa.Column("voucher_relationship", sa.String(30)))
    legacy = sa.table("chemistry_sample", sa.column("id"), sa.column("specimen_id"), sa.column("plant_part"),
                      sa.column("collection_event"), sa.column("voucher_relationship"))
    for sample_id, part, note, notes, specimen_id, role in connection.execute(
            sa.select(samples.c.id, samples.c.plant_part, samples.c.plant_part_note, samples.c.collection_notes,
                      links.c.specimen_id, links.c.role).join(links, links.c.sample_id == samples.c.id)).all():
        connection.execute(legacy.update().where(legacy.c.id == sample_id).values(
            specimen_id=specimen_id, voucher_relationship=role,
            plant_part=(note or part)[:100] if part == "other" else part,
            collection_event=notes or "Not recorded",
        ))
    with op.batch_alter_table("chemistry_sample") as batch:
        batch.alter_column("specimen_id", existing_type=sa.String(50), nullable=False)
        batch.alter_column("collection_event", existing_type=sa.String(200), nullable=False)
        batch.alter_column("voucher_relationship", existing_type=sa.String(30), nullable=False)
        batch.create_foreign_key("fk_chemistry_sample_specimen", "specimen", ["specimen_id"], ["specimen_id"])
        batch.drop_constraint("fk_chemistry_sample_site_specimen", type_="foreignkey")
        batch.drop_constraint("fk_chemistry_sample_field_loc", type_="foreignkey")
        for name in ("site_specimen_id", "field_loc_id", *(name for name, _ in reversed(ADDED_COLUMNS))):
            batch.drop_column(name)
    op.drop_table("chemistry_sample_voucher")
