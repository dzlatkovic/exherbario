# Ex Herbario web app UI roadmap

**20 November 2026.** This roadmap builds on [web-app-ui-proposal.md](web-app-ui-proposal.md), which has the page map and the full endpoint inventory. Where the two differ, follow this roadmap.

## Goals

- A visitor can find a voucher by plant name or accession, see its evidence, and share the record's address.
- A researcher can choose vouchers by searching, follow a study from sample to published dataset, and pick up unfinished work where they left it.
- A curator reviews and releases records in the context of the record itself.
- The interface stays clean. Each screen has one main task and one main action, and optional sections appear only when they have data.

Success is measured by the tasks people can complete. How many API endpoints the UI calls is not a goal.

## Visual design

- **Dark only.** There is no light theme. `color-scheme: dark`, near-black surfaces with a slight green tint, and one muted sage accent for primary actions, links and the current page.
- **Understated, Material-inspired.** Flat layered surfaces (background, card, raised), thin borders, a soft shadow only on menus and dialogs, rounded buttons, clear hover, focus and disabled states. No gradients, illustrations or decorative motion.
- **Fira Sans** for text, in weights 400, 500 and 600, and **Fira Mono** for identifiers, digests, code and data. Both are self-hosted woff2 under the SIL Open Font License, with Latin, Greek and Cyrillic subsets, so names like α-pinene and Serbian text render in the same face.
- **Mobile first.** Single-column forms below 36rem; touch targets at least 44 px tall; 16 px inputs, so phones do not zoom on focus; wide tables scroll inside their own frame; section navigation becomes scrollable chips on phones and a sticky side list on wide screens.

## Principles

1. **Public pages are rendered on the server.** Jinja templates built from the public data only: fast, shareable, and usable without JavaScript. A signed-in visitor sees exactly what the public sees.
2. **Staff pages use small scripts.** Plain JavaScript with no build step or framework, one small module per page instead of a growing `researcher.js`.
3. **One main action per screen.** Secondary actions sit beside the data they change. Advanced fields are folded away and open on request.
4. **Show only what exists.** No empty sections. Evidence columns, photos, chemistry and history appear only when the record has them.
5. **Search instead of IDs.** Pickers search by name and accession, and show the holding institution and recorded name. The IDs can still be copied and are used in addresses.
6. **The server makes the visibility decisions.** The UI never decides what is public. It renders what the API returns.

## Navigation

| Audience | Navigation |
| --- | --- |
| Visitor | **Specimens** · **Depositions** · **Sign in** |
| Researcher | **Catalog** · **My work** · account menu |
| Curator | **Catalog** · **My work** · **Curation** · account menu |

- **Taxa** is a link from the specimen search and the specimen record, not a top-level item.
- **My work** holds studies and depositions together, most recently changed first.
- **Curation** is one area with four tabs: **Review**, **Vouchers**, **Directories** (institutions, taxonomy, storage, field locations, bibliography) and **Accounts**.

## Endpoint triage

The API has 118 operations. Each gets one of three treatments.

| Treatment | Operations |
| --- | --- |
| **Screen** | Public catalog, specimen record, its history and literature; public study, profile and compound; deposition versions and the index; studies, samples, preparations, profiles, imports and corrections; depositions and review; release controls; photos; labels and QR codes; directories; accounts. |
| **Folded into an existing screen** | `filter-by-date`, `get-last-specimens` and `get-specimens-by-distance` become filters and a sort order on the staff search. `create-revision` and `update-specimen` (for the name) become one **Redetermine** action on the record. `get-specimens-for-taxon` becomes a taxon filter. Linking a publication or an author is done from the record it concerns. |
| **API only, for now** | Per-year, per-user and per-region counts; `get-gps` and `visualize-gps`; Pl@ntNet; weather; `get-publication-report`; `build-taxonomic-tree` and `create-taxon-from-gbif-data` (used by scripts). These can be reconsidered for a later **Collection reports** page, or for removal. |

## Step 0: Prerequisites

| Work | Detail |
| --- | --- |
| **Session cookie** | Signing in also sets an HttpOnly, SameSite=Lax session cookie. The bearer token stays for API clients. Without this, every page change or reload signs a researcher out. Add a sign-in redirect that returns to the page that was asked for, CSRF protection for cookie-authenticated writes, and sign-out. |
| **Shared layout** | A masthead with the navigation for each audience, an account menu, a page title block, and an empty-state component in `base.html`. |
| **Split `researcher.js`** | Shared helpers (requests, forms, pickers) in one module, plus one module per staff page. Behaviour stays the same while the existing workspace is moved over. |

The step is done when a researcher can reload any staff page without signing in again, and a page that requires sign-in returns to itself after login.

