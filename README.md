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

- `GET /api/specimen` supports filtered search and pagination for released vouchers. Use `/api/specimen/export` for CSV.
- `GET /api/specimen/{specimen_id}` returns specimen details and links to photos. The `/revisions` and `/publications` subpaths show its history and references.
- A fresh database starts empty. Curators can follow the release workflow below to make selected synthetic vouchers visible in a local demo.

## Register one voucher

In Swagger, authenticate as a curator and call `POST /api/specimen/create-new-specimen`. For a voucher held locally, the minimum JSON body is `{"holding_type": "local"}`. Use `external` for a voucher held elsewhere.

```json
{
  "holding_type": "external",
  "holding_institution": "Example University",
  "collection": "Herbarium A",
  "accession": "BOT-2024-000001",
  "verbatim_label": "Text as written on the original label",
  "collector_name": "F. Collector",
  "determiner_name": "D. Botanist",
  "determination_date": "2024-05-02",
  "subnomen": "Achillea cf. millefolium"
}
```

Omit unknown fields or send `null`. HERBAR supplies a specimen UUID and registration date. A linked taxon, collection site, storage slot, and login accounts for the collector or determiner are optional. The scientific names are independent of accounts. You can add a `verifier_name` if known. Accession numbers are unique within a holding institution and collection when all three values are known. Legacy `reg_no` remains a separate global lookup key.

Use the returned `specimen_id` to link images and lab samples, and as the query parameter for label and QR reads when a legacy registration number is unavailable. The full label and scientific attribution names are available on authenticated routes. After curator release, the public catalog supports accession, institution, and collection filters.

## Public visibility

| Role | Access |
| --- | --- |
| Anonymous | Released vouchers, approved photos, linked citations and determination history, eligible released chemistry, and taxonomy vocabulary. |
| Researcher | Anonymous views plus operational reads through the authenticated archive routes. These include exact collection sites, maps, QR labels, storage, and original JPEG downloads at `GET /api/image/{image_id}/original`. Private chemistry stays available to the study owner and curators. |
| Curator (`super_user`) | Researcher access plus account directory, archive edits, and release or withdrawal controls. |

Set voucher visibility with `PUT /api/specimen/{specimen_id}/visibility` and a JSON body such as `{"is_public": true, "public_location": "withheld"}`. The `withheld` setting omits all structured location fields. The `region` setting returns country and region and enables regional filtering. Public output excludes exact GPS, locality, habitat, and staff attribution. Use the authenticated storage routes for box searches.

Approve photos individually with `PUT /api/image/{image_id}/visibility` and `{"is_public": true}`. The voucher must also be released for its photos to appear. The public content endpoint returns a re-encoded JPEG without original metadata, including GPS. The authenticated original download preserves the archived file. Review visible labels, landmarks, and free-text content before release. Withdrawing a voucher immediately hides its linked photos and chemistry from anonymous readers.

## Phytochemistry

Profiles are optional for each specimen. To add one, link a lab sample to a voucher, add a preparation batch, and import one UTF-8 CSV per run. Use `feature,value,confidence` with an optional `status` column. Leave the value blank for `not_detected` or `not_measured`.

New profile uploads preserve the original CSV bytes in `files/`, including any UTF-8 byte-order mark and original line endings. The authenticated source download verifies the SHA-256 and reports `X-HERBAR-Source-Fidelity: byte-preserved` and `X-HERBAR-SHA256`. Older profiles return UTF-8 reconstructed from stored text and report `legacy-reconstructed`. New photo uploads likewise record a SHA-256 for their archived JPEG. Older photos have no upload digest.

An administrator can release a study and selected profiles. Public profiles require release of the study, profile, and linked voucher. A study appears publicly when at least one profile meets those conditions. `GET /api/chemistry/public/specimens/{specimen_id}/profiles` lists eligible profiles. For PCA, select 3–50 comparable profiles from distinct lab samples. HERBAR saves the selected profiles, preprocessing settings, and results.

## Publish a scientific deposition

