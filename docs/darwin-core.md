# Darwin Core Archive

`/api/dwca.zip` packages the released vouchers as a [Darwin Core Archive](https://dwc.tdwg.org/text/), the format GBIF and other biodiversity aggregators harvest.

## Contents

- **Occurrences**: one row per released voucher, identified by its public page address (the one in its label QR code). Institution, collection and catalogue number, collector number, dates, name and GBIF taxon, type status, linked DOIs, approved photographs and licence.
- **Measurements**: released chemistry, one row per measured compound for each linked voucher. Add `?measurements=false` to leave them out.
- **Metadata**: `meta.xml` and `eml.xml` (GBIF's EML profile).

The archive follows the public catalog: no unreleased records, no exact localities, no collector or determiner names, no labels.

## Settings

| Setting | Purpose |
| --- | --- |
| `PUBLIC_BASE_URL` | Required. Occurrence IDs are built from it, so keep it fixed once the dataset is registered. |
| `DWC_DATASET_TITLE`, `DWC_DATASET_DESCRIPTION` | Shown by GBIF. |
| `DWC_PUBLISHER`, `DWC_CONTACT_EMAIL` | The publishing organisation and contact. |
| `DWC_LICENSE` | `CC0-1.0`, `CC-BY-4.0` (default) or `CC-BY-NC-4.0`. |

## Register with GBIF

An institution that is a GBIF data publisher, or is endorsed as one, registers the archive's address as a dataset, directly or through its national node's IPT; GBIF then harvests it regularly. For one dataset per collection, register a filtered address such as `/api/dwca.zip?collection=Herbarium`. Check the archive with the [GBIF data validator](https://www.gbif.org/tools/data-validator) first.