**Status, 20 November 2026: done.**
- **Session cookie:** `POST /sign-in` and `POST /sign-out` are plain forms. The session cookie is HttpOnly and SameSite=Lax. A readable CSRF cookie is echoed in `X-CSRF-Token` for cookie-authenticated writes. Bearer tokens keep working for API clients without CSRF.
- **Pages:** `GET /api/users/me` tells pages who is signed in. The redirect target after sign-in is limited to local paths, and sign-in forms posted from another origin are refused.
- **Layout and scripts:** `base.html` has the masthead and account menu. Scripts are split into `assets/js/core.js` and `assets/js/researcher.js`. The dark stylesheet and Fira fonts are in place.
- **Checked:** in Chrome at 390 px and 1440 px wide.

## Step 1: Find a voucher

| Page | Content |
| --- | --- |
| `/` | A search field labelled "Plant name, accession or registration number", a short introduction, and recently published depositions once the index exists. |
| `/specimens` | Results with the filters in the address (collection, institution, region, date range), pagination, separate empty states for "nothing released yet" and "no matches", and **Download matching specimens (CSV)**. |
| `/specimens/{id}` | Determination, accession, institution and collection first. Then approved photos, collection date and public region, determination history, literature and released chemistry. Unknown and private IDs show the same "unavailable" page. |
| Voucher picker | One search component used in the sample form and the deposition form. It uses the authenticated keyword search, so private vouchers can be found by accession, and has a **Use voucher** action. Looking up an exact ID still works for pasted links. |

The step is done when:
- A guest can search by common name and share a filtered address that reproduces the results.
- A researcher can select a private voucher by accession without copying an ID.
- Private vouchers and their photos never appear in public results or exports.

**Status, 21 November 2026: done.**
- **Public pages:** `/`, `/specimens` and `/specimens/{id}` are Jinja pages in `app/web/catalog_pages.py`, built on the existing public catalog functions. The holding-institution and collection filters list only released specimens (`catalog.public_facets`).
- **Ordering:** results are ordered by registration number, then accession.
- **Navigation:** visitors see Specimens · Sign in; staff see Catalog · My work.
- **Voucher picker:** `voucherPicker` in `assets/js/core.js` drives the workspace's Voucher section and the deposition draft. A pasted record ID opens that voucher directly.
- **Checked:** in Chrome at 390 px and 1440 px wide.

## Step 2: Follow the evidence

| Page | Content |
| --- | --- |
| `/studies/{id}`, `/profiles/{id}` | The released study and its eligible profiles. Each profile shows every linked voucher with its role, the technique and run, the yield, the measurements with their evidence, the qualifiers (trace, <LOQ, not detected), the compound corrections and the redetermination notice. Each study offers long and wide CSV. |
| `/compounds/{cid}` | The registry record: structure, formula, mass, InChIKey, SMILES, CAS (from PubChem synonyms) and a link to PubChem. |
| `/researcher/specimens/{id}` | The staff record: exact site, storage, original media, label and QR printing, **Redetermine**, **Manage photos**, and **Release voucher** beside the data being reviewed. |

The step is done when:
- A visitor can go from a voucher to a released measurement and its unit.
- Making any linked voucher private removes the profile from the public study, the voucher page and the export.

**Status, 21 November 2026: done.**
- **Public pages:** `/studies/{id}`, `/profiles/{id}` and `/compounds/{cid}` are in `app/web/chemistry_pages.py`. They read the local compound registry only, never PubChem. Measurements are shown in retention-time order, and evidence columns appear only when used.
- **Staff record:** `/researcher/specimens/{id}` and its print label (`/label`, with an inline QR code linking to the public record) are in `app/web/staff_pages.py`, with actions in `assets/js/specimen.js`. Research use lists only the viewer's own studies; curators see all.
- **API:** the staff specimen read now includes `is_public` and `public_location`, and the image read includes `is_public`.
- **Not yet:** a public "Cited in datasets" list on the voucher record is still to come.

## Step 3: Resume work and publish

| Page | Content |
| --- | --- |
| `/researcher` (**My work**) | Studies and depositions in one list, plus "continue import" entries. |
| `/researcher/studies/{id}` | Samples (codes, vouchers and roles, provenance), each with its preparations and runs. **Add sample**, **Import results table** and **Upload CSV** are separate actions. A private profile view lists its measurements, source download and compound corrections. |
| `/researcher/studies/{id}/imports/{id}` | The import wizard on its own page, in four steps (upload, columns, preview, review), with cell errors shown beside the table and a progress bar for PubChem lookups. Leaving the page and coming back resumes the import. |
| `/researcher/depositions/{id}` | Edit, preview, release status (every linked voucher, study and profile) and publication. Vouchers and profiles are chosen by name. A conflicting edit shows the current draft and asks for a new preview. |

The step is done when:
- A researcher can reopen a draft and an unfinished import from **My work**.
- A researcher can recover from a stale preview, and can publish a deposition with vouchers only.
- A researcher can prepare a preview, but only a curator can publish.

