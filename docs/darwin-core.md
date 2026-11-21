# Darwin Core Archive

`GET /api/dwca.zip` packages the released vouchers as a [Darwin Core Archive](https://dwc.tdwg.org/text/), the format GBIF and other biodiversity aggregators harvest. Back to the [README](../README.md).

## What is in the archive

- `occurrence.txt`: one row per released voucher.
  - `occurrenceID` is the voucher's public page, `PUBLIC_BASE_URL/specimens/{id}`, the address printed in its label QR code. Keep `PUBLIC_BASE_URL` fixed once the dataset is registered: GBIF matches records across harvests by this ID.
  - Holding institution, collection and catalogue number; collector number; event date as recorded and as written on the label; name and GBIF taxon with its classification; determination date; type status; linked DOIs (`associatedReferences`); approved photos (`associatedMedia`); licence.
- `measurementorfact.txt`: released chemistry, as one row per detected or trace measurement for each released voucher linked to the measured sample. Each row gives the compound and measurement basis, the value and unit, the technique and method, and the profile, sample, voucher role, PubChem CID and retention index. Values keep the chemistry export's precision. A qualified value keeps its qualifier: `trace`, `<LOQ`, or `<LOQ (0.123456789)` when a number was also recorded, and the remarks begin with the qualifier. Leave the measurements out with `?measurements=false`.
- `meta.xml` describes the columns, and `eml.xml` describes the dataset: title, abstract, publisher, contact and licence. `eml.xml` validates against GBIF's EML profile 1.3; the tests check this. Its `packageId` combines a stable dataset identifier, derived from the archive URL and its filters, with a version that changes whenever the metadata or records change.

## What is left out

The archive follows the public catalog's rules. Unreleased vouchers are not included, nor are unapproved photos, or chemistry that is not fully released. Exact coordinates and localities are never exported: a voucher released with `region` gives its country and region, and one released with `withheld` gives no location. `informationWithheld` says which applies. Collector, determiner and verifier names, staff accounts, verbatim labels and storage are never exported.

The archive is built from live records each time it is requested; collections above SQLite's per-query parameter limit export normally, up to 100,000 vouchers per archive. Deposition snapshots are not read or changed; each published deposition version keeps its own frozen record and archive.

## Settings

| Setting | Purpose |
| --- | --- |
| `PUBLIC_BASE_URL` | Required; occurrence IDs are built from it. |
| `DWC_DATASET_TITLE` | Dataset title shown by GBIF. |
| `DWC_DATASET_DESCRIPTION` | A paragraph describing the collection. |
| `DWC_PUBLISHER` | The publishing organization, e.g. the university herbarium. |
| `DWC_CONTACT_EMAIL` | Dataset contact; `EXTERNAL_CONTACT_EMAIL` is used when empty. |
| `DWC_LICENSE` | `CC0-1.0`, `CC-BY-4.0` (default) or `CC-BY-NC-4.0`, the three licences GBIF accepts. |

## Registering with GBIF

An institution that is, or is endorsed as, a GBIF data publisher can register the archive URL as a dataset, either directly or through its GBIF node's IPT. GBIF then harvests it periodically. To publish one dataset per collection, register a filtered URL such as `/api/dwca.zip?holding_institution=Example%20University&collection=Herbarium`. Check an archive with the [GBIF data validator](https://www.gbif.org/tools/data-validator) before registering it.
