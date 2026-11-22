# Upgrade notes

Notes for specific database migrations, for instances upgrading from older versions. The general procedure is in
[docs/operations.md](docs/operations.md): stop the app, take a verified backup, then run `python -m alembic upgrade head`.

Migration `0005` adds nullable source and digest fields without modifying existing records or files. Its downgrade removes the original CSV links and upload digests from the database. Keep a verified snapshot of all three components to recover their associations.

Migration `0006` adds holding and scientific attribution fields and makes the legacy registration number optional. Existing UUIDs, registration numbers, account links, and dependent records are preserved. SQLite rebuilds the voucher table within a transaction and checks foreign keys before committing. Use a verified pre-upgrade snapshot for rollback. Downgrade removes the new metadata and is blocked once a voucher has been saved without a legacy registration number.

Migration `0007` adds deposition tables and preserves existing scientific records and file references. The SQLite snapshot includes frozen deposition metadata and files. Downgrade is blocked when deposition records exist. Keep verified backups and preserve the serving URLs for published versions.

Migration `0008` widens location, voucher and taxon text fields and adds collector numbers, verbatim collection dates, type status and georeference details. Existing values are kept. Downgrade is blocked when a value exceeds an earlier length or a new field holds data.

Migration `0009` adds the institution registry and dataset DOIs. It registers each institution code already used by a deposition, named as its latest version or draft names it. Review those entries and add Index Herbariorum and ROR identifiers. Versions published before this migration keep their original relative paths and snapshot digests. Publish a correction to give a deposition absolute identifiers. Downgrade is blocked once a dataset DOI is recorded.

Migration `0015` adds `external_lookup_cache`, which can be emptied at any time, and `external_import`, which records values curators accepted from GBIF, Crossref, ROR and Index Herbariorum. Existing records are unchanged. Downgrade is blocked once `external_import` holds entries.

Migration `0016` adds the ORCID iD, the name ORCID returned and the link date to accounts. Downgrade is blocked while any account has a linked iD. Migration `0017` adds `taxon_literature_compound`, the curator-published LOTUS lists; it holds only copies of Wikidata data that can be published again.

Migration `0019` adds `chemistry_condition_preset`, the run conditions and preparation methods researchers save for reuse; dropping it loses no results. Migration `0020` adds `chemistry_structure` for structures authors supply that PubChem does not have, and co-injection and structure-determination evidence on measurements. Downgrade is blocked once any structure or new evidence is recorded. Install `rdkit` from `requirements.txt` before upgrading.

## Preview migration 0004

With writers stopped and a verified snapshot available, run the preview against revision `0003`. If rehearsing from an earlier revision, first upgrade a restored copy to `0003`.

```powershell
python -m app.visibility_preview
python -m alembic upgrade head
```

The preview reports counts of vouchers, photo records, and previously released studies and profiles affected by the private defaults. It reads the configured database without updating records. Photo counts include metadata rows whose original files may be unavailable.

Migration `0004` retains identifiers, links, files, and chemistry release flags. It withholds every legacy voucher and photo until a curator reviews them individually. Review approved vouchers and their linked chemistry before restoring anonymous access. During rollback to an earlier application version, keep the instance private because the older routes make archive records anonymous again. Use the verified snapshot for recovery and clear any cached public responses from before the upgrade.
