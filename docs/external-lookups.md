# External lookups

Curators can fill forms from public registries instead of typing values. A lookup only proposes values; nothing is saved until the form is saved, and Ex Herbario records which values came from where.

| Service | Used for |
| --- | --- |
| GBIF | Matching a name as written on a label to a taxon. |
| Crossref | Filling a reference from its DOI. |
| ROR, Index Herbariorum | Institution names, ROR IDs and herbarium codes. |
| LOTUS (Wikidata) | Natural products reported in the literature for a taxon, shown on its released vouchers as literature, not as measurements. |
| PubChem | Identifying compounds in imported results. |
| ORCID | Linking an account to its ORCID iD, and signing in with it. |

## Settings

| Setting | Purpose |
| --- | --- |
| `EXTERNAL_LOOKUPS` | Services to use (default `gbif,crossref,ror,index_herbariorum,lotus`). Empty for an offline instance. |
| `EXTERNAL_CONTACT_EMAIL` | Sent to Crossref and ROR so they can contact you about heavy use. |
| `EXTERNAL_TIMEOUT_SECONDS` | How long to wait for an answer (default 15). |
| `ORCID_CLIENT_ID`, `ORCID_CLIENT_SECRET` | A Public API client from [ORCID developer tools](https://orcid.org/developer-tools), with `<PUBLIC_BASE_URL>/orcid/callback` as redirect URI. ORCID stays hidden until both are set. |

Answers are cached in the database for up to 30 days, and an expired answer is used when a service is unreachable. PubChem requests are paced to PubChem's limits and retried when it is busy.

To check that the server reaches every service, run `python -m app.external.check`, and for PubChem `python -m app.chemistry.pubchem_record --check`.
