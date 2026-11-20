"""DataCite Metadata Schema 4 attributes for a frozen deposition version.

The output is the ``attributes`` object of the DataCite REST API, so an institution with a DataCite
membership can register a DOI from it directly. Zenodo mirroring uses the same frozen snapshot.
"""


def _creator(contributor):
    creator = {"name": contributor["name"], "nameType": "Personal"}
    if contributor.get("orcid"):
        creator["nameIdentifiers"] = [{
            "nameIdentifier": f"https://orcid.org/{contributor['orcid']}",
            "nameIdentifierScheme": "ORCID", "schemeUri": "https://orcid.org",
        }]
    return creator


def datacite_metadata(snapshot, published_at, article_dois, dataset_doi=None):
    identifiers = snapshot.get("institution_identifiers") or {}
    publisher = {"name": snapshot["institution_name"]}
    if identifiers.get("ror"):
        publisher.update(publisherIdentifier=identifiers["ror"], publisherIdentifierScheme="ROR",
                         schemeUri="https://ror.org/")
    related = [{"relatedIdentifier": doi, "relatedIdentifierType": "DOI", "relationType": "IsSupplementTo"}
               for doi in article_dois]
    if snapshot.get("supersedes"):
        related.append({"relatedIdentifier": snapshot["supersedes"], "relatedIdentifierType": "URL",
                        "relationType": "IsNewVersionOf"})
    attributes = {
        "types": {"resourceTypeGeneral": "Dataset", "resourceType": "Voucher-linked scientific deposition"},
        "titles": [{"title": snapshot["title"]}],
        "creators": [_creator(contributor) for contributor in snapshot["contributors"]],
        "publisher": publisher,
        "publicationYear": str(published_at.year),
        "dates": [{"date": published_at.date().isoformat(), "dateType": "Issued"}],
        "version": str(snapshot["version"]),
        "url": snapshot["identifier"],
        "alternateIdentifiers": [{
            "alternateIdentifier": f"{snapshot['institution']} {snapshot['accession']} v{snapshot['version']}",
            "alternateIdentifierType": "HERBAR accession",
        }],
        "rightsList": [{"rights": snapshot["license"]}],
        "relatedIdentifiers": related,
        "subjects": [{"subject": name} for name in sorted({
            (voucher["determination"].get("taxonomy") or {}).get("name") or voucher["determination"]["name_as_recorded"]
            for voucher in snapshot["vouchers"]
        } - {None})],
    }
    if snapshot.get("description"):
        attributes["descriptions"] = [{"description": snapshot["description"], "descriptionType": "Abstract"}]
    if dataset_doi:
        attributes["doi"] = dataset_doi
    return attributes
