# Vouchers, visibility and corrections

How to register vouchers, control what the public sees, and correct records. Back to the [documentation home](index.md).

## Register one voucher

Sign in as a curator and choose **My work → Register a voucher**. Enter the collector, field number and collection date from the label. For a partial date such as “May 1972”, use **Date as written on the label** and leave the exact date blank. Choose a saved field site or enter a new one on the form. Under **Identification**, search for the taxon and choose **Use** for a local match or **Add and use** for a GBIF match. Transcribe the name printed on the label separately.

In Swagger, authenticate as a curator and call `POST /api/specimen/create-new-specimen`. For a voucher held locally, the minimum JSON body is `{"holding_type": "local"}`. Use `external` for a voucher held elsewhere. Supply `field_loc_id` to reuse a field site or `field_location` to save a new site together with the voucher.

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
  "field_location": {"country": "Serbia", "region": "Niš", "locality": "Suva Planina"},
  "type_status": "isotype"
}
```

Omit unknown fields or send `null`. `type_status` accepts holotype, isotype, lectotype, isolectotype, neotype, isoneotype, epitype, syntype, isosyntype, paratype, isoparatype or type. Collection sites accept locality text up to 500 characters and optional `coordinate_uncertainty_m`, `geodetic_datum` and `georeference_source`. Ex Herbario supplies a specimen UUID and registration date. A linked taxon, collection site, storage slot, and login accounts for the collector or determiner are optional. The scientific names are independent of accounts. You can add a `verifier_name` if known. Accession numbers are unique within a holding institution and collection when all three values are known. Legacy `reg_no` remains a separate global lookup key.

Use the returned `specimen_id` to link images and lab samples, and as the query parameter for label and QR reads when a legacy registration number is unavailable. The full label and scientific attribution names are available on authenticated routes. The public catalog shows the collector number and type status, but not collector names. After curator release, the public catalog supports accession, institution, and collection filters.

## Explore the API

- `GET /api/specimen` supports filtered search and pagination for released vouchers. Use `/api/specimen/export` for CSV.
- `GET /api/specimen/{specimen_id}` returns specimen details and links to photos. The `/revisions` and `/publications` subpaths show its history and references.
- A fresh database starts empty. Curators can follow the release workflow below to make selected synthetic vouchers visible in a local demo.

## Public visibility

| Role | Access |
| --- | --- |
| Anonymous | Released vouchers, approved photos, linked citations and determination history, eligible released chemistry, and taxonomy vocabulary. |
| Researcher | Anonymous views plus operational reads through the authenticated archive routes. These include exact collection sites, maps, QR labels, storage, and original JPEG downloads at `GET /api/image/{image_id}/original`. Private chemistry stays available to the study owner and curators. |
| Curator (`super_user`) | Researcher access plus account directory, archive edits, and release or withdrawal controls. |

Set voucher visibility with `PUT /api/specimen/{specimen_id}/visibility` and a JSON body such as `{"is_public": true, "public_location": "withheld"}`. The `withheld` setting omits all structured location fields. The `region` setting returns country and region and enables regional filtering. Public output excludes exact GPS, locality, habitat, and staff attribution. Use the authenticated storage routes for box searches.

Approve photos individually with `PUT /api/image/{image_id}/visibility` and `{"is_public": true}`. The voucher must also be released for its photos to appear. The public content endpoint returns a re-encoded JPEG without original metadata, including GPS. The authenticated original download preserves the archived file. Review visible labels, landmarks, and free-text content before release. Withdrawing a voucher immediately hides its linked photos and chemistry from anonymous readers.

## Scientific corrections

Send a nonblank `correction_reason` in the JSON body of `PUT /api/field-locations/update-field-loc` when correcting a collection site and of `PUT /api/specimen/update-specimen` when correcting voucher metadata. A determination-only update may omit the reason for a new determination. Include it for a correction. Ex Herbario records the authenticated curator, UTC timestamp and changed fields with their old and new values in the same transaction. Changes to identification also retain the existing determination history. To clear a collection date, site, storage slot, collector account or verifier account, send `null` or an empty string with a reason; omitted fields are left unchanged. The registration number, taxon and name cannot be cleared, and a voucher's site cannot be cleared while a lab sample takes its collection site from it.

Deleting a collection site referenced by a voucher returns HTTP 409. Weather records also prevent automatic deletion of their voucher. Migration `0003` adds the correction log and preserves prior records. Downgrading it drops the log. Back up the archive before upgrading and use a verified snapshot for recovery.
