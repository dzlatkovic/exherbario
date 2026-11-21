# HERBAR web app structure

**Proposal for checkout `13ffce6` · 20 November 2026**

Make the public specimen catalog the home page. A visitor should be able to arrive with a plant name, find a voucher, inspect its evidence, and share the record URL. A signed-in researcher should be able to find that voucher, select it for a sample, and follow the sample through to a published dataset. Curators should manage collection records in the same context, with a dedicated area for release review and administration.

**Build search first.** Add the public catalog and specimen detail page, then put a searchable voucher picker into the existing researcher form. All three have backend support today. Reuse the existing Jinja templates, stylesheet and FastAPI services for public pages, and extend the current JavaScript form for staff selection.

## What ships today

| Entry point | What a person can do today | Where the workflow stops |
| --- | --- | --- |
| `/` | Read a JSON “In Progress” message. | A visitor gets no collection search or navigation. |
| `/researcher` | Sign in, use a voucher by ID, select or create a study, link samples to vouchers, record preparations, import analytical results, review PubChem assignments, save a deposition and preview it. Curators also have registration, release and publish controls. | Four sections share one page. The voucher picker requires a specimen ID. Reopening a deposition requires its internal ID. The sheet importer has compound search, which searches a different entity. |
| `/depositions/{institution}/{accession}/versions/{number}` | Read a published version by direct link. See vouchers, provenance, citation, license, version status, and available downloads. | There is no published-deposition index. The masthead leads back to the research workspace or API docs. |
| `/docs` and `/redoc` | Inspect the API. Swagger also lets a user execute operations with the appropriate credentials. | Visitors need to know which operation to run and how to interpret its response. |

The OpenAPI schema contains **118 method/path operations on 115 API paths**. The researcher page references **27** operations, including CSV export links and curator-only controls. The count comes from static analysis of browser calls and download links. The public version page also uses the deposition service on the server and links to two API downloads. The inventory at the end maps each operation to its current use and proposed screen. [App entry](../app/main.py) · [HTML routes](../app/web/routes.py) · [Workspace actions](../app/web/assets/researcher.js) · [Version template](../app/web/templates/deposition.html)

## Navigation

| Audience | Navigation | Starting task |
| --- | --- | --- |
| Visitor | **Specimens** · **Taxa** · **Depositions** · **Sign in** | Search the released collection. Add the Depositions navigation item when the public index is available. Existing version links work independently. |
| Researcher | **Collection** · **Studies** · **My depositions** · **Public catalog** | Find an archive voucher or resume an owned study. Reach imports and measurements from their study. |
| Curator | Researcher navigation plus **Curation** | Review a deposition, release a voucher or photo, manage collection directories, or administer accounts. Record-specific edits also appear on the relevant detail page. |

Use **Specimens** for public browsing and **Select voucher** when choosing the physical evidence for a sample or deposition. Both actions resolve to a HERBAR specimen ID. Show the accession, holding institution and recorded name in pickers so a researcher can distinguish records with similar names. Keep the ID available to copy and use it in URLs and relationships.

### Proposed page map

Paths below are proposed HTML routes except for the two marked **existing**. All API paths remain under `/api`.

```text
/                                      Public catalog entry
/specimens                             Search results with shareable query parameters
/specimens/{id}                        Public specimen record
/taxa                                  Taxon search and hierarchy
/studies/{id}                          Released study and eligible profiles
/profiles/{id}                         Public measurements and evidence
/depositions                           Published dataset index
/depositions/{institution}/{accession}/versions/{number}   Existing version page

/researcher                            Existing sign-in and workspace entry
/researcher/collection                 Staff voucher search
/researcher/collection/{id}            Archive record, labels, media and related work
/researcher/studies                    Accessible studies
/researcher/studies/{id}               Samples, preparations, profiles and imports
/researcher/studies/{id}/imports/{importId}   Resume column assignment and review
/researcher/depositions                Drafts and previously published work
/researcher/depositions/{id}           Edit, validate, preview and share a draft
/researcher/curation                   Release review and collection administration
```

## Public catalog

