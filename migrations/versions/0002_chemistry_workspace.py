"""Add studies, voucher-linked profiles, and saved PCA results."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _unique_columns(table):
    return {
        tuple(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, sa.UniqueConstraint)
    } | {
        tuple(index.columns.keys()) for index in table.indexes if index.unique
    }


def _foreign_keys(table):
    return {
        (tuple(constraint.columns.keys()),
         tuple(element.target_fullname for element in constraint.elements))
        for constraint in table.foreign_key_constraints
    }


def _create_table(name, *definition):
    context = op.get_context()
    if context.as_sql or not sa.inspect(op.get_bind()).has_table(name):
        op.create_table(name, *definition, mysql_engine="InnoDB")
        return

    # MySQL commits each DDL statement. A retry can encounter tables from the first attempt.
    connection = op.get_bind()
    expected = sa.Table(name, sa.MetaData(), *definition)
    existing = sa.Table(name, sa.MetaData(), autoload_with=connection, resolve_fks=False)
    expected_keys = _foreign_keys(expected)
    actual_keys = _foreign_keys(existing)
    is_mysql = context.dialect.name == "mysql"
    if (
        set(existing.columns.keys()) != set(expected.columns.keys())
        or tuple(existing.primary_key.columns.keys()) != tuple(expected.primary_key.columns.keys())
        or _unique_columns(existing) != _unique_columns(expected)
        or (not actual_keys.issubset(expected_keys) if is_mysql else actual_keys != expected_keys)
        or any(
            existing.c[column.name].nullable != column.nullable
            or context.impl.compare_type(existing.c[column.name], column)
            for column in expected.columns
        )
    ):
        raise RuntimeError(f"Existing table {name} does not match migration 0002.")

    if is_mysql:
        engine = existing.dialect_options["mysql"].get("engine", "").lower()
        if engine == "myisam":
            quoted_name = connection.dialect.identifier_preparer.quote(name)
            op.execute(f"ALTER TABLE {quoted_name} ENGINE=InnoDB")
        elif engine != "innodb":
            raise RuntimeError(f"Existing table {name} has unsupported storage engine {engine!r}.")
        # MySQL supplies the indexes required by these foreign keys.
        for columns, targets in sorted(expected_keys - actual_keys):
            target_table = targets[0].rsplit(".", 1)[0]
            target_columns = [target.rsplit(".", 1)[1] for target in targets]
            op.create_foreign_key(
                f"fk_{name}_{columns[0]}", name, target_table, list(columns), target_columns
            )


def upgrade():
    _create_table('chemistry_study',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('owner_id', sa.String(length=50), nullable=False),
        sa.Column('publication_id', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['publication_id'], ['publication.pub_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    _create_table('chemistry_pca',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('study_id', sa.String(length=50), nullable=False),
        sa.Column('created_by', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('profile_ids', sa.JSON(), nullable=False),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['chemistry_study.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    _create_table('chemistry_sample',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('study_id', sa.String(length=50), nullable=False),
        sa.Column('specimen_id', sa.String(length=50), nullable=False),
        sa.Column('code', sa.String(length=80), nullable=False),
        sa.Column('plant_part', sa.String(length=100), nullable=False),
        sa.Column('collection_event', sa.String(length=200), nullable=False),
        sa.Column('voucher_relationship', sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.specimen_id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['chemistry_study.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('study_id', 'code', name='uq_chemistry_sample_code')
    )
    _create_table('chemistry_preparation',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('sample_id', sa.String(length=50), nullable=False),
        sa.Column('batch_code', sa.String(length=80), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('method_reference', sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(['sample_id'], ['chemistry_sample.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sample_id', 'batch_code', name='uq_chemistry_batch_code')
    )
    _create_table('chemistry_profile',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('preparation_id', sa.String(length=50), nullable=False),
        sa.Column('run_code', sa.String(length=80), nullable=False),
        sa.Column('analytical_method', sa.String(length=120), nullable=False),
        sa.Column('measurement_basis', sa.String(length=25), nullable=False),
        sa.Column('unit', sa.String(length=40), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('source_csv', sa.Text().with_variant(mysql.MEDIUMTEXT(), 'mysql'), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['preparation_id'], ['chemistry_preparation.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('preparation_id', 'run_code', name='uq_chemistry_run_code')
    )
    _create_table('chemistry_measurement',
        sa.Column('profile_id', sa.String(length=50), nullable=False),
        sa.Column('feature', sa.String(length=160), nullable=False),
        sa.Column('value', sa.Double(), nullable=True),
        sa.Column('confidence', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['chemistry_profile.id'], ),
        sa.PrimaryKeyConstraint('profile_id', 'feature')
    )


def downgrade():
    op.drop_table('chemistry_measurement')
    op.drop_table('chemistry_profile')
    op.drop_table('chemistry_preparation')
    op.drop_table('chemistry_sample')
    op.drop_table('chemistry_pca')
    op.drop_table('chemistry_study')
