# Editing and removing records in Ex Herbario

**Start with the saved voucher.** A curator can register a sheet with its date, collector, site and label, then discover a transcription error as soon as the staff record opens. That page offers **Print label**, **Redetermine** and release controls, but no obvious way to fix the date. **Edit voucher** belongs beside the accession. **Delete voucher** belongs one level deeper, where the curator can see what else uses the record.

## First release — finish the voucher workflow

| Priority | Where | Proposed change | Implementation |
| --- | --- | --- | --- |
| 1 | Staff voucher header | Add **Edit voucher**. Open a prefilled form using the registration labels for holding, accession, collection, collector, field number, exact and verbatim dates, site, storage, type status and verbatim label. Save returns to the same voucher. | Use `PUT /api/specimen/update-specimen` with the specimen ID, changed fields and a correction reason. Keep new determinations in the existing **Redetermine** flow. |
| 2 | Voucher editor, Collection | Offer **Choose another site** for this voucher. Give **Correct shared site** its own link to the directory editor and show how many vouchers use the site before saving there. | Reassignment already accepts a saved site ID. The registration form’s inline site creation and registration date are absent from the update schema. Extend it if those fields are to be offered in the editor. |
| 3 | Voucher record, below Collection | Add **Correction history** with the field, previous and new values, curator, date and reason. Keep the existing determination timeline under Identification. | Read the existing scientific correction journal into the staff page. This makes a corrected date or locality as traceable as a changed determination. |
| 4 | Voucher’s Literature section | Show **Link publication** even when the list is empty. Beside each citation, offer **Unlink from this voucher**. The article stays available to the bibliography and other vouchers. | The specimen–publication create and delete routes exist. Include the relationship ID in each staff row because deletion takes the link ID. |
| 5 | Each voucher photograph | Keep **Approve** and **Withdraw** visible. Add **Delete photograph** to the photo’s actions menu. Confirm against its thumbnail and accession so a curator can identify the exact upload. | Use the existing image delete route. Explain that a linked PlantNet result blocks deletion. Withdrawal already handles the common case of taking a photo out of public view. |
| 6 | Voucher header, **More actions** | Offer **Delete voucher** for an erroneous entry. Name the accession or specimen ID in the confirmation. On success return to voucher search. For an in-use voucher, keep the record open and identify the blocking dependency. | The curator delete route exists and enforces database references. Add a dependency summary for specific guidance. For a released record, offer the existing visibility control first. |

**One backend detail matters before shipping the editor.** The update handler ignores explicit empty values for several fields, including the exact collection date, site and storage. If a curator replaces an assumed day with “May 1972”, saving must clear the old exact date and preserve the label wording. Give omitted fields and explicit clears distinct meanings, and submit only fields the curator changed. Otherwise the editor can report success while the old date still appears.

## Next releases — fix the same problem elsewhere

| Area | Proposed controls | What exists and what is needed |
| --- | --- | --- |
| Saved sample → Vouchers | **Link voucher** beside the list and **Unlink from sample** on each row. | Both API operations exist. Today, **Remove** is available while composing a new sample. On a saved sample, explain why unlinking is blocked when this is the last voucher, it supplies the collection site, or the sample has a released profile. An atomic **Change role** action would need API support to preserve the original link and its recorded identification. |
| Study, sample and preparation | Start with **Edit study details**, then **Edit sample** and **Edit preparation** beside their headings. Allow deletion of an empty private study or an unused entry after showing its contents. | These records have create routes but lack general update and delete routes. Add owner/curator checks. A study with samples, a sample with preparations, or a preparation with runs should identify its dependants before any removal. Record corrections to metadata already used in released work. |
| Imports and runs | Offer **Discard import** beside an unfinished upload. On a confirmed run, put **Correct compound assignment** beside the measurement and preselect that row in the existing correction form. | Discard needs a new endpoint restricted to unconfirmed imports and coordinated with confirmation. Compound correction, its reason and its history already exist. Preserve the uploaded source and measured values. |
| Deposition drafts and published versions | Add **Discard draft** in the draft editor. For a submitted draft, surface the existing **Take back** action first. On a published version, surface **Create correction** and **Withdraw version**. | Discard needs a new endpoint. Distinguish a never-published draft from a correction draft belonging to an existing accession. Discarding the latter should remove only the pending correction. Retain published snapshots internally. The public URL of a withdrawn version should continue to show its withdrawal notice. |
| Directories and accounts | Keep the existing row actions for storage, locations, bibliography and accounts. Bring their **Edit**, **Cancel**, confirmation and refusal patterns into the record pages. | These screens already cover much of the requested behavior. Keep **Deactivate** prominent for accounts with history. Keep the established restrictions on institution codes, box labels and GBIF-backed taxa visible where people manage them. |

## What to verify in the first release

- A curator can register a voucher, reopen it, correct the collector and date, and see the reason and previous values in history. Cancel leaves the saved values intact.
- Reassigning one of two vouchers that share a site affects only the chosen voucher. Correcting the shared site identifies both affected records before save.
- Unlinking a citation preserves the publication. Deleting an unused voucher succeeds. Attempting to delete a voucher with determination history or a linked lab sample explains why it must be retained.
- At phone width, **Edit voucher** is visible beside or directly below the accession. **More actions** is a labeled button reachable by touch and keyboard. Public readers see the catalog view, and the API independently enforces curator permissions.

## Repository references

- Voucher pages and writes — [staff record](../app/web/templates/staff-specimen.html), [registration form](../app/web/templates/curation-vouchers.html), [update schema](../app/specimen/schemas/specimen_schemas.py), [update and deletion behavior](../app/specimen/repository/specimen_repository.py), [specimen and citation routes](../app/specimen/routes.py), [image deletion](../app/image/services/image_services.py).
- Research workflows — [saved sample page](../app/web/templates/staff-study.html), [chemistry routes](../app/chemistry/routes.py), [sample link rules](../app/chemistry/services/chemistry_services.py), [run correction form](../app/web/templates/staff-profile.html), [deposition routes](../app/deposition/routes.py).
- Existing management patterns — [directory actions](../app/web/assets/js/directories.js), [account actions](../app/web/assets/js/accounts.js).
