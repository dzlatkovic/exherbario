# Ex Herbario

[![Tests](https://github.com/dzlatkovic/HERBAR/actions/workflows/tests.yml/badge.svg)](https://github.com/dzlatkovic/HERBAR/actions/workflows/tests.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.165-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Ex Herbario (formerly HERBAR) is an open-source, self-hosted platform for university herbaria and research groups. It keeps voucher specimens together with their taxonomy, collection sites, photos, publications and identification history, links them to lab samples and chemical profiles, and publishes citable, verifiable depositions for journal articles.

- **Vouchers:** registration from labels, GBIF name matching, redetermination history, logged corrections, per-record public release and a Darwin Core Archive for GBIF.
- **Chemistry:** GC-MS and LC-MS profiles imported from your own results table, with compounds identified through PubChem, analysis-ready CSV export, and curator-published natural products reported in the literature (LOTUS).
- **Depositions:** frozen, versioned snapshots with SHA-256 digests, a downloadable ZIP, an offline verifier, optional Zenodo or DataCite DOIs and ORCID-confirmed contributors.
- **Deployment:** one SQLite database plus two file folders, with checked backups and restores.

The repository, Python package, `herbar.db`, the `X-HERBAR-*` headers and the `herbar-deposition` archive format keep the old name so existing installations and archives keep working.

## Quick start

Use Python 3.12 and run these commands from the project root with your virtual environment active.

```powershell
python -m pip install -r requirements.txt
```

Copy `env-template` to `.env` and set `USER_SECRET` to the output of `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Before publishing real records, set `PUBLIC_BASE_URL` to the instance's public origin, such as `https://herbar.example.edu`; published versions record their identifiers under it.

```powershell
python -m alembic upgrade head
python -m app.users.bootstrap admin@example.org Firstname Lastname
python -m uvicorn app.main:app --reload
```

The bootstrap command creates the first administrator and prompts for a password. Then open the [web app](http://127.0.0.1:8000/) or the [API docs](http://127.0.0.1:8000/docs); in the API docs, log in with `POST /api/users/login` and paste the `access_token` into **Authorize**. A fresh database starts empty.

## Using the web app

Visitors browse released vouchers and published depositions. After signing in, **My work** lists your studies, depositions and unfinished imports. Researchers add samples and runs, import results tables and draft depositions, then submit them for review. Curators register and release vouchers, review and publish depositions, and manage directories and accounts under **Curation**.

## Documentation

- [Vouchers, visibility and corrections](docs/vouchers.md): registering vouchers, public release, roles and scientific corrections.
- [Phytochemistry](docs/chemistry.md): samples, preparations, profile import, PubChem compounds and CSV export.
- [Preparing a results table with an AI assistant](docs/ai-extraction.md): the extraction prompt and the import template.
- [Scientific depositions](docs/depositions.md): publishing, verifying archives, DOIs, corrections and withdrawal.
- [Database, backups and migrations](docs/operations.md): storage, backup and restore, and upgrade notes.
- [External lookups](docs/external-lookups.md): optional GBIF, Crossref, ROR, Index Herbariorum and LOTUS lookups, ORCID iDs, caching and offline use.
- [Darwin Core Archive](docs/darwin-core.md): publishing released vouchers to GBIF.

## Tests

Run `python -m pytest`.

## License

Ex Herbario is released under the [MIT License](LICENSE).

## Contact

Dragan Zlatković – [dragan.zlatkovic@gmail.com](mailto:dragan.zlatkovic@gmail.com)
