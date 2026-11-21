# Editing and removing records in Ex Herbario

**Start with the saved voucher.** A curator can register a sheet with its date, collector, site and label, then discover a transcription error as soon as the staff record opens. That page offers **Print label**, **Redetermine** and release controls, but no obvious way to fix the date. **Edit voucher** belongs beside the accession. **Delete voucher** belongs one level deeper, where the curator can see what else uses the record.

## First release — finish the voucher workflow

| Priority | Where | Proposed change | Implementation |
| --- | --- | --- | --- |
| 1 | Staff voucher header | Add **Edit voucher**. Open a prefilled form using the registration labels for holding, accession, collection, collector, field number, exact and verbatim dates, site, storage, type status and verbatim label. Save returns to the same voucher. | Use `PUT /api/specimen/update-specimen` with the specimen ID, changed fields and a correction reason. The API already refuses a metadata change without a reason, so the form should ask for one up front rather than after a failed save. Keep new determinations in the existing **Redetermine** flow: the editor must not send `taxon_id` or `subnomen`, even though the endpoint still accepts them. |
| 2 | Voucher editor, Collection | Offer **Choose another site** for this voucher. Give **Correct shared site** its own link to the directory editor and show how many vouchers use the site before saving there. | Reassignment already accepts a saved site ID. The registration form’s inline site creation and registration date are absent from the update schema. Extend it if those fields are to be offered in the editor. |
| 3 | Voucher record, below Collection | Add **Correction history** with the field, previous and new values, curator, date and reason. Keep the existing determination timeline under Identification. | Read the existing scientific correction journal into the staff page. This makes a corrected date or locality as traceable as a changed determination. |
| 4 | Voucher’s Literature section | Show **Link publication** even when the list is empty. Beside each citation, offer **Unlink from this voucher** for a link made in error. The article stays available to the bibliography and other vouchers. Unlinking asks for a reason and is logged, because a citation is how a reader finds the voucher behind a published result. | The specimen–publication create and delete routes exist. Include the relationship ID in each staff row because deletion takes the link ID. |
| 5 | Each voucher photograph | Keep **Approve** and **Withdraw** visible. Add **Delete photograph** to the photo’s actions menu. Confirm against its thumbnail and accession so a curator can identify the exact upload. | Use the existing image delete route. Explain that a linked PlantNet result blocks deletion. Withdrawal already handles the common case of taking a photo out of public view. Offer deletion only for a photograph that was never approved for public view; an approved one is withdrawn instead. |
| 6 | Voucher header, **More actions** | Offer **Delete voucher** only for an erroneous entry that has never been public, is not cited and has no history (see *Records that are kept*). Name the accession or specimen ID in the confirmation. On success return to voucher search. Otherwise keep the record open, say why it is kept, and offer withdrawal from public view instead. | The curator delete route exists and enforces database references, but it does not check release state: a public voucher with no linked rows can be deleted outright and its public page disappears. Refuse deletion of any voucher that has been public, and add a dependency summary for specific guidance. Do not tell curators to remove images or citations first. |

**Clearing fields — fixed.** The update handler used to ignore explicit empty values for the exact collection date, site, storage, collector and verifier, so an editor could report success while the old date still appeared. It now gives omitted fields and explicit clears distinct meanings:

- `collection_date`, `field_loc_id`, `storage_id`, `collected_by` and `verified_by` are cleared by `null` or an empty string. A clear is a correction, so it needs a reason and is logged with the previous value.
- `reg_no`, `taxon_id` and `subnomen` cannot be cleared; the request is refused with 400 instead of being ignored.
- A voucher's site cannot be cleared while a lab sample takes its collection site from that voucher (409). Choosing another site is still allowed.

The editor should submit only the fields the curator changed. To stop two curators overwriting each other, the form should also send the record state it was opened with, and the API should refuse the save (409) if the voucher changed since then.

## Records that are kept

Ex Herbario publishes records that journal articles cite, so removal is the exception. These are never deleted, only corrected or withdrawn from public view:

- a voucher that has ever been public, is cited by a publication, belongs to a deposition, is linked to a lab sample, or has a determination or correction history;
- a photograph that has been approved for public view;
- a confirmed run, its measurements and its uploaded source file;
- a published deposition version, which keeps its URL and shows a withdrawal notice.

Deletion is for mistakes caught before anyone else could rely on the record: an unused voucher entered twice, a photo uploaded to the wrong sheet, an unconfirmed import, a never-submitted draft.

