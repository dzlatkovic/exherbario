# Database, backups and migrations

Running an instance: storage, backups, restores and migration notes. Back to the [README](../README.md).

## Database and backups

The API and Alembic use `DATABASE_URL`, which defaults to `sqlite:///./herbar.db`. Keep `herbar.db`, `images/`, and `files/` on persistent local storage. Ex Herbario stores its archive in SQLite only, so `DATABASE_URL` must be a `sqlite:///` path.

Stop the API and other writers before backing up the database, photos, and analytical files together.

```powershell
python -m app.db.backup backup backups/collection-snapshot
python -m app.db.backup restore backups/collection-snapshot backups/restore-check
```

Both commands create a new directory containing `herbar.db`, `images/`, `files/`, and `manifest.json`. They check SQLite integrity and foreign keys, verify that referenced files exist, and compare SHA-256 against recorded upload digests where available. Restore also checks the snapshot manifest, which detects changes since the snapshot even for older photos without an upload digest. A failed check reports the affected record or file and leaves the destination unpublished.

For a trusted older snapshot without a manifest, use `python -m app.db.backup restore OLD_SNAPSHOT NEW_DIRECTORY --allow-legacy`. Restore still verifies references and any recorded digests, then creates a manifest. A missing historical digest limits verification to the bytes available now. With the API stopped, move the current database and both file directories aside and put the verified restored copies in their place.

Migration `0005` adds nullable source and digest fields without modifying existing records or files. Its downgrade removes the original CSV links and upload digests from the database. Keep a verified snapshot of all three components to recover their associations.

Migration `0006` adds holding and scientific attribution fields and makes the legacy registration number optional. Existing UUIDs, registration numbers, account links, and dependent records are preserved. SQLite rebuilds the voucher table within a transaction and checks foreign keys before committing. Use a verified pre-upgrade snapshot for rollback. Downgrade removes the new metadata and is blocked once a voucher has been saved without a legacy registration number.

Migration `0007` adds deposition tables and preserves existing scientific records and file references. The SQLite snapshot includes frozen deposition metadata and files. Downgrade is blocked when deposition records exist. Keep verified backups and preserve the serving URLs for published versions.

Migration `0008` widens location, voucher and taxon text fields and adds collector numbers, verbatim collection dates, type status and georeference details. Existing values are kept. Downgrade is blocked when a value exceeds an earlier length or a new field holds data.

Migration `0009` adds the institution registry and dataset DOIs. It registers each institution code already used by a deposition, named as its latest version or draft names it. Review those entries and add Index Herbariorum and ROR identifiers. Versions published before this migration keep their original relative paths and snapshot digests. Publish a correction to give a deposition absolute identifiers. Downgrade is blocked once a dataset DOI is recorded.

Migration `0015` adds `external_lookup_cache`, which can be emptied at any time, and `external_import`, which records values curators accepted from GBIF, Crossref, ROR and Index Herbariorum. Existing records are unchanged. Downgrade is blocked once `external_import` holds entries.

Migration `0016` adds the ORCID iD, the name ORCID returned and the link date to accounts. Downgrade is blocked while any account has a linked iD. Migration `0017` adds `taxon_literature_compound`, the curator-published LOTUS lists; it holds only copies of Wikidata data that can be published again.

Migration `0019` adds `chemistry_condition_preset`, the run conditions and preparation methods researchers save for reuse; dropping it loses no results. Migration `0020` adds `chemistry_structure` for structures authors supply that PubChem does not have, and co-injection and structure-determination evidence on measurements. Downgrade is blocked once any structure or new evidence is recorded. Install `rdkit` from `requirements.txt` before upgrading.

### Preview migration 0004

With writers stopped and a verified snapshot available, run the preview against revision `0003`. If rehearsing from an earlier revision, first upgrade a restored copy to `0003`.

```powershell
python -m app.visibility_preview
python -m alembic upgrade head
```

The preview reports counts of vouchers, photo records, and previously released studies and profiles affected by the private defaults. It reads the configured database without updating records. Photo counts include metadata rows whose original files may be unavailable.

Migration `0004` retains identifiers, links, files, and chemistry release flags. It withholds every legacy voucher and photo until a curator reviews them individually. Review approved vouchers and their linked chemistry before restoring anonymous access. During rollback to an earlier application version, keep the instance private because the older routes make archive records anonymous again. Use the verified snapshot for recovery and clear any cached public responses from before the upgrade.

## Deploying with Docker

The repository's `Dockerfile` runs the migrations and then starts the app on `$PORT` (8000 by default). The
database, uploads and photographs live in `DATA_DIR`; mount a persistent volume there, or every redeploy starts
empty.

| Variable | Value |
| --- | --- |
| `DATA_DIR` | `/data` (the volume's mount path) |
| `DATABASE_URL` | `sqlite:////data/herbar.db` (four slashes: an absolute path) |
| `PUBLIC_BASE_URL` | The public address, e.g. `https://demo.exherbario.org` |
| `USER_SECRET` | A random value of at least 32 bytes, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

The proxy in front of the app (Railway's, or Caddy/nginx on a faculty server) handles HTTPS. Uvicorn trusts its
forwarded headers so that links and secure cookies use `https`.

## A shared password for an alpha

To keep the whole site private during a trial, set `SITE_PASSWORD` in `.env` (or in Railway's variables) and
restart. Every page then asks for that password first; a browser stays unlocked for `SITE_PASSWORD_DAYS` (30 by
default). Changing the password locks every browser again, and an empty `SITE_PASSWORD` opens the site. API
clients that send a valid `Authorization: Bearer` token are let through. Accounts and sign-in work as before,
behind the password.

## A public demo on Railway

A demo instance sets `DEMO_MODE=true`. In that mode the app:

- shows a banner on every page and asks search engines not to index it;
- lists the demo accounts and their password (`DEMO_PASSWORD`, default `herbar-demo`) on the sign-in page;
- keeps publishing locally: no DOI registration, no Zenodo mirror and no Darwin Core Archive for GBIF;
- seeds itself with synthetic data when its database is empty, and resets every day at `DEMO_RESET_HOUR` UTC
  (default 3; `-1` turns the reset off).

Steps on Railway (the Hobby plan, which allows a custom domain):

1. Create a project, choose **Deploy from GitHub repo**, and select the repository. Railway builds the `Dockerfile`.
2. Add a **volume** to the service, mounted at `/data`.
3. Set the variables in the table above, plus `DEMO_MODE=true`.
4. Under **Settings → Networking**, add the custom domain `demo.exherbario.org`. Then create the CNAME record that
   Railway shows at your DNS provider. Railway issues the certificate.
5. Deploy. The first start seeds the demo; open the address and sign in with a demo account.

To start the demo again by hand, open the service's shell and run `python -m app.demo reset`. Every demo command
refuses to run unless `DEMO_MODE` is on, so a real instance cannot be wiped.

The seed looks taxa up in GBIF and compounds in PubChem. To make it work without network access, run
`python -m app.demo record` once on a machine that is online, and commit `app/demo_data/lookups.json`; after that,
`python -m app.demo reset --offline` uses only the recorded answers.

Never run a demo and real data in the same instance: the demo's accessions and identifiers are not permanent.
