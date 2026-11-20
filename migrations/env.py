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
        is_sqlite = connection.dialect.name == "sqlite"
        if is_sqlite:
            # A SQLite batch rebuild replaces the parent table before restoring its name.
            # Disable enforcement on this connection only and check every key before commit.
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            connection.commit()
        context.configure(
            connection=connection, target_metadata=Base.metadata,
            transactional_ddl=True if is_sqlite else None, render_as_batch=is_sqlite,
        )
        try:
            with context.begin_transaction():
                if is_sqlite:
                    connection.exec_driver_sql("BEGIN IMMEDIATE")
                context.run_migrations()
                if is_sqlite:
                    broken = connection.exec_driver_sql("PRAGMA foreign_key_check").first()
                    if broken:
                        table, row, parent, _ = broken
                        raise RuntimeError(f"Foreign-key check failed in {table}, row {row}, referencing {parent}.")
        finally:
            if is_sqlite:
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")
                connection.commit()