**Search and results.** Label the home page search field “Plant name, accession or registration number.” Submitting opens `/specimens?q=…`. Reuse the public list query for search, counts and pagination. It matches scientific names, common names, the name recorded on the voucher, accessions and registration numbers. Offer collection, holding institution, region and collection-date range as additional filters. Keep filters and page number in the URL so Back and shared links reproduce the result. [Catalog queries](../app/catalog.py) · [Parameters and export](../app/catalog_routes.py)

| Results view | Behavior |
| --- | --- |
| Matching vouchers | Show name, accession or registration number, holding institution, collection, collection date, and public region when supplied. The result payload supports a text list without fetching each record. Show photos on the detail page. |
| Empty collection or search | Distinguish “No specimens have been released” on an unfiltered catalog from “No matches for these filters.” Keep the query editable and offer **Clear filters**. |
| Export | Offer **Download matching specimens (CSV)** with the same filters. The server caps the full export at 10,000 matches. Above that threshold, ask the visitor to narrow the search. |
| Taxonomy | Browse roots and children with `GET /api/taxonomy` and `parent_id`, or search using `query`. A taxon can link to a catalog name search. Label it **Search this name** because the catalog's taxon filter is a substring match. An exact membership view would need a public taxon-ID filter. |

**Specimen record.** Lead with determination, accession, institution and collection. Follow with approved photos, collection date, public region/country, determination history, linked literature, and released analytical profiles. Make sections conditional on available data. Offer a shareable record link even when the voucher has no photograph or chemistry. Use the public photo URL returned by the detail response. A public request for an unavailable specimen gets the same unavailable view whether the ID is unknown or private. [Public specimen projection](../app/catalog_routes.py) · [Released profile selection](../app/chemistry/repository/chemistry_repository.py)

**From voucher to research data.** A profile links to its released study and to other released vouchers attached to the same sample. Show the role of each voucher, technique, measurement basis, units, identification evidence and corrections. Preserve the distinction between zero, trace, below quantification, not measured and not detected. Link a registered CID to its compound details. Offer long and wide CSV for eligible profiles. An unlinked or unpublished profile must never be revealed through a public study count or an empty-state message. [Chemistry responses](../app/chemistry/controller/chemistry_controller.py) · [CSV export](../app/chemistry/services/export.py)

**Published depositions.** Keep the existing version URL as the citable destination. A future public index should lead with title, institution, accession, latest version, date and DOI when present. On a version page show the frozen determination and measurements as published, including for older versions. Link a live voucher separately if publicly available. Preserve supersession links and the withdrawal notice with its existing HTTP 410 behavior. A public version can outlive a change in the live catalog. [Version rendering](../app/web/routes.py) · [Public version and withdrawal rules](../app/deposition/services.py)

## Signed-in workspace