## Corrections after publication

A published deposition snapshot is frozen, so it keeps the voucher's old date or site after a correction. That is correct, but readers should be told. Public chemistry and deposition pages already flag vouchers that were redetermined after linking; add the same flag for vouchers **corrected since deposition**, driven by the correction log, with the corrected fields and the date. The snapshot and its SHA-256 digest do not change.

## Next releases — fix the same problem elsewhere

| Area | Proposed controls | What exists and what is needed |
| --- | --- | --- |
| Saved sample → Vouchers | **Link voucher** beside the list and **Unlink from sample** on each row. | Both API operations exist. Today, **Remove** is available while composing a new sample. On a saved sample, explain why unlinking is blocked when this is the last voucher, it supplies the collection site, or the sample has a released profile. An atomic **Change role** action would need API support to preserve the original link and its recorded identification. |
| Study, sample and preparation | Start with **Edit study details**, then **Edit sample** and **Edit preparation** beside their headings. Allow deletion of an empty private study or an unused entry after showing its contents. | These records have create routes but lack general update and delete routes. Add owner/curator checks. A study with samples, a sample with preparations, or a preparation with runs should identify its dependants before any removal. Metadata behind a released profile is changed only with a logged reason, and the change reaches readers through a deposition correction, not by silently altering what they already cite. |
| Imports and runs | Offer **Discard import** beside an unfinished upload. On a confirmed run, put **Correct compound assignment** beside the measurement and preselect that row in the existing correction form. | Discard needs a new endpoint restricted to unconfirmed imports and coordinated with confirmation. Compound correction, its reason and its history already exist. Preserve the uploaded source and measured values. |
| Deposition drafts and published versions | Add **Discard draft** in the draft editor. For a submitted draft, surface the existing **Take back** action first. On a published version, surface **Create correction** and **Withdraw version**. | Discard needs a new endpoint. Distinguish a never-published draft from a correction draft belonging to an existing accession. Discarding the latter should remove only the pending correction. Retain published snapshots internally. The public URL of a withdrawn version should continue to show its withdrawal notice. |
| Directories and accounts | Keep the existing row actions for storage, locations, bibliography and accounts. Bring their **Edit**, **Cancel**, confirmation and refusal patterns into the record pages. | These screens already cover much of the requested behavior. Keep **Deactivate** prominent for accounts with history. Keep the established restrictions on institution codes, box labels and GBIF-backed taxa visible where people manage them. |

## What to verify in the first release

- A curator can register a voucher, reopen it, correct the collector and date, and see the reason and previous values in history. Cancel leaves the saved values intact.
- Reassigning one of two vouchers that share a site affects only the chosen voucher. Correcting the shared site identifies both affected records before save.
- Replacing an exact date with “May 1972” clears the date and keeps the label wording. Omitted fields keep their values.
- Saving a correction without a reason is refused, and the form asks for the reason before saving.
- Unlinking a citation preserves the publication and records the reason. Deleting an unused, never-public voucher succeeds. Deleting a voucher that has been public, is cited, or has determination history or a linked lab sample is refused with the reason, and the page offers withdrawal instead.
- A voucher in a published deposition, corrected afterwards, shows **corrected since deposition** on its public pages, and the deposition's snapshot digest is unchanged.
- A save based on a stale form is refused rather than overwriting another curator's change.
- At phone width, **Edit voucher** is visible beside or directly below the accession. **More actions** is a labeled button reachable by touch and keyboard. Public readers see the catalog view, and the API independently enforces curator permissions.

## Repository references

- Voucher pages and writes — [staff record](../app/web/templates/staff-specimen.html), [registration form](../app/web/templates/curation-vouchers.html), [update schema](../app/specimen/schemas/specimen_schemas.py), [update and deletion behavior](../app/specimen/repository/specimen_repository.py), [specimen and citation routes](../app/specimen/routes.py), [image deletion](../app/image/services/image_services.py).
- Research workflows — [saved sample page](../app/web/templates/staff-study.html), [chemistry routes](../app/chemistry/routes.py), [sample link rules](../app/chemistry/services/chemistry_services.py), [run correction form](../app/web/templates/staff-profile.html), [deposition routes](../app/deposition/routes.py).
- Existing management patterns — [directory actions](../app/web/assets/js/directories.js), [account actions](../app/web/assets/js/accounts.js).
