# External lookups

Curators can fill forms from four public registries instead of typing values by hand. Back to the [README](../README.md).

| Provider | Used for | Endpoint in Ex Herbario | Data terms |
| --- | --- | --- | --- |
| GBIF Backbone Taxonomy | Matching a name as written on a label, and importing taxa | `GET /api/taxonomy/gbif-match`, `gbif-search`, `POST import-from-gbif` | CC BY 4.0 |
| Crossref | Filling a bibliography entry from a DOI | `GET /api/publication/doi-lookup` | Metadata CC0; abstracts stay under the publisher's terms |
| ROR | Finding an institution's name and ROR ID | `GET /api/institutions/lookup` | CC0 |
| Index Herbariorum | Finding a herbarium's code | `GET /api/institutions/lookup` | Courtesy of the New York Botanical Garden |
| LOTUS (via Wikidata) | Natural products reported in the literature for a taxon | `GET /api/chemistry/lotus/taxa/{taxon_id}` | Wikidata CC0; cite Rutz et al. 2022 |
| ORCID | Linking an account to the iD ORCID confirms, and signing in with it | `/account/orcid/link`, `/sign-in/orcid` | Public record data CC0 |

All lookups need a curator account. `GET /api/external/providers` lists the providers with their licence, citation and whether they are turned on.

## What a lookup does and does not do

- **A lookup only proposes.** It returns values for a form, with warnings to check and a `source` (provider, licence, citation, link, retrieval date). Nothing is added to the archive until the curator reviews the values and saves the form.
- **Saving records where values came from.** When a curator saves a taxon, publication or institution filled from a lookup, the `external_import` table stores the provider, the external identifier, the curator, the time and, for a publication, which fields were kept from Crossref and which were edited. Records entered by hand have no entry.
- **Published versions don't change.** Deposition snapshots keep the institution name and identifiers they were published with. Citations and taxa are not part of snapshots, and a later lookup never alters a published version or its SHA-256 digest.

## GBIF name matching

`GET /api/taxonomy/gbif-match?name=Porella platiphylla` (optionally `&kingdom=Plantae`) returns GBIF's best match with its `match_type` (`exact`, `fuzzy`, `higherrank` or `none`) and `confidence`, the accepted name when the match is a synonym, alternatives from herbarium kingdoms, and plain-language `review` notes: a different spelling, a match only at genus level, confidence below 95%, a synonym, or several equally good matches. Import the chosen key with `POST /api/taxonomy/import-from-gbif?gbif_key=…&matched_name=…`. In the web app, the taxon picker shows the match for any name of two or more words, with these notes, above the other GBIF names.

## Crossref DOI lookup

`GET /api/publication/doi-lookup?doi=…` accepts a bare DOI, `doi:…` or a `https://doi.org/…` link. It returns the title, journal, year and abstract with markup removed, the authors for reference, and `existing_pub_id` if the DOI is already in the bibliography. Warnings cover a missing abstract or journal, a DOI that is not a journal article, values too long for the form, and the publisher's rights in the abstract. Send the reviewed fields with `"source": {"provider": "crossref", "external_id": "<doi>", "retrieved_at": "…"}` to `POST /api/publication/create-new-publication`. DOIs are compared without case or prefix, so the same article can't be entered twice.

## ROR and Index Herbariorum

`GET /api/institutions/lookup?q=…` searches both registries by name, herbarium code or ROR ID. Each result has `registered_code` when that ROR ID or herbarium code is already registered here, and `errors` names a registry that could not be reached, while the other's results are still shown. Register with `POST /api/institutions` and a `sources` list naming the ROR ID and herbarium code you used; a source that does not match the identifier being registered is refused. The permanent institution code is always the curator's choice.

## LOTUS natural products

`GET /api/chemistry/lotus/taxa/{taxon_id}` finds the taxon in Wikidata through its GBIF key and lists the compounds with a referenced "found in taxon" statement, which is how LOTUS publishes its structure-organism pairs. Each compound has its name, InChIKey, PubChem CID, whether it is in this instance's compound registry, and its references with DOI, title and year. References come from Wikidata's separate scholarly query service, used since its May 2025 split. On a voucher's staff page, curators review the list and can uncheck compounds. `PUT …/published` copies the checked compounds for that taxon, replacing any earlier list, and `DELETE …/published` removes it. The public pages of the taxon's released vouchers then show the list under **Reported in the literature for this taxon**, with its source, retrieval date and citation, and a statement that these compounds were not measured on the voucher. `GET /api/chemistry/public/taxa/{taxon_id}/literature-compounds` serves the same list. Only the taxon itself is queried, not its subspecies or varieties.

## ORCID iDs

Set `ORCID_CLIENT_ID` and `ORCID_CLIENT_SECRET` from a Public API client registered at [orcid.org/developer-tools](https://orcid.org/developer-tools), with `<PUBLIC_BASE_URL>/orcid/callback` as its redirect URI. To rehearse, use a sandbox client and `ORCID_URL=https://sandbox.orcid.org`. Until both values are set, nothing ORCID-related appears.

- **Linking:** on **My work**, *Link your ORCID iD* sends the person to ORCID with the `/authenticate` scope. ORCID returns the authenticated iD and public name. Ex Herbario then asks the person to confirm the link to their account; only then is the iD stored, with an `external_import` entry. The access token is discarded, and the account's own name is not changed. Each iD can belong to only one account, and **Unlink** removes it.
- **Using it:** the iD appears in the curators' account list, and the deposition editor offers *Add me with my ORCID iD*, which fills a contributor row with the confirmed iD. Published versions keep whatever contributors they were published with.
- **Signing in:** with `ORCID_SIGN_IN=true` (the default), the sign-in page offers *Sign in with ORCID* for accounts that already have a linked iD. It never creates an account.
- **Security:** each round trip is tied to a random state value in a signed, short-lived HttpOnly cookie. A missing, mismatched or expired state is refused, and so is a confirmation from a different signed-in account.

## Caching, timeouts and offline use

- Answers are cached in the database: GBIF, Crossref, ROR and LOTUS for 30 days, Index Herbariorum for 7 days (it refreshes weekly), and "not found" for one day. If a provider is unreachable, an expired answer is still served and marked `stale`.
- Each request has a 5-second connect timeout and a read timeout of `EXTERNAL_TIMEOUT_SECONDS` (default 15).
- Set `EXTERNAL_LOOKUPS` to the providers you want (default `gbif,crossref,ror,index_herbariorum,lotus`). Leave it empty for an offline instance; lookups then answer 503 and every other part of Ex Herbario works as before. Turning GBIF off also turns off GBIF taxon search and import.
- Set `EXTERNAL_CONTACT_EMAIL` so Crossref and ROR can contact you about heavy use; it is sent in the User-Agent and, for Crossref, as `mailto`. `ROR_CLIENT_ID` is optional and raises ROR's rate limit.
- Run `python -m app.external.check` to confirm that this machine reaches each enabled provider and that its answers still parse. It queries each provider once, bypassing the cache, and stores nothing.

## Tests

The test suite never reaches the network: an automatic fixture makes every unmocked HTTP request fail as if offline. Provider tests use stored sample answers in `app/external/tests/`.