| Screen | Main interactions | Backend fit and constraints |
| --- | --- | --- |
| **Collection / Select voucher** | Use the same search control in the collection, sample editor and deposition editor. In selection mode, show a **Use voucher** action that returns to the form with the chosen record. Keep exact-ID lookup for pasted links and historical records. | Use authenticated `GET /api/specimen/search-specimens-by-keyword` with `keyword`, `page` and `size`. It covers accession, registration number and recorded name, including private vouchers. Display those supported search terms. Public catalog search additionally supports taxonomy names. |
| **Archive specimen** | Put identification, label and QR, exact collection site, storage box, photographs, Pl@ntNet suggestions, weather and literature on the record. Put **Edit determination**, **Manage photos** and **Release voucher** next to the data a curator is reviewing. | Reuse staff reads and the curator writes. Labels and QR accept a specimen ID even without a legacy registration number. Determination edits already create revision history. Keep Pl@ntNet suggestions visibly distinct from the accepted identification. |
| **Studies** | Open a study by title. Within it, organize work by sample code, voucher links and roles, preparation batch, then analytical run. Show a redetermination notice when a voucher's identification has changed since linking. | The study detail already returns samples, preparation records and profile summaries. Owners and curators can inspect private profiles, download their source and correct a compound assignment with a reason. Use the existing add/remove-link operations when editing an existing sample. |
| **Import results** | Keep the existing upload → assign columns → preview → review compounds → confirm flow. Display row/cell errors beside the table, retain manual resolution during PubChem outages, and link each created profile back to its study. | Reuse the existing import endpoints and per-profile CSV path. A saved import can be reopened by ID. Listing resumable imports requires a new study-scoped read. |
| **My depositions** | Select vouchers and optional profiles by display name. Save a draft, reopen it, share its internal link with a curator, and inspect exactly what will be published. Support voucher-only deposits. | Creation, editing, preview and known-ID retrieval already exist. The index requires a new owner-scoped list. Preserve draft revision and preview digest checks. On a conflict, show the current draft and require a fresh preview before publication. |
| **Curation / Release review** | Open a draft, show each selected voucher, study and profile with its release state, inspect the public preview, then publish. Handle DOI registration, related article DOI and withdrawal on the version record. | A curator can open a known draft by ID. Fix the profile-linked inputs response before expanding the release panel. A cross-owner list needs a curator-scoped read. A submitted-for-review inbox also needs an explicit submission state and action. |
| **Curation / Collection administration** | Provide directories for institutions, taxonomy, storage, field locations, bibliography and accounts. Put operations such as linking a publication or moving a specimen into the relevant record workflow. Group internal collection counts and maps under **Collection reports**. | Reuse the directory routes in the inventory. Offer account creation and activation to curators. Existing server constraints can reject deletion of linked records. Show the reason and retain the record on screen. |

**Role and navigation behavior.** Public pages should render entirely from public projections, including for signed-in visitors. Authenticated collection pages may show exact locations, attribution, original media and storage. Study ownership further limits private chemistry. Curators can approve photos separately from vouchers. A public profile requires a released study, a released profile, and at least one linked voucher with every linked voucher released. Leave each decision to the existing server checks. [Bearer roles](../app/users/controller/user_auth_controller.py) · [Visibility](../app/visibility_routes.py) · [Study access](../app/chemistry/services/chemistry_services.py)

**Session and forms.** The current JavaScript holds the token and current selection in memory and reads `can_publish` after login. For the first delivery, keep authenticated navigation within that workspace so selecting a voucher preserves the form and session. Before splitting it into full page loads, define how a user resumes the intended URL after sign-in. Preserve unsaved edits when opening a picker, return keyboard focus to its trigger on selection, and announce search counts and validation errors. On narrow screens, let search filters collapse and keep accession, name and the selection action visible together. [Workspace state and forms](../app/web/assets/researcher.js)

## API work that affects the design

| Screen or action | Dependency | Delivery decision |
| --- | --- | --- |
| Public catalog, detail, staff voucher picker | Existing public and authenticated searches have different fields and visibility. | Build both clients now. Keep the results and counts specific to their audience. |
| Release review for drafts containing profiles | The draft-inputs service unpacks six values where the snapshot selector returns five, including a collection of voucher links. The current panel also expects one voucher per profile. | Return and render every linked voucher and its release state. Cover a sample with two vouchers, one private. [Draft inputs](../app/deposition/services.py) · [Record selection](../app/deposition/snapshot.py) |
| Curator release controls on a standalone record | The staff specimen response lacks the voucher visibility fields needed to initialize a toggle reliably. The draft-inputs endpoint provides them only in draft context. | Extend the staff read to expose the recorded release flag and public-location setting before adding standalone controls. [Specimen schema](../app/specimen/schemas/specimen_schemas.py) |
| **My depositions**, curator review list, public dataset index | The API can retrieve a known draft or public version, but has no paginated collection read for these screens. | Add a private list bounded by actor and a separate published-version index. Define handling of superseded versions and withdrawal notices in the public index. Keep known-ID opening and stable version links during rollout. |
| **Resume import** list | The per-import read exists. Study detail omits import drafts. | Add a study-scoped summary list with import ID, source name, date and status, restricted to permitted imports. Offer direct resume links first. |
| Voucher-to-deposition links | Public voucher detail does not enumerate version snapshots that cite the voucher. | Introduce a published-version lookup by voucher ID before promising “Cited in datasets” on every record. |