**Status, 21 November 2026: done, with two items left.**
- **Pages:** `/researcher` (My work), `/researcher/studies/{id}`, `/researcher/profiles/{id}`, `/researcher/studies/{id}/imports/{id}`, `/researcher/depositions/new` and `/researcher/depositions/{id}` are in `app/web/work_pages.py`. Each page has its own script (`mywork.js`, `study.js`, `profile.js`, `import.js`, `deposition.js`); shared helpers are in `core.js`. Records the viewer may not see return the same "not found" page as missing ones.
- **Replaced:** the one-page workspace (`researcher.html`, `researcher.js`) is gone.
- **Deposition editor:** runs are chosen by study and run, vouchers through the voucher search, and both show as named lists; the raw ID lists stay under **More options**. The page address changes to the deposition's own address after the first save. Curators see **Publish**; researchers see a note to pass the page to a curator.
- **API:** `GET /api/depositions` lists the signed-in user's depositions, and `GET /api/chemistry/studies/{id}/imports` lists a study's imports.
- **Checked** in Chrome at phone and desktop widths: create a study, build a deposition by name, save, reload, validate, publish and open the published version, with no page or request errors.
- **Progress (added 21 November 2026):** PubChem lookups and "Accept all" show a progress bar and can be stopped between batches of five; finished rows are kept, so the lookup resumes later.
- **Not yet:** a conflicting draft edit shows the server's message rather than loading the current draft.

## Step 4: Published work and curation

| Page | Content |
| --- | --- |
| `/depositions` | The published index: title, institution, accession, latest version, date and DOI. Superseded versions are reached through their record. Withdrawn versions keep their notice and HTTP 410. |
| Curation › Review | Drafts submitted for review, each opening the release panel and preview. |
| Curation › Directories and Accounts | List, create and edit. When a delete is refused because the record is linked, the page shows the server's reason and keeps the record on screen. |
| Version management | Article DOI, dataset DOI and withdrawal, on the version page, for curators. |

The step is done when:
- An old citation still opens its original frozen version.
- A withdrawn version opens its notice.
- Public search never returns a draft.

**Status, 21 November 2026: done.**
- **Public index:** `/depositions` (in `catalog_pages.py`) lists each published deposition at its latest version, newest first, with search over title, accession, institution and dataset DOI. A withdrawn latest version stays listed with a **Withdrawn** label and opens its notice (HTTP 410). API: `GET /api/depositions/public?q=&page=&size=`. Visitors see **Specimens · Depositions** in the navigation; signed-in users reach both through tabs under **Catalog**.
- **Review:** migration `0014` adds `deposition.submitted_at`. Researchers use **Submit for review** and **Take back** on the deposition page (`POST`/`DELETE /api/depositions/{id}/submission`); they can keep editing, and curators review the latest saved draft. Publishing clears the submission. Curators see the queue, oldest first, at **Curation › Review** (`GET /api/depositions/review`). My work marks drafts that are in review.
- **Version management:** on a published version page, curators get **Manage this version**: link an article DOI, register the dataset DOI (once), or withdraw the version after a confirmation. The frozen snapshot is unchanged.
- **Curation area:** `app/web/curation_pages.py` with tabs **Review**, **Vouchers** (search every voucher, register a new one), **Directories** (institutions, storage, field locations, bibliography, taxonomy; driven by `assets/js/directories.js`) and **Accounts** (create researcher or curator accounts, deactivate, reactivate, delete). Researchers get a 404 there.
- **Refused deletes:** deleting a storage box, field location, publication, taxon or account that is still in use now returns HTTP 409 with a plain reason instead of a database error, and the page keeps the record on screen with that reason. Curators can't delete or deactivate their own account.
- **Limits of the existing API:** institutions can only be added (codes are part of published accessions); a storage box keeps its label; taxa are added from GBIF keys and can't be edited by hand.
- **Checked** in Chrome at 360, 390 and 1440 px: index and search, account creation, add, edit and delete in a directory, a refused delete, taxon search, linking an article DOI, and a researcher submitting and taking back a draft while the curator's queue updates.

## API work by step

| Step | Change |
| --- | --- |
| 0 | Session cookie at sign-in, a cookie-or-bearer authentication dependency, CSRF protection for cookie-authenticated writes, sign-out. |
| 1 | None. The public list, export and detail endpoints and the authenticated keyword search already exist. |
| 2 | Add the release flag and public-location setting to the staff specimen read, so a standalone release control starts in the right state. Add a public lookup of the published versions that cite a voucher before promising "Cited in datasets". |
| 3 | An owner-scoped list of depositions and drafts. A study-scoped list of imports (ID, file, date, status). Study detail links to its open imports. |
| 4 | A published-version index with pagination. A curator review list, with an explicit "submitted for review" state and the action that sets it. |

The release panel for drafts with several vouchers per profile was fixed on 20 November 2026. A test covers a sample with two vouchers, one of them private.

## Not in scope yet

- Collection reports (counts, maps), Pl@ntNet and weather screens.
- Cross-study search and per-taxon chemistry summaries; these come after the "Later" items in the chemistry redesign.
- A separate front-end framework or build pipeline.
