"""Create the original HERBAR archive schema."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_table(name, *definition):
    op.create_table(name, *definition, mysql_engine="InnoDB")


def upgrade():
    _create_table('field_loc',
        sa.Column('field_loc_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('country', sa.String(length=20), nullable=True),
        sa.Column('region', sa.String(length=20), nullable=True),
        sa.Column('locality', sa.String(length=40), nullable=True),
        sa.Column('altitude', sa.Integer(), nullable=True),
        sa.Column('habitat', sa.String(length=20), nullable=True),
        sa.Column('gps_lat', sa.Float(), nullable=True),
        sa.Column('gps_long', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('field_loc_id')
    )
    _create_table('publication',
        sa.Column('pub_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('doi', sa.String(length=200), nullable=False),
        sa.Column('year', sa.Date(), nullable=True),
        sa.Column('journal', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('pub_id')
    )
    _create_table('storage',
        sa.Column('storage_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('box', sa.String(length=100), nullable=False),
        sa.Column('room', sa.String(length=20), nullable=True),
        sa.Column('shelf', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('storage_id'),
        sa.UniqueConstraint('box')
    )
    _create_table('taxonomy',
        sa.Column('taxon_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('taxon_name', sa.String(length=100), nullable=False),
        sa.Column('gbif_key', sa.String(length=20), nullable=False),
        sa.Column('taxon_rank', sa.Enum('FORM', 'VARIETY', 'SUBSPECIES', 'SPECIES', 'GENUS', 'FAMILY', 'ORDER', 'CLASS', 'PHYLUM', 'KINGDOM', name='taxonrank'), nullable=False),
        sa.Column('parent_taxon_key', sa.String(length=50), nullable=True),
        sa.Column('common_name', sa.String(length=50), nullable=True),
        sa.Column('authority', sa.String(length=30), nullable=True),
        sa.ForeignKeyConstraint(['parent_taxon_key'], ['taxonomy.taxon_id']),
        sa.PrimaryKeyConstraint('taxon_id'),
        sa.UniqueConstraint('gbif_key')
    )
    _create_table('users',
        sa.Column('user_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=True),
        sa.Column('surname', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('password', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )
    _create_table('publication_authors',
        sa.Column('publication_authors_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('publication_id', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['publication_id'], ['publication.pub_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id']),
        sa.PrimaryKeyConstraint('publication_authors_id'),
        sa.UniqueConstraint('user_id', 'publication_id', name='publication_authors_uc')
    )
    _create_table('specimen',
        sa.Column('specimen_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('reg_no', sa.String(length=10), nullable=False),
        sa.Column('collection_date', sa.Date(), nullable=True),
        sa.Column('reg_date', sa.Date(), nullable=True),
        sa.Column('taxon_id', sa.String(length=50), nullable=True),
        sa.Column('subnomen', sa.String(length=200), nullable=True),
        sa.Column('field_loc_id', sa.String(length=50), nullable=True),
        sa.Column('storage_id', sa.String(length=50), nullable=True),
        sa.Column('collected_by', sa.String(length=50), nullable=True),
        sa.Column('verified_by', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['collected_by'], ['users.user_id']),
        sa.ForeignKeyConstraint(['field_loc_id'], ['field_loc.field_loc_id']),
        sa.ForeignKeyConstraint(['storage_id'], ['storage.storage_id']),
        sa.ForeignKeyConstraint(['taxon_id'], ['taxonomy.taxon_id']),
        sa.ForeignKeyConstraint(['verified_by'], ['users.user_id']),
        sa.PrimaryKeyConstraint('specimen_id'),
        sa.UniqueConstraint('reg_no')
    )
    _create_table('image',
        sa.Column('image_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('specimen_id', sa.String(length=50), nullable=True),
        sa.Column('image_type', sa.Enum('field', 'herbarium', 'macro', 'microscope', name='imagetype'), nullable=True),
        sa.Column('file_path', sa.String(length=150), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.specimen_id']),
        sa.PrimaryKeyConstraint('image_id')
    )
    _create_table('revision',
        sa.Column('revision_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('revised_by', sa.String(length=50), nullable=True),
        sa.Column('specimen_id', sa.String(length=50), nullable=True),
        sa.Column('prev_taxon_id', sa.String(length=50), nullable=True),
        sa.Column('prev_subnomen', sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(['prev_taxon_id'], ['taxonomy.taxon_id']),
        sa.ForeignKeyConstraint(['revised_by'], ['users.user_id']),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.specimen_id']),
        sa.PrimaryKeyConstraint('revision_id')
    )
    _create_table('specimen_publication',
        sa.Column('specimen_publication_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('specimen_id', sa.String(length=50), nullable=True),
        sa.Column('publication_id', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['publication_id'], ['publication.pub_id']),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.specimen_id']),
        sa.PrimaryKeyConstraint('specimen_publication_id'),
        sa.UniqueConstraint('specimen_id', 'publication_id', name='publication_authors_uc')
    )
    _create_table('weather',
        sa.Column('weather_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('specimen_id', sa.String(length=50), nullable=True),
        sa.Column('mean_temperature', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('precipitation', sa.Float(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('wind_direction', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['specimen_id'], ['specimen.specimen_id']),
        sa.PrimaryKeyConstraint('weather_id'),
        sa.UniqueConstraint('specimen_id')
    )
    _create_table('plantnet_result',
        sa.Column('result_id', sa.String(length=50), autoincrement=False, nullable=False),
        sa.Column('image_id', sa.String(length=50), nullable=True),
        sa.Column('best_match', sa.String(length=150), nullable=True),
        sa.Column('gbif_id', sa.String(length=20), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['image.image_id']),
        sa.PrimaryKeyConstraint('result_id')
    )


def downgrade():
    op.drop_table('plantnet_result')
    op.drop_table('weather')
    op.drop_table('specimen_publication')
    op.drop_table('revision')
    op.drop_table('image')
    op.drop_table('specimen')
    op.drop_table('publication_authors')
    op.drop_table('users')
    op.drop_table('taxonomy')
    op.drop_table('storage')
    op.drop_table('publication')
    op.drop_table('field_loc')
