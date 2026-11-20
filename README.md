# Herbarium Research and Botanical Archive Resource (HERBAR)

HERBAR is a FastAPI backend for a university herbarium. It links specimen records to taxonomy, collection sites, storage, photos, publications, and identification history. Researchers can also link lab samples and chemical profiles to voucher specimens.

## Quick start

Use Python 3.12 and run these commands from the project root with your virtual environment active.

```powershell
python -m pip install -r requirements.txt
```

Copy `env-template` to `.env`. Set `USER_SECRET` to the output of `python -c "import secrets; print(secrets.token_urlsafe(32))"`. The file also configures the origin for distance searches and the Pl@ntNet key for image identification. Before publishing real records, set `PUBLIC_BASE_URL` to the instance's public origin, such as `https://herbar.example.edu`. Every published version records its identifiers under that origin.

```powershell
python -m alembic upgrade head
python -m app.users.bootstrap admin@example.org Firstname Lastname
python -m uvicorn app.main:app --reload
```

The bootstrap command creates the first administrator and prompts for a password. In Swagger, log in with `POST /api/users/login` and paste the returned `access_token` into **Authorize**. [Open Swagger](http://127.0.0.1:8000/docs)

The [research workspace](http://127.0.0.1:8000/researcher) uses the same sign-in. It guides you through voucher registration or selection, study and sample setup, CSV upload, draft validation, preview, and publication. A researcher can save the draft and share its internal deposition ID with a curator. Curators can open that draft, review its linked records, and publish the approved preview.

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
  "subnomen": "Achillea cf. millefolium",
  "collector_number": "FC 1234",
  "verbatim_collection_date": "mid-June 2024",
  "type_status": "isotype"
}
```

Omit unknown fields or send `null`. `type_status` accepts holotype, isotype, lectotype, isolectotype, neotype, isoneotype, epitype, syntype, isosyntype, paratype, isoparatype or type. Collection sites accept locality text up to 500 characters and optional `coordinate_uncertainty_m`, `geodetic_datum` and `georeference_source`. HERBAR supplies a specimen UUID and registration date. A linked taxon, collection site, storage slot, and login accounts for the collector or determiner are optional. The scientific names are independent of accounts. You can add a `verifier_name` if known. Accession numbers are unique within a holding institution and collection when all three values are known. Legacy `reg_no` remains a separate global lookup key.

Use the returned `specimen_id` to link images and lab samples, and as the query parameter for label and QR reads when a legacy registration number is unavailable. The full label and scientific attribution names are available on authenticated routes. The public catalog shows the collector number and type status, but not collector names. After curator release, the public catalog supports accession, institution, and collection filters.

## Public visibility

| Role | Access |
| --- | --- |
| Anonymous | Released vouchers, approved photos, linked citations and determination history, eligible released chemistry, and taxonomy vocabulary. |
| Researcher | Anonymous views plus operational reads through the authenticated archive routes. These include exact collection sites, maps, QR labels, storage, and original JPEG downloads at `GET /api/image/{image_id}/original`. Private chemistry stays available to the study owner and curators. |
| Curator (`super_user`) | Researcher access plus account directory, archive edits, and release or withdrawal controls. |

Set voucher visibility with `PUT /api/specimen/{specimen_id}/visibility` and a JSON body such as `{"is_public": true, "public_location": "withheld"}`. The `withheld` setting omits all structured location fields. The `region` setting returns country and region and enables regional filtering. Public output excludes exact GPS, locality, habitat, and staff attribution. Use the authenticated storage routes for box searches.

Approve photos individually with `PUT /api/image/{image_id}/visibility` and `{"is_public": true}`. The voucher must also be released for its photos to appear. The public content endpoint returns a re-encoded JPEG without original metadata, including GPS. The authenticated original download preserves the archived file. Review visible labels, landmarks, and free-text content before release. Withdrawing a voucher immediately hides its linked photos and chemistry from anonymous readers.

## Phytochemistry

Profiles are optional for each specimen. To add one, create a lab sample linked to one or more vouchers, each with a role (`sampled_from_voucher`, `same_individual`, `same_population`, `collected_alongside`, `cultivated_from` or `reference_for_commercial_material`). Record the sample's plant part, material state and other provenance, then add a preparation batch. Essential-oil preparations need their yield (% w/w).

There are two ways to add profiles. Every profile records its technique (`GC-MS`, `GC-FID`, `LC-MS`, `LC-MS/MS` or `HPLC-DAD`) and run metadata; GC runs need the column polarity class.

- **Results table (main path):** upload the `.xlsx` or `.csv` table prepared for the paper, with compounds in rows and samples in columns. Choose the header row and assign each column a role. Preview the parsed values, totals, RI checks and summary rows, then review every PubChem assignment before confirming. Each sample column becomes one profile. Confirmed names become your aliases, and a layout can be saved as a template.
- **Per-profile CSV:** use `feature,value,confidence` with optional `status`, `cid`, `inchikey`, `cas`, `rt_min`, `id_basis`, `id_level`, `qualifier` (`trace`, `<LOQ`), `sd` and `n`. GC profiles also accept `ri_exp`, `ri_ref`, `ri_ref_source` and `ri_ref_polarity`; GC-MS profiles also accept `library_match` and `library_score`; LC-MS profiles also accept `mz_obs`, `adduct`, `mass_error_ppm` and `msms_match`. Leave the value blank for `not_detected` or `not_measured`, or with a `trace` / `<LOQ` qualifier.

Compounds are stored locally in a registry keyed by PubChem CID, so saved data, exports and public pages work without PubChem. An author or curator can correct a measurement's compound with a reason; the change is logged and shown on the profile, and values and source files are never edited. To check that this machine reaches PubChem, run `python -m app.chemistry.pubchem_record --check`.

New profile uploads preserve the original CSV bytes in `files/`, including any UTF-8 byte-order mark and original line endings. The authenticated source download verifies the SHA-256 and reports `X-HERBAR-Source-Fidelity: byte-preserved` and `X-HERBAR-SHA256`. Older profiles return UTF-8 reconstructed from stored text and report `legacy-reconstructed`. New photo uploads likewise record a SHA-256 for their archived JPEG. Older photos have no upload digest.

An administrator can release a study and selected profiles. Public profiles require release of the study, the profile and every linked voucher. A study appears publicly when at least one profile meets those conditions. `GET /api/chemistry/public/specimens/{specimen_id}/profiles` lists eligible profiles. Profiles whose voucher was redetermined after the sample was linked are flagged.

`GET /api/chemistry/public/export?study_id=…` (or repeated `profile_id=…`) returns released profiles as analysis-ready CSV, ready for PCA or other statistics in R or Python. `format=long` gives one row per measurement; `format=wide` gives one row per profile, with a column per compound keyed by CID (`cid:6654`). Unlinked compounds are keyed by name and RI. In the wide format, trace values are `tr` and not-detected values are `nd`.

HERBAR no longer runs PCA. Before upgrading past migration 0013, export any saved analyses with `python -m app.db.export_pca <directory> --remove-exported`.

## Publish a scientific deposition

A curator first registers the institution whose namespace holds the accessions. Use `POST /api/institutions` with a `code` such as `EXU` and the institution `name`. Add the `index_herbariorum_code` and `ror_id` where they exist, so citations resolve to a known institution. `GET /api/institutions` lists registered codes. A code, Index Herbariorum code or ROR ID cannot be reassigned to another institution.

1. An authenticated researcher creates a draft with `POST /api/depositions`. Supply a registered institution code, then add the title, license and contributor names and roles, with an optional `orcid` for each contributor. Select `profile_ids` for analytical profiles, `specimen_ids` for vouchers cited without analytical data, or both. Description and rights statements are optional. HERBAR reserves an accession in that institution's namespace. Use `PUT /api/depositions/{id}/draft` with the returned `draft_revision` as `expected_revision` to edit.
2. Review `GET /api/depositions/{id}/draft/preview` before release. It shows the exact proposed public snapshot. Profiles must belong to studies available to the draft owner. Each voucher, study, and profile must be released through its existing visibility control. The preview uses the voucher's approved regional projection and keeps verbatim labels, exact locations, original sample collection-event text, and account IDs private. Scientific determiner and collector names are included only when the draft enables `include_determiner_names` or `include_collector_names`. Collector numbers and type status are always included. Review contributor names and remaining free text before approval.
3. A curator calls `POST /api/depositions/{id}/publish` with the preview's `draft_revision` and `snapshot_sha256`. If the underlying records or files have changed, review a new preview. Retry the same request to get the same version. The returned `identifier` is the version's public page under `PUBLIC_BASE_URL`, and `url` is its JSON record.

Each published version freezes the metadata, voucher determination, sample and preparation links, methods, measurements, credits, rights, and file digests. It stores a bounded copy of each source file with the snapshot in the database, in the same transaction. The original uploads remain in local storage. Exports of legacy sources are marked `legacy-reconstructed`. Published files remain available if live records or files later change.

Share the public page at `/depositions/{institution}/{accession}/versions/{number}`. It shows the citation, licenses and credits, voucher and sample relationships, methods, files, and any correction or withdrawal notice. The **Download version ZIP** link packages the frozen `deposition.json`, source files under `files/`, and a versioned `manifest.json` with sizes and SHA-256 digests. Later DOI links and status notices appear on the page while the archived version bytes stay fixed. Withdrawal disables downloads for that version.

Verify a downloaded ZIP from a checkout with Python 3.12. Use the snapshot SHA-256 shown on the public page to compare against the published digest.

```powershell
python -m app.deposition.verify_archive .\deposition-v1.zip --snapshot-sha256 <digest>
```

The verifier runs offline without the server, database, or installed Python dependencies. Omitting the expected digest still checks the archive's internal consistency.

- Get a dataset DOI by mirroring the version to Zenodo. Set `ZENODO_TOKEN` to a token with the `deposit:write` and `deposit:actions` scopes. Rehearse with `ZENODO_URL=https://sandbox.zenodo.org`, then run `python -m app.deposition.mirror_zenodo EXU <accession> 1 --curator curator@example.org`. Add `--dry-run` to review the Zenodo metadata first. Zenodo receives the same ZIP that HERBAR serves, and HERBAR records the DOI it returns. An institution with its own DataCite membership can register a DOI from `GET /api/depositions/public/{institution}/{accession}/versions/{number}/datacite.json`. Record that DOI with `PUT /api/depositions/{id}/versions/{number}/doi` and `{"doi": "10.…", "agency": "datacite"}`. The public page then cites the DOI.
- Link a bare article DOI with `PUT /api/depositions/{id}/versions/{number}/article-doi`. Article links are attached to the cited version without editing its snapshot.
- Create a correction by sending a complete new draft with `expected_revision: null` and a `correction_reason`, then preview and publish it. The accession stays the same and the version-specific URL changes. Earlier versions remain citable and indicate that they were superseded.
- Withdraw a published version with `POST /api/depositions/{id}/versions/{number}/withdraw` and a public `reason`. Its URL returns a 410 notice with citation identity and linked DOIs. File downloads are withdrawn and the frozen records remain in the archive. Withdrawing release from a live voucher or profile leaves the immutable deposition in place. Use the version withdrawal action for the published record.

## Scientific corrections

Send a nonblank `correction_reason` in the JSON body of `PUT /api/field-locations/update-field-loc` when correcting a collection site and of `PUT /api/specimen/update-specimen` when correcting voucher metadata. A determination-only update may omit the reason for a new determination. Include it for a correction. HERBAR records the authenticated curator, UTC timestamp and changed fields with their old and new values in the same transaction. Changes to identification also retain the existing determination history.

Deleting a collection site referenced by a voucher returns HTTP 409. Weather records also prevent automatic deletion of their voucher. Migration `0003` adds the correction log and preserves prior records. Downgrading it drops the log. Back up the archive before upgrading and use a verified snapshot for recovery.

## Database and backups

The API and Alembic use `DATABASE_URL`, which defaults to `sqlite:///./herbar.db`. Keep `herbar.db`, `images/`, and `files/` on persistent local storage. HERBAR stores its archive in SQLite only, so `DATABASE_URL` must be a `sqlite:///` path.

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

### Preview migration 0004

With writers stopped and a verified snapshot available, run the preview against revision `0003`. If rehearsing from an earlier revision, first upgrade a restored copy to `0003`.

```powershell
python -m app.visibility_preview
python -m alembic upgrade head
```

The preview reports counts of vouchers, photo records, and previously released studies and profiles affected by the private defaults. It reads the configured database without updating records. Photo counts include metadata rows whose original files may be unavailable.

Migration `0004` retains identifiers, links, files, and chemistry release flags. It withholds every legacy voucher and photo until a curator reviews them individually. Review approved vouchers and their linked chemistry before restoring anonymous access. During rollback to an earlier application version, keep the instance private because the older routes make archive records anonymous again. Use the verified snapshot for recovery and clear any cached public responses from before the upgrade.

## Tests

Run `python -m pytest`. The suite covers the SQLite API, migrations, concurrent specimen revisions, and backup restoration.

## License

HERBAR is released under the [MIT License](LICENSE).

## Meta

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)
