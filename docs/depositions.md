# Scientific depositions

A deposition is the data behind a paper, published as a fixed, citable version: vouchers, samples, preparations, methods and measurements, with a downloadable archive that anyone can verify.

## Create and publish

1. A curator registers the institution once (**Curation → Directories**), with its Index Herbariorum code and ROR ID where they exist. Its code becomes the namespace of the deposition's accession number.
2. The researcher creates a deposition under **My work**: title and description (usually the paper's title and abstract), licence (CC BY 4.0 is recommended), contributors with optional ORCID iDs, and the runs, preparations and vouchers to include.
3. **Validate and preview** shows exactly what will be published, and lists the private studies, runs and vouchers that publishing will release.
4. The researcher chooses **Submit for review**. A curator checks the preview and chooses **Publish version**.

The published version is frozen: later edits to live records do not change it. Public pages never show exact localities, labels or account details; collector and determiner names appear only if the deposition includes them.

## Cite and verify

Each version has a public page at `/depositions/{institution}/{accession}/versions/{number}` with its citation, credits, methods, files and SHA-256 digest. **Download version ZIP** gives the frozen record, the source files and a manifest of digests. Anyone can check the archive offline:

```
python -m app.deposition.verify_archive deposition-v1.zip --snapshot-sha256 <digest>
```

## DOIs

To get a DOI, mirror a version to Zenodo, which receives the same ZIP:

```
python -m app.deposition.mirror_zenodo <institution> <accession> <version> --curator curator@example.org
```

Set `ZENODO_TOKEN` first, and rehearse with `ZENODO_URL=https://sandbox.zenodo.org` and `--dry-run`. An institution with its own DataCite membership can register a DOI from the version's `datacite.json` instead. The article's DOI can be linked to a version once the paper is out.

## Correct or withdraw

- **Start a correction** opens the published content as a new draft. Give a reason, edit, and publish: the accession stays, a new version is created, and earlier versions remain citable with a note that they were superseded.
- On the version's page, a curator chooses **Withdraw version** and gives a public reason. Its page then shows a withdrawal notice and its files are no longer offered; the record itself is kept.
