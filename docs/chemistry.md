# Phytochemistry

Lab samples, preparations, profiles, the results-table import and CSV export. Back to the [README](../README.md).

## Overview

Profiles are optional for each specimen. To add one, create a lab sample linked to one or more vouchers, each with a role (`sampled_from_voucher`, `same_individual`, `same_population`, `collected_alongside`, `cultivated_from` or `reference_for_commercial_material`). Record the sample's plant part, material state and other provenance, then add a preparation batch. Essential-oil preparations need their yield (% w/w).

There are two ways to add profiles. Every profile records its technique (`GC-MS`, `GC-FID`, `LC-MS`, `LC-MS/MS` or `HPLC-DAD`) and run metadata; GC runs need the column polarity class.

- **Results table (the web page's only path):** upload the `.xlsx` or `.csv` table prepared for the paper, with compounds in rows and one column per sample (a single sample is fine). Choose the header row, assign each column a role, and enter the run conditions once for all sample columns (import tables run under different conditions separately). Columns can carry the same evidence as the per-profile CSV: RT, RI exp/lit and source, identification basis and MSI level, SD, n, CID/CAS/InChIKey, GC-MS library match and score, and LC-MS m/z, adduct, mass error (ppm) and MS/MS match. Preview the parsed values, totals, RI checks and summary rows, then review every PubChem assignment before confirming. Each sample column becomes one profile. Confirmed names become your aliases, and a layout can be saved as a template.
- **Per-profile CSV (API only):** for scripts and instrument exports, `POST /api/chemistry/preparations/{id}/profiles` takes one run as a CSV. Use `feature,value,confidence` with optional `status`, `cid`, `inchikey`, `cas`, `rt_min`, `id_basis`, `id_level`, `qualifier` (`trace`, `<LOQ`), `sd` and `n`. GC profiles also accept `ri_exp`, `ri_ref`, `ri_ref_source` and `ri_ref_polarity`; GC-MS profiles also accept `library_match` and `library_score`; LC-MS profiles also accept `mz_obs`, `adduct`, `mass_error_ppm` and `msms_match`. Leave the value blank for `not_detected` or `not_measured`, or with a `trace` / `<LOQ` qualifier.

Compounds are stored locally in a registry keyed by PubChem CID, so saved data, exports and public pages work without PubChem. An author or curator can correct a measurement's compound with a reason; the change is logged and shown on the profile, and values and source files are never edited. To check that this machine reaches PubChem, run `python -m app.chemistry.pubchem_record --check`.

New profile uploads preserve the original CSV bytes in `files/`, including any UTF-8 byte-order mark and original line endings. The authenticated source download verifies the SHA-256 and reports `X-HERBAR-Source-Fidelity: byte-preserved` and `X-HERBAR-SHA256`. Older profiles return UTF-8 reconstructed from stored text and report `legacy-reconstructed`. New photo uploads likewise record a SHA-256 for their archived JPEG. Older photos have no upload digest.

An administrator can release a study and selected profiles. Public profiles require release of the study, the profile and every linked voucher. A study appears publicly when at least one profile meets those conditions. `GET /api/chemistry/public/specimens/{specimen_id}/profiles` lists eligible profiles. Profiles whose voucher was redetermined after the sample was linked are flagged.

`GET /api/chemistry/public/export?study_id=…` (or repeated `profile_id=…`) returns released profiles as analysis-ready CSV, ready for PCA or other statistics in R or Python. `format=long` gives one row per measurement; `format=wide` gives one row per profile, with a column per compound keyed by CID (`cid:6654`). Unlinked compounds are keyed by name and RI. In the wide format, trace values are `tr` and not-detected values are `nd`.

Ex Herbario no longer runs PCA. Before upgrading past migration 0013, export any saved analyses with `python -m app.db.export_pca <directory> --remove-exported`.
