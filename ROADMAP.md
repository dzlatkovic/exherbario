# HERBAR release baseline

Reviewed checkout `ec02bf8` on 2026-11-20. The supplied roadmap describes the intended product and an audit checklist. The findings below reflect the checked-out code.

## First-release workflow

1. **Install independently.** Use Python 3.12, FastAPI, SQLAlchemy, Alembic and pytest. Run `alembic upgrade head`, bootstrap the first administrator locally, and keep SQLite and `images/` on persistent local storage. SQLite enforces foreign keys, waits up to 10 seconds for locks and serializes concurrent specimen revisions. Start with selected research vouchers. [Setup and recovery](README.md) · [Database configuration](app/db/database.py) · [Bootstrap](app/users/bootstrap.py)
2. **Register and curate a voucher.** A curator records the accession number, determination, collection site, storage and attribution, then adds photographs and literature links as available. Reuse the catalog's paginated search, CSV export, taxonomy browse and detail views. Reidentification already records the previous taxon and determination text, the actor and the timestamp in the same transaction. Add an explicit review and release step for the voucher. [Specimen and revision routes](app/specimen/routes.py) · [Revision write](app/specimen/repository/specimen_repository.py) · [Catalog](app/catalog_routes.py)
3. **Attach optional research data.** Reuse study ownership, voucher-linked samples, preparation batches, CSV profile import, source download and saved PCA. The existing study and profile flags support curator-controlled release of chemistry summaries and measurements. Voucher registration works without chemistry. [Chemistry routes](app/chemistry/routes.py) · [Study and profile services](app/chemistry/services/chemistry_services.py)
4. **Publish citable research.** Build on the existing specimen, sample, profile and publication IDs. The first scientific release needs a curator-approved deposition with a stable version ID, license and citation, an immutable snapshot, and a downloadable package with a manifest and SHA-256 checksums. Reuse the publication and specimen-publication relationships for related literature. [Publication model](app/publication/models/publication.py) · [Specimen–publication link](app/specimen/models/specimen_publication.py) · [Chemistry models](app/chemistry/models)

## Findings and release order

| Priority | Confirmed finding | Smallest practical next change |
| --- | --- | --- |
| P0 | Anonymous legacy reads expose exact coordinates, staff emails and account flags, storage locations, stored image paths and internal identification reports. The map, label and QR also carry exact coordinates. | Require staff authorization on those reads and retain the existing handlers for staff clients. Test access for anonymous callers, ordinary accounts and curators. [Legacy specimen routes](app/specimen/routes.py) · [Field locations](app/field_loc/routes.py) · [Users](app/users/routes.py) · [Storage](app/storage/routes.py) · [Images and Pl@ntNet](app/image/routes.py) |
| P0 | The specimen model has no release state. Catalog counts, list, CSV, detail, revisions and citations include records without an approval check. Locality text, staff names and the public box filter can reveal information even where the response omits numeric GPS. | Apply one publication policy before lookup, filtering, aggregation and export. Allow only approved public fields and remove the public box filter. Cover legacy reads and linked resources in the same change. [Specimen model](app/specimen/models/specimen.py) · [Catalog queries](app/catalog.py) · [Catalog responses](app/catalog_routes.py) |
| P0 | Direct image content checks the path and file, then serves the original JPEG. An image with no voucher link is retrievable and original metadata reaches the caller. Released chemistry responses can disclose voucher IDs and collection-event text without any voucher release check. | Enforce the voucher and media policies on direct downloads and all three public chemistry routes. Review image contents and publish metadata-stripped derivatives while preserving the originals. [Image validation and storage](app/image/services/image_services.py) · [Image content](app/catalog_routes.py) · [Chemistry joins](app/chemistry/repository/chemistry_repository.py) · [Public chemistry fields](app/chemistry/controller/chemistry_controller.py) |
| P0 | The catalog returns 404 for an unknown specimen while the legacy lookup returns 400. Legacy directory reads are unbounded. Login has no application-level throttling. | Verify and standardize missing-resource handling, paginate retained directories, and add login throttling. Reuse signed tokens, current-account and role checks, startup secret validation, PBKDF2 and legacy password rehashing. [Legacy specimen lookup](app/specimen/repository/specimen_repository.py) · [Bearer dependency](app/users/controller/user_auth_controller.py) · [Login and password handling](app/users/services/user_services.py) · [Startup](app/main.py) |
| P1 | Revision history covers changes to identification. A specimen release lifecycle, provenance events beyond determination revisions, and versioned depositions are absent. Chemistry flags expose current rows, and the catalog CSV is a live query. | Add review and release events, then immutable deposition versions with license, manifest, citation and withdrawal handling. Keep existing accession numbers and links. [Revision model](app/specimen/models/revision.py) · [Schema history](migrations/versions) |
| P1 | The checkout provides an API and generated docs. It has no researcher or public catalog frontend, production container recipe, or bulk voucher import. | Validate the local end-to-end workflow first. Build browser workflows on the approved API, document a deployment and restore drill, and stage broader imports and fieldwork after the voucher-to-deposition workflow. [App entry point](app/main.py) · [Current setup](README.md) |

