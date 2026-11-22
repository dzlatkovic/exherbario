# Install, back up and upgrade

An instance is one SQLite database (`herbar.db`) and two folders: `files/` for analytical uploads and `images/` for photographs. Keep all three on persistent storage and back them up together.

## Install

Ex Herbario needs Python 3.12.

```
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m app.users.bootstrap admin@example.org Firstname Lastname
python -m uvicorn app.main:app
```

Before running the migrations, copy `env-template` to `.env` and set `USER_SECRET` to a long random value (`python -c "import secrets; print(secrets.token_urlsafe(32))"`). Before publishing anything, set `PUBLIC_BASE_URL` to the instance's public address, such as `https://herbarium.example.edu`: published versions and the Darwin Core Archive record their identifiers under it, so it must not change later.

The bootstrap command creates the first curator account and asks for its password. For public access, put the app behind a web server that provides HTTPS, such as Caddy or nginx.

## Settings

| Setting | Purpose |
| --- | --- |
| `DATABASE_URL` | The database, `sqlite:///./herbar.db` by default. Only SQLite is supported. |
| `DATA_DIR` | Folder that holds `files/` and `images/` (default: the working folder). |
| `PUBLIC_BASE_URL` | The public address; see above. |
| `SITE_PASSWORD` | Optional shared password in front of the whole site, for a closed trial. Empty keeps the site open. |

Other settings are described in [External lookups](external-lookups.md), [Darwin Core Archive](darwin-core.md) and [Depositions](depositions.md).

## Back up and restore

Stop the app, then:

```
python -m app.db.backup backup backups/2026-11-22
python -m app.db.backup restore backups/2026-11-22 backups/restore-check
```

A backup copies the database and both folders into a new folder with a manifest of SHA-256 digests. Both commands check the database's integrity, that every referenced file exists, and that files match their recorded digests; a failed check names the record or file. To restore, stop the app and put the verified copies in place of the current database and folders.

## Upgrade

1. Stop the app and take a backup.
2. Update the code and run `python -m pip install -r requirements.txt`.
3. Run `python -m alembic upgrade head`, then start the app.

Notes on specific migrations for older instances are in [UPGRADING.md](https://github.com/dzlatkovic/exherbario/blob/main/UPGRADING.md).
