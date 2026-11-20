"""Export saved PCA analyses before migration 0013 removes them from HERBAR.

    python -m app.db.export_pca exports/pca
    python -m app.db.export_pca exports/pca --remove-exported

Each analysis is written as <id>.json, with manifest.json listing SHA-256 digests. --remove-exported deletes only
the analyses whose files were written and verified, so `alembic upgrade head` can continue.
"""

import argparse
import json
from hashlib import sha256
from pathlib import Path

import sqlalchemy as sa

from app.db.database import engine

COLUMNS = ("id", "study_id", "created_by", "created_at", "profile_ids", "configuration", "results")


def _value(value):
    return json.loads(value) if isinstance(value, str) and value[:1] in "[{" else value


def export(connection, directory: Path, remove: bool) -> int:
    if not sa.inspect(connection).has_table("chemistry_pca"):
        print("No chemistry_pca table: nothing to export.")
        return 0
    table = sa.table("chemistry_pca", *(sa.column(name) for name in COLUMNS))
    directory.mkdir(parents=True, exist_ok=True)
    manifest = {}
    rows = connection.execute(sa.select(*table.c).order_by(table.c.created_at, table.c.id)).mappings().all()
    for row in rows:
        record = {name: _value(row[name]) for name in COLUMNS}
        record["created_at"] = str(record["created_at"])
        data = (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        path = directory / f"{row['id']}.json"
        path.write_bytes(data)
        if sha256(path.read_bytes()).hexdigest() != sha256(data).hexdigest():
            raise SystemExit(f"Could not verify {path}.")
        manifest[path.name] = sha256(data).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if remove and manifest:
        connection.execute(table.delete().where(table.c.id.in_([name[:-5] for name in manifest])))
    print(f"Exported {len(manifest)} analyses to {directory}" + (" and removed them." if remove else "."))
    return len(manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--remove-exported", action="store_true")
    arguments = parser.parse_args()
    with engine.begin() as connection:
        export(connection, arguments.directory, arguments.remove_exported)


if __name__ == "__main__":
    main()