## Route-by-route public access

These 48 paths accept requests without a bearer token in the current FastAPI application. “Staff” means the read should require an authorized staff account in the first release. Archive writes currently use `super_user`. “Reviewed” means anonymous access to approved records and fields only.

| Method and route | Current anonymous response | Proposed first-release access |
| --- | --- | --- |
| `GET /` | Placeholder JSON | Public landing entry |
| `GET, HEAD /openapi.json` | API schema | Staff on public deployments |
| `GET, HEAD /docs` | Swagger UI | Staff on public deployments |
| `GET, HEAD /docs/oauth2-redirect` | Swagger OAuth redirect helper | Staff on public deployments |
| `GET, HEAD /redoc` | ReDoc UI | Staff on public deployments |
| `POST /api/users/login` | Token for valid active credentials | Public entry with throttling |
| `GET /api/specimen` | Paginated specimens, dates and locality. The box filter and total count cover every matching specimen. | Reviewed list and counts, with box filtering reserved for staff |
| `GET /api/specimen/export` | Filtered catalog CSV, up to 10,000 rows | Reviewed fields and records |
| `GET /api/specimen/{specimen_id}` | Accession, determination, dates, collector and verifier names, locality, habitat and photo links | Reviewed fields and media links |
| `GET /api/specimen/{specimen_id}/revisions` | Previous determination, timestamps and reviser names | Reviewed history and attribution |
| `GET /api/specimen/{specimen_id}/publications` | Linked citation metadata | Reviewed citations |
| `GET /api/image/{image_id}/content` | Original JPEG bytes by image ID | Reviewed derivatives tied to released vouchers |
| `GET /api/taxonomy` | Paginated names, ranks, parent IDs and GBIF keys | Public taxonomy vocabulary |
| `GET /api/chemistry/public/studies/{study_id}` | Public study metadata and summaries for profiles with both release flags set | Reviewed study metadata and profiles |
| `GET /api/chemistry/public/profiles/{profile_id}` | Summary and normalized measurements when both flags are set | Reviewed profile, fields and voucher link |
| `GET /api/chemistry/public/specimens/{specimen_id}/profiles` | Released profile summaries for a known voucher, including an empty list if none; 404 for an unknown voucher | Reviewed vouchers and profiles |
| `GET /api/specimen/get-specimen-by-id` | Legacy specimen row with internal foreign keys | Staff |
| `GET /api/specimen/get-specimen-per-year` | Counts by collection year | Staff until reviewed aggregation exists |
| `GET /api/specimen/get-specimen-per-user` | Counts keyed by collector name | Staff |
| `GET /api/specimen/get-specimen-per-region` | Counts by field region | Staff until reviewed aggregation exists |
| `GET /api/specimen/get-gps` | Exact locations by accession for keyword matches | Staff |
| `GET /api/specimen/visualize-gps` | HTML map with exact marker locations | Staff |
| `GET /api/specimen/get-last-specimens` | Latest ten specimen rows with internal foreign keys | Staff |
| `GET /api/specimen/get-herbarium-label` | Label with coordinates, altitude and attribution | Staff |
| `GET /api/specimen/filter-by-date` | Specimen rows and internal foreign keys in date range | Staff |
| `GET /api/specimen/get-specimens-by-distance` | Accession, determination and rounded distance from configured origin | Staff |
| `GET /api/specimen/generate_qr_code` | PNG QR encoding the full label | Staff |
| `GET /api/specimen/search-specimens-by-keyword` | Paginated legacy specimen rows with internal foreign keys | Staff |
| `GET /api/field-locations/get-all-field-locations` | Location directory with exact coordinates | Staff |
| `GET /api/field-locations/get-field-loc-by-id` | Full location record by ID | Staff |
| `GET /api/storage/get-all` | Storage directory with room, shelf and box | Staff |
| `GET /api/storage/get-storage-by-id` | Room, shelf and box by ID | Staff |
| `GET /api/storage/get-box-content` | Specimens assigned to a box | Staff |
| `GET /api/image/get-image/{image_id}` | Photo metadata and stored path by ID | Staff |
| `GET /api/image/get-all_images/{specimen_id}` | Photo metadata and stored paths for a voucher | Staff |
| `GET /api/plantnet/get-result/{result_id}` | Identification result and score by ID | Staff |
| `GET /api/plantnet/get-all-results-for-image/{image_id}` | Identification results for an image | Staff |
| `GET /api/plantnet/get-all-results-for-specimen/{specimen_id}` | Identification results for a voucher | Staff |
| `GET /api/plantnet/get-plantnet-results-with-mismatched-taxonomy` | Determination discrepancies and verifier names | Staff |
| `GET /api/publication/get-all` | Full bibliography, including abstracts | Staff; approved citations via catalog |
| `GET /api/publication/get-publication-by-id` | Full publication record, including abstract | Staff; approved citations via catalog |
| `GET /api/publication_authors/get-publication-report` | DOI, author names and associated determinations | Staff |
| `GET /api/taxonomy/get-taxon-by-gbif` | Taxon record by GBIF key | Public taxonomy vocabulary |
| `GET /api/taxonomy/get-taxon-by-id` | Taxon record by HERBAR ID | Public taxonomy vocabulary |
| `GET /api/taxonomy/get-specimens-for-taxon` | Legacy specimen rows for a taxon | Staff; reviewed matches via catalog |
| `GET /api/users/id` | User ID, name, email, activation and administrator flags | Staff |
| `GET /api/users/get-all-users` | User directory with the same fields | Staff |
| `GET /api/weather/get-weather_data` | Weather measurements linked to a voucher | Staff |

