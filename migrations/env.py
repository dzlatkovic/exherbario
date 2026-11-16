"""Run HERBAR schema migrations against the configured database."""

from alembic import context

import app.main  # Registers all ORM models.
from app.db.database import Base, DATABASE_URL, engine


if context.is_offline_mode():
    context.configure(url=DATABASE_URL, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        # Explicit BEGIN makes SQLite DDL transactional with the sqlite3 driver.
        is_sqlite = connection.dialect.name == "sqlite"
        context.configure(
            connection=connection, target_metadata=Base.metadata,
            transactional_ddl=True if is_sqlite else None, render_as_batch=is_sqlite,
        )
        with context.begin_transaction():
            if is_sqlite:
                connection.exec_driver_sql("BEGIN IMMEDIATE")
            context.run_migrations()