## Delivery order and acceptance

1. **Find a voucher.** Replace the root placeholder with catalog entry, add public results and detail, update the masthead, and embed the staff picker in the existing form. Verify a guest can search by common name and share a filtered URL, and a researcher can select a private voucher by accession without copying a UUID. Confirm a private voucher and its photos are absent from public results and exports.
2. **Follow the evidence.** Link taxonomy, studies, profiles and compound detail from public records. Add staff record tools, profile source download and correction history. Verify a visitor can go from a voucher to a released measurement and its unit. Verify that making any linked voucher private removes the live profile from public study, voucher and export results.
3. **Resume work and publish.** Add private list reads, repair the multi-voucher release panel and link drafts and imports from their owning screens. Verify reopening a draft, recovering from a stale preview and publishing a voucher-only version. A researcher can prepare a preview. Only a curator can publish it.
4. **Discover and maintain published work.** Add the public deposition index, version management and curator directories. Verify an old citation still opens its original frozen version, a withdrawn version opens its notice, and a public search never returns a draft.

## Endpoint inventory

One row per registered `/api` method and path. **Access** records the route's entry requirement. Private chemistry, imports and draft services also check record ownership. **Current UI** identifies direct workspace calls and clickable downloads. “Service” means the version page obtains the same data by calling the service in-process. A dash means no direct wiring was found in either custom HTML surface. Proposed destinations group related actions on a single record or workflow. Swagger and external API clients are outside the UI usage count.

### Public catalog (5)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `GET /api/specimen` | Public | — | Results |
| `GET /api/specimen/export` | Public | — | export CSV |
| `GET /api/specimen/{specimen_id}` | Public | — | specimen detail |
| `GET /api/specimen/{specimen_id}/revisions` | Public | — | history |
| `GET /api/specimen/{specimen_id}/publications` | Public | — | literature |

### Taxa (8)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/taxonomy/create-taxon` | Curator | — | Curate taxon |
| `GET /api/taxonomy/get-taxon-by-gbif` | Public | — | taxon by GBIF key |
| `GET /api/taxonomy/get-taxon-by-id` | Public | — | taxon detail |
| `POST /api/taxonomy/create-taxon-from-gbif-data` | Curator | — | import GBIF entry |
| `POST /api/taxonomy/build-taxonomic-tree` | Curator | — | build taxonomy tree |
| `DELETE /api/taxonomy/delete-taxon` | Curator | — | curate taxon |
| `GET /api/taxonomy/get-specimens-for-taxon` | Account | — | staff taxon specimens |
| `GET /api/taxonomy` | Public | — | browse taxa |

### Staff collection (15)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/specimen/create-new-specimen` | Curator | Workspace | Register voucher |
| `GET /api/specimen/get-specimen-by-id` | Account | Workspace | staff voucher detail |
| `DELETE /api/specimen/delete-specimen` | Curator | — | remove voucher |
| `GET /api/specimen/get-specimen-per-year` | Account | — | reports by year |
| `GET /api/specimen/get-specimen-per-user` | Account | — | reports by collector |
| `GET /api/specimen/get-specimen-per-region` | Account | — | reports by region |
| `GET /api/specimen/get-gps` | Account | — | staff map data |
| `GET /api/specimen/visualize-gps` | Account | — | staff map |
| `GET /api/specimen/get-last-specimens` | Account | — | recent vouchers |
| `GET /api/specimen/get-herbarium-label` | Account | — | print label |
| `PUT /api/specimen/update-specimen` | Curator | — | edit voucher |
| `GET /api/specimen/filter-by-date` | Account | — | date search |
| `GET /api/specimen/get-specimens-by-distance` | Account | — | nearby specimens |
| `GET /api/specimen/generate_qr_code` | Account | — | print QR |
| `GET /api/specimen/search-specimens-by-keyword` | Account | — | staff results and voucher picker |

### Determination history (1)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/revision/create-revision` | Curator | — | Record a determination revision |

### Record release (2)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `PUT /api/specimen/{specimen_id}/visibility` | Curator | Workspace | Release voucher and set public location |
| `PUT /api/image/{image_id}/visibility` | Curator | — | approve photo |

