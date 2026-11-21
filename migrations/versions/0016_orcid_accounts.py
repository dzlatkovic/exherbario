"""Accounts can hold an ORCID iD that ORCID authenticated and the account holder confirmed."""

from alembic import op
import sqlalchemy as sa

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as table:
        table.add_column(sa.Column("orcid", sa.String(19), nullable=True))
        table.add_column(sa.Column("orcid_name", sa.String(200), nullable=True))
        table.add_column(sa.Column("orcid_linked_at", sa.DateTime(), nullable=True))
        table.create_unique_constraint("uq_users_orcid", ["orcid"])


def downgrade():
    connection = op.get_bind()
    if connection.execute(sa.text("SELECT 1 FROM users WHERE orcid IS NOT NULL LIMIT 1")).first():
        raise RuntimeError("Accounts have linked ORCID iDs. Unlink them before downgrading.")
    with op.batch_alter_table("users") as table:
        table.drop_constraint("uq_users_orcid", type_="unique")
        table.drop_column("orcid_linked_at")
        table.drop_column("orcid_name")
        table.drop_column("orcid")
