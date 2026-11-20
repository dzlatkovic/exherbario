# Herbarium Research and Botanical Archive Resource (HERBAR)

HERBAR is a FastAPI backend for a university herbarium. It links specimen records to taxonomy, collection sites, storage, photos, publications, and identification history. Researchers can also link lab samples and chemical profiles to voucher specimens.

## Quick start

Use Python 3.12 and run these commands from the project root with your virtual environment active.

```powershell
python -m pip install -r requirements.txt
```

Copy `env-template` to `.env`. Set `USER_SECRET` to the output of `python -c "import secrets; print(secrets.token_urlsafe(32))"`. The file also configures the origin for distance searches and the Pl@ntNet key for image identification.

```powershell
python -m alembic upgrade head
python -m app.users.bootstrap admin@example.org Firstname Lastname
python -m uvicorn app.main:app --reload
```

The bootstrap command creates the first administrator and prompts for a password. In Swagger, log in with `POST /api/users/login` and paste the returned `access_token` into **Authorize**. [Open Swagger](http://127.0.0.1:8000/docs)

## Explore the API

- `GET /api/specimen` supports filtered search and pagination. Use `/api/specimen/export` for CSV.
- `GET /api/specimen/{specimen_id}` returns specimen details and links to photos. The `/revisions` and `/publications` subpaths show its history and references.
- In the locally seeded demo database, try `reg_no=DEMO-001` for a yarrow voucher with a photo and two revisions, or search for `wild thyme` to find vouchers with synthetic chemistry profiles. A fresh database starts empty.

## Phytochemistry

Profiles are optional for each specimen. To add one, link a lab sample to a voucher, add a preparation batch, and import one UTF-8 CSV per run. Use `feature,value,confidence` with an optional `status` column. Leave the value blank for `not_detected` or `not_measured`.

An administrator can release a study and selected profiles. `GET /api/chemistry/public/specimens/{specimen_id}/profiles` lists the released profiles for a voucher. For PCA, select 3–50 comparable profiles from distinct lab samples. HERBAR saves the selected profiles, preprocessing settings, and results.

## Scientific corrections

Send a nonblank `correction_reason` in the JSON body of `PUT /api/field-locations/update-field-loc` when correcting a collection site and of `PUT /api/specimen/update-specimen` when correcting voucher metadata. A determination-only update may omit the reason for a new determination. Include it for a correction. HERBAR records the authenticated curator, UTC timestamp and changed fields with their old and new values in the same transaction. Changes to identification also retain the existing determination history.

Deleting a collection site referenced by a voucher returns HTTP 409. Weather records also prevent automatic deletion of their voucher. Migration `0003` adds the correction log and preserves prior records. Downgrading it drops the log. Back up the database and images together before upgrading and use a verified snapshot for recovery.

## Database and backups

The API and Alembic use `DATABASE_URL`, which defaults to `sqlite:///./herbar.db`. Keep `herbar.db` and `images/` on persistent local storage. MySQL deployments can set an explicit `mysql+pymysql://…` URL and use a separate account for migrations.

Stop the API and other writers before backing up the database and photos together.

```powershell
python -m app.db.backup backup backups/collection-snapshot
python -m app.db.backup restore backups/collection-snapshot backups/restore-check
```

Both commands create a new directory containing `herbar.db` and `images/`. With the API stopped, move the current pair aside and put the restored pair in its place.

## Tests

Run `python -m pytest`. The suite covers the SQLite API, migrations, concurrent specimen revisions, and backup restoration. CI also checks MySQL.

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)
