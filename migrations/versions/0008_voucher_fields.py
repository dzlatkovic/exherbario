"""Widen voucher, location and taxon text fields and add collector numbers and georeference details."""

from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

# table -> column -> (previous length, new length)
WIDENED = {
    "field_loc": {"country": (20, 100), "region": (20, 150), "locality": (40, 500), "habitat": (20, 255)},
    "specimen": {"reg_no": (10, 40)},
    "taxonomy": {"taxon_name": (100, 255), "common_name": (50, 150), "authority": (30, 200)},
}
NOT_NULL = {("taxonomy", "taxon_name")}
ADDED = {
    "field_loc": {
        "coordinate_uncertainty_m": sa.Integer(),
        "geodetic_datum": sa.String(20),
        "georeference_source": sa.String(200),
    },
    "specimen": {
        "collector_number": sa.String(100),
        "verbatim_collection_date": sa.String(100),
        "type_status": sa.String(50),
    },
}


def _alter(batch, table, column, old, new):
    batch.alter_column(column, existing_type=sa.String(old), type_=sa.String(new),
                       existing_nullable=(table, column) not in NOT_NULL)


def upgrade():
    for table, columns in WIDENED.items():
        with op.batch_alter_table(table) as batch:
            for column, (old, new) in columns.items():
                _alter(batch, table, column, old, new)
            for column, kind in ADDED.get(table, {}).items():
                batch.add_column(sa.Column(column, kind))


def downgrade():
    connection = op.get_bind()
    for table, columns in WIDENED.items():
        for column, (old, _) in columns.items():
            values = sa.table(table, sa.column(column))
            if connection.scalar(sa.select(sa.literal(1)).where(
                    sa.func.length(values.c[column]) > old).limit(1)):
                raise RuntimeError(f"Downgrade would truncate {table}.{column}. Restore a verified pre-upgrade snapshot.")
    for table, columns in ADDED.items():
        values = sa.table(table, *(sa.column(name) for name in columns))
        if connection.scalar(sa.select(sa.literal(1)).where(
                sa.or_(*(values.c[name].is_not(None) for name in columns))).limit(1)):
            raise RuntimeError(f"Downgrade would remove recorded {table} details. Restore a verified pre-upgrade snapshot.")
    for table, columns in WIDENED.items():
        with op.batch_alter_table(table) as batch:
            for column in ADDED.get(table, {}):
                batch.drop_column(column)
            for column, (old, new) in columns.items():
                _alter(batch, table, column, new, old)