### Specimen photographs (6)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/image/upload-image` | Curator | — | Upload photo |
| `GET /api/image/get-image/{image_id}` | Account | — | staff photo details |
| `GET /api/image/get-all_images/{specimen_id}` | Account | — | staff voucher gallery |
| `DELETE /api/image/delete-image` | Curator | — | manage photo |
| `GET /api/image/{image_id}/content` | Public | — | public approved image |
| `GET /api/image/{image_id}/original` | Account | — | staff original download |

### Pl@ntNet identification (6)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/plantnet/save-plantnet-identification` | Curator | — | Request identification |
| `GET /api/plantnet/get-result/{result_id}` | Account | — | identification detail |
| `DELETE /api/plantnet/delete-id-result` | Curator | — | manage identification |
| `GET /api/plantnet/get-all-results-for-image/{image_id}` | Account | — | photo suggestions |
| `GET /api/plantnet/get-all-results-for-specimen/{specimen_id}` | Account | — | voucher suggestions |
| `GET /api/plantnet/get-plantnet-results-with-mismatched-taxonomy` | Account | — | discrepancy report |

### Field locations (5)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/field-locations/create-new-field-loc` | Curator | — | Create site |
| `GET /api/field-locations/get-all-field-locations` | Account | — | sites directory |
| `GET /api/field-locations/get-field-loc-by-id` | Account | — | site detail |
| `DELETE /api/field-locations/delete-field-loc` | Curator | — | manage site |
| `PUT /api/field-locations/update-field-loc` | Curator | — | edit site |

### Storage and box contents (6)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/storage/create-new-storage` | Curator | — | Create storage location |
| `GET /api/storage/get-all` | Account | — | storage directory |
| `GET /api/storage/get-storage-by-id` | Account | — | storage detail |
| `DELETE /api/storage/delete-storage` | Curator | — | manage storage |
| `GET /api/storage/get-box-content` | Account | — | box contents |
| `PUT /api/storage/update-storage` | Curator | — | edit storage |

### Collection-event weather (4)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/weather/create-weather_data` | Curator | — | Enter observations |
| `POST /api/weather/download-weather_data` | Curator | — | fetch weather data |
| `GET /api/weather/get-weather_data` | Account | — | voucher weather |
| `DELETE /api/weather/delete-weather_data` | Curator | — | manage weather record |

### Bibliography (5)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/publication/create-new-publication` | Curator | — | Create reference |
| `GET /api/publication/get-all` | Account | — | staff bibliography |
| `GET /api/publication/get-publication-by-id` | Account | — | reference details |
| `DELETE /api/publication/delete-publication` | Curator | — | manage reference |
| `PUT /api/publication/update-publication` | Curator | — | edit reference |

### Publication authors and reports (3)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/publication_authors/create-new-publication-authors` | Curator | — | Link author |
| `DELETE /api/publication_authors/delete-publication-authors` | Curator | — | unlink author |
| `GET /api/publication_authors/get-publication-report` | Account | — | publication report |

### Voucher bibliography (2)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/specimen_publication/create-new-specimen_publication` | Curator | — | Link reference to voucher |
| `DELETE /api/specimen_publication/delete-specimen_publication` | Curator | — | unlink reference |