1. An authenticated researcher creates a draft with `POST /api/depositions`. Supply an institution code such as `EXU`, then add the institution name, title, license, contributor names and roles, and selected `profile_ids`. Description and rights statements are optional. HERBAR reserves an accession in that institution's namespace. Use `PUT /api/depositions/{id}/draft` with the returned `draft_revision` as `expected_revision` to edit.
2. Review `GET /api/depositions/{id}/draft/preview` before release. It shows the exact proposed public snapshot. Profiles must belong to studies available to the draft owner. Each voucher, study, and profile must be released through its existing visibility control. The preview uses the voucher's approved regional projection and keeps verbatim labels, exact locations, original sample collection-event text, and account IDs private. Scientific determiner names are included only when the draft explicitly enables them. Review contributor names and remaining free text before approval.
3. A curator calls `POST /api/depositions/{id}/publish` with the preview's `draft_revision` and `snapshot_sha256`. If the underlying records or files have changed, review a new preview. Retry the same request to get the same version. Cite the returned path at the serving instance, `/api/depositions/public/{institution}/{accession}/versions/{number}`.

Each published version freezes the metadata, voucher determination, sample and preparation links, methods, measurements, credits, rights, and file digests. It stores a bounded copy of each source file with the snapshot in the database, in the same transaction. The original uploads remain in local storage. Exports of legacy sources are marked `legacy-reconstructed`. Published files remain available if live records or files later change.

- Link a bare article DOI with `PUT /api/depositions/{id}/versions/{number}/article-doi`. Article links are attached to the cited version without editing its snapshot.
- Create a correction by sending a complete new draft with `expected_revision: null` and a `correction_reason`, then preview and publish it. The accession stays the same and the version-specific URL changes. Earlier versions remain citable and indicate that they were superseded.
- Withdraw a published version with `POST /api/depositions/{id}/versions/{number}/withdraw` and a public `reason`. Its URL returns a 410 notice with citation identity and linked DOIs. File downloads are withdrawn and the frozen records remain in the archive. Withdrawing release from a live voucher or profile leaves the immutable deposition in place. Use the version withdrawal action for the published record.

## Scientific corrections

Send a nonblank `correction_reason` in the JSON body of `PUT /api/field-locations/update-field-loc` when correcting a collection site and of `PUT /api/specimen/update-specimen` when correcting voucher metadata. A determination-only update may omit the reason for a new determination. Include it for a correction. HERBAR records the authenticated curator, UTC timestamp and changed fields with their old and new values in the same transaction. Changes to identification also retain the existing determination history.

Deleting a collection site referenced by a voucher returns HTTP 409. Weather records also prevent automatic deletion of their voucher. Migration `0003` adds the correction log and preserves prior records. Downgrading it drops the log. Back up the archive before upgrading and use a verified snapshot for recovery.

## Database and backups

The API and Alembic use `DATABASE_URL`, which defaults to `sqlite:///./herbar.db`. Keep `herbar.db`, `images/`, and `files/` on persistent local storage. MySQL deployments can set an explicit `mysql+pymysql://…` URL and use a separate account for migrations.

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

### Preview migration 0004

With writers stopped and a verified snapshot available, run the preview against revision `0003`. If rehearsing from an earlier revision, first upgrade a restored copy to `0003`.

```powershell
python -m app.visibility_preview
python -m alembic upgrade head
```

The preview reports counts of vouchers, photo records, and previously released studies and profiles affected by the private defaults. It reads the configured database without updating records. Photo counts include metadata rows whose original files may be unavailable.

Migration `0004` retains identifiers, links, files, and chemistry release flags. It withholds every legacy voucher and photo until a curator reviews them individually. Review approved vouchers and their linked chemistry before restoring anonymous access. During rollback to an earlier application version, keep the instance private because the older routes make archive records anonymous again. Use the verified snapshot for recovery and clear any cached public responses from before the upgrade.

## Tests

Run `python -m pytest`. The suite covers the SQLite API, migrations, concurrent specimen revisions, and backup restoration. CI also checks MySQL.

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)
