"""External registries curators can query, with the attribution shown wherever their data is used."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    key: str
    name: str
    homepage: str
    license: str
    citation: str
    ttl_days: int


PROVIDERS = {
    "gbif": Provider(
        "gbif", "GBIF Backbone Taxonomy", "https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c",
        "CC BY 4.0", "GBIF Secretariat. GBIF Backbone Taxonomy. Checklist dataset https://doi.org/10.15468/39omei",
        30,
    ),
    "crossref": Provider(
        "crossref", "Crossref", "https://www.crossref.org/",
        "Bibliographic metadata: CC0 1.0; abstracts remain under the publisher's terms",
        "Metadata retrieved from Crossref (https://api.crossref.org)", 30,
    ),
    "ror": Provider(
        "ror", "Research Organization Registry (ROR)", "https://ror.org/", "CC0 1.0",
        "Research Organization Registry (https://ror.org)", 30,
    ),
    "index_herbariorum": Provider(
        "index_herbariorum", "Index Herbariorum", "https://sweetgum.nybg.org/science/ih/",
        "Data courtesy of the New York Botanical Garden",
        "Thiers, B. Index Herbariorum: A Global Directory of Public Herbaria and Associated Staff. "
        "New York Botanical Garden's Virtual Herbarium. https://sweetgum.nybg.org/science/ih/",
        7,  # IH refreshes its API weekly
    ),
}

# How long a "not found" answer is remembered, so a typo does not query the provider on every keystroke.
NOT_FOUND_TTL_DAYS = 1