### Studies and analytical profiles (28)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `GET /api/chemistry/studies` | Account | Workspace | Study list |
| `POST /api/chemistry/studies` | Account | Workspace | new study |
| `GET /api/chemistry/studies/{study_id}` | Account | Workspace | study detail |
| `POST /api/chemistry/studies/{study_id}/samples` | Account | Workspace | add sample |
| `POST /api/chemistry/samples/{sample_id}/vouchers` | Account | — | link voucher |
| `DELETE /api/chemistry/samples/{sample_id}/vouchers/{specimen_id}` | Account | — | remove voucher link |
| `POST /api/chemistry/samples/{sample_id}/preparations` | Account | Workspace | add preparation |
| `POST /api/chemistry/preparations/{preparation_id}/profiles` | Account | Workspace | upload per-profile CSV |
| `PUT /api/chemistry/profiles/{profile_id}/measurements/{feature}/compound` | Account | — | correct compound assignment |
| `POST /api/chemistry/studies/{study_id}/imports` | Account | Workspace | upload results table |
| `GET /api/chemistry/imports/{import_id}` | Account | — | resume import by ID |
| `PUT /api/chemistry/imports/{import_id}/assignment` | Account | Workspace | assign columns and preview |
| `POST /api/chemistry/imports/{import_id}/match` | Account | Workspace | match compounds |
| `PUT /api/chemistry/imports/{import_id}/rows/{row}/compound` | Account | Workspace | review compound for row |
| `POST /api/chemistry/imports/{import_id}/confirm` | Account | Workspace | confirm import |
| `GET /api/chemistry/import-templates` | Account | Workspace | saved layouts |
| `GET /api/chemistry/imports/{import_id}/templates/{template_id}` | Account | Workspace | apply layout |
| `GET /api/chemistry/compounds/search` | Account | Workspace | compound picker |
| `GET /api/chemistry/compounds/{cid}/parent` | Account | — | inspect parent compound |
| `GET /api/chemistry/public/export` | Public | Workspace link | export released profiles |
| `GET /api/chemistry/public/compounds/{cid}` | Public | — | public compound detail |
| `GET /api/chemistry/profiles/{profile_id}` | Account | — | private profile detail |
| `GET /api/chemistry/profiles/{profile_id}/source` | Account | — | download private source |
| `PUT /api/chemistry/studies/{study_id}/visibility` | Curator | Workspace | release study |
| `PUT /api/chemistry/profiles/{profile_id}/visibility` | Curator | Workspace | release profile |
| `GET /api/chemistry/public/studies/{study_id}` | Public | — | public study |
| `GET /api/chemistry/public/profiles/{profile_id}` | Public | — | public profile |
| `GET /api/chemistry/public/specimens/{specimen_id}/profiles` | Public | — | public specimen chemistry |

### Depositions and institutions (15)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/depositions` | Account | Workspace | New deposition |
| `GET /api/depositions/{deposition_id}/draft` | Account | Workspace | open draft |
| `PUT /api/depositions/{deposition_id}/draft` | Account | Workspace | edit draft |
| `GET /api/depositions/{deposition_id}/draft/preview` | Account | Workspace | preview snapshot |
| `GET /api/depositions/{deposition_id}/draft/inputs` | Account | Workspace | release prerequisites |
| `POST /api/depositions/{deposition_id}/publish` | Curator | Workspace | publish approved version |
| `PUT /api/depositions/{deposition_id}/versions/{number}/article-doi` | Curator | — | link article DOI |
| `PUT /api/depositions/{deposition_id}/versions/{number}/doi` | Curator | — | register dataset DOI |
| `POST /api/depositions/{deposition_id}/versions/{number}/withdraw` | Curator | — | record withdrawal |
| `GET /api/depositions/public/{institution}/{accession}/versions/{number}` | Public | Version · service | citable version |
| `GET /api/depositions/public/{institution}/{accession}/versions/{number}/datacite.json` | Public | — | download metadata when supported |
| `GET /api/depositions/public/{institution}/{accession}/versions/{number}/archive.zip` | Public | Version link | download version ZIP |
| `GET /api/depositions/public/{institution}/{accession}/versions/{number}/files/{profile_id}` | Public | Version link | download frozen file |
| `GET /api/institutions` | Public | — | institution picker |
| `POST /api/institutions` | Curator | — | register institution |

### Sign-in and accounts (7)

| API operation | Access | Current UI | Proposed destination |
| --- | --- | --- | --- |
| `POST /api/users/add-new-user` | Curator | — | Create researcher account |
| `POST /api/users/add-new-super-user` | Curator | — | create curator account |
| `POST /api/users/login` | Public | Workspace | sign in |
| `GET /api/users/id` | Curator | — | account detail |
| `GET /api/users/get-all-users` | Curator | — | account directory |
| `DELETE /api/users/delete-user` | Curator | — | remove account |
| `PUT /api/users/update/is_active` | Curator | — | activate or deactivate account |