The other registered routes require bearer authentication. Archive writes and the two chemistry visibility writes require `super_user`. Private chemistry list, read, create, import, source and PCA routes require an active user, with service checks limiting access to the owner or an administrator where a study already exists. [Router registration](app/main.py) · [Bearer checks](app/users/controller/user_auth_controller.py) · [Chemistry routes](app/chemistry/routes.py) · [Ownership checks](app/chemistry/services/chemistry_services.py)

## Proposed migration of existing public records

1. **Use curator approval as the publication evidence.** Prepare a dry-run inventory keyed by specimen UUID and accession number, including linked photos, citations, history and chemistry. Put new records and legacy records with unknown approval into private review, including records currently visible anonymously. Backfill publication only from a curator-approved list with an approval date and allowed public fields. Preserve the current chemistry flags and check the linked vouchers and public metadata before restoring anonymous chemistry access.
2. **Preserve accessions and original evidence.** Add release state and review provenance in a forward Alembic revision. Keep identifiers, foreign keys, timestamps, coordinates, files and scientific history. Keep the existing public URLs for approved records and return 404 for withheld records across detail, subresources and direct downloads. Use regional locality where needed and require approval for precise locations, attribution and media. Apply the policy to counts, list, CSV and every related route in the same cutover. Record withdrawals or corrections to versioned depositions and retain a public tombstone only where authorized.
3. **Rehearse recovery before cutover.** Stop writers, snapshot the SQLite database and `images/` together, then restore to a separate directory. Run each new revision on an empty database and on a populated synthetic copy with approved, withheld, partially linked and already-released records. Compare IDs, links and file hashes, run SQLite integrity and foreign-key checks, and exercise anonymous and authorized API requests. Restore the verified database and image pair under maintenance if cutover fails. The current `0002` downgrade drops chemistry tables and is unsuitable for recovering populated chemistry records. Unversioned legacy databases need a separate schema comparison before any Alembic stamping or conversion. [Migration runner](migrations/env.py) · [Chemistry upgrade and downgrade](migrations/versions/0002_chemistry_workspace.py) · [Backup utility](app/db/backup.py)

## Baseline verification

- Compared the table with the running app's route definitions and bearer dependencies. All 52 anonymous method/path pairs are listed.
- Ran Alembic against fresh temporary SQLite and upgraded a separate synthetic database from `0001` to `0002`. Both passed integrity and foreign-key checks. The populated upgrade preserved the fixture fields, identifiers and relationships across nine archive tables.
- Ran the full pytest suite with temporary SQLite and synthetic fixtures. All 193 tests passed, including image and database backup restoration, concurrent revisions and chemistry release. The run reported eight deprecation warnings.
- Clean dependency installation, MySQL, unversioned legacy imports, external service calls and production deployment remain unverified. The proposed publication migration awaits implementation and approval of the records and fields to release.

Public deployment, publication of real records and changes to live institutional data require separate authorization.
