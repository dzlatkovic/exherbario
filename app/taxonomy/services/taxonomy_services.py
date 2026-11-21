from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.external.lookups import LookupUnavailable, attribution, cached, record_import, timeout
from app.taxonomy.exceptions import (TaxonDoesNotExistException,
                                     TaxonAlreadyExistException,
                                     TaxonomyServiceException,
                                     GBIFServiceException)
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TAXON_DICT, TaxonRank
from pygbif import species

# GBIF names are shared across kingdoms (Porella is also a bryozoan); a herbarium needs these.
HERBARIUM_KINGDOMS = ("Plantae", "Fungi", "Chromista", "Protozoa")
STATUS_ORDER = {"ACCEPTED": 0, "DOUBTFUL": 1}
# Below this GBIF confidence, or for anything but an exact match, the curator is asked to check the match.
REVIEW_CONFIDENCE = 95
MAX_ALTERNATIVES = 5


def _gbif(key: str, fetch, failure: str):
    """A cached GBIF answer; an unreachable or switched-off GBIF becomes a GBIFServiceException."""
    try:
        return cached("gbif", key, fetch)
    except LookupUnavailable as error:
        raise GBIFServiceException(message=error.message if error.code == 503 else failure, code=error.code) from error


def _expect(kind):
    def check(value):
        if not isinstance(value, kind):
            raise ValueError("GBIF returned an unexpected answer.")
        return value
    return check


def _ranks(classification) -> dict:
    return {str(item.get("rank") or "").upper(): item.get("name")
            for item in classification or [] if isinstance(item, dict)}


def _as_v2(data: dict) -> dict:
    """GBIF v1 match answers are flat; convert them to the v2 shape (usage, acceptedUsage, classification)."""
    if "usage" in data or "diagnostics" in data:
        return data
    ranks = ("kingdom", "phylum", "class", "order", "family", "genus", "species")
    usage = {"key": data.get("usageKey"), "name": data.get("scientificName"), "canonicalName": data.get("canonicalName"),
             "rank": data.get("rank"), "status": data.get("status")} if data.get("usageKey") else None
    accepted = ({"key": data.get("acceptedUsageKey"), "name": data.get("accepted") or data.get("species")}
                if data.get("acceptedUsageKey") else None)
    return {"usage": usage, "acceptedUsage": accepted, "synonym": bool(data.get("synonym")),
            "classification": [{"rank": rank.upper(), "name": data[rank]} for rank in ranks if data.get(rank)],
            "diagnostics": {key: data.get(key) for key in ("matchType", "confidence", "note") if key in data}
            | {"alternatives": [item for item in data.get("alternatives") or [] if isinstance(item, dict)]}}


def _sentence(text: str) -> str:
    """End with one full stop, even after an abbreviated author such as Pfeiff."""
    return text if text.endswith(".") else text + "."


def _review(match, accepted, match_type, confidence, synonym, note, alternatives):
    """Plain-language reasons a curator should look twice before importing a match."""
    if match is None:
        review = (["GBIF found several equally good matches. Choose one of the alternatives, or add the authorship "
                   "to the name."] if alternatives else
                  ["GBIF found no match. Check the spelling or search for the genus."])
        return review + ([f"GBIF: {note}"] if note else [])
    review = []
    if match_type == "FUZZY":
        review.append(_sentence(f"GBIF matched a differently spelled name: {match['name']}"))
    elif match_type == "HIGHERRANK":
        review.append(f"GBIF matched only the {match['rank']} {match['name']}, not the full name.")
    elif match_type != "EXACT":
        review.append(f"GBIF reports a {match_type.lower()} match.")
    if isinstance(confidence, (int, float)) and confidence < REVIEW_CONFIDENCE:
        review.append(f"GBIF's confidence in this match is {confidence}%.")
    if synonym:
        review.append(_sentence(f"{match['name']} is a synonym in GBIF"
                                + (f"; importing it links the accepted name {accepted['name']}" if accepted else "")))
    if match["kingdom"] and match["kingdom"] not in HERBARIUM_KINGDOMS:
        review.append(f"The match is in kingdom {match['kingdom']}, which herbaria do not usually hold.")
    if not match["importable"]:
        review.append("This match can't be imported: its rank is not one Ex Herbario records.")
    if note:
        review.append(f"GBIF: {note}")
    return review


class TaxonomyService:
    @staticmethod
    def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                if taxon_data.parent_taxon_key is not None:
                    parent_taxon = repository.read_taxon_by_taxon_id(taxon_data.parent_taxon_key)
                    if not parent_taxon:
                        raise TaxonDoesNotExistException(
                            code=404,
                            message=f"Parent taxon with id: "
                                    f"{taxon_data.parent_taxon_key} does not exist in the database."
                        )
                return repository.create_taxon(taxon_data, taxon_rank)
        except Exception as error:
            raise error

    @staticmethod
    def read_taxon_by_gbif_key(gbif_key: str):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_gbif_key(gbif_key)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with gbif key: {gbif_key} does not exist in the database."
                    )
                return taxon
        except Exception as error:
            raise error

    @staticmethod
    def read_taxon_by_taxon_id(taxon_id: str):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_taxon_id(taxon_id)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with id: {taxon_id} does not exist in the database."
                    )
                return taxon
        except Exception as error:
            raise error

    @staticmethod
    def _usage(gbif_key: str):
        return _gbif(f"usage:{gbif_key}", lambda: _expect(dict)(species.name_usage(key=gbif_key, timeout=timeout())),
                     "Unable to retrieve this taxon from GBIF.")

    @staticmethod
    def _fetch_taxon(gbif_key: str):
        data = TaxonomyService._usage(gbif_key).data
        if (not isinstance(data, dict) or str(data.get("key")) != gbif_key
                or not isinstance(data.get("scientificName"), str)):
            raise GBIFServiceException(message="GBIF returned an unexpected taxon.", code=502)
        return data

    @staticmethod
    def _add_taxon(repository, data, rank, parent_id):
        details = TaxonomySchemaIn(
            taxon_name=data.get("scientificName"),
            gbif_key=str(data["key"]),
            parent_taxon_key=parent_id,
            common_name=data.get("vernacularName"),
            authority=data.get("authorship"),
        )
        return repository.add_taxon(details, rank)

    @staticmethod
    def create_taxon_from_gbif_data(gbif_key: str):
        gbif_key = str(gbif_key)
        data = TaxonomyService._fetch_taxon(gbif_key)
        rank = TAXON_DICT.get(data.get("rank"))
        if rank is None:
            raise TaxonomyServiceException(message="This GBIF rank is unsupported.", code=422)
        try:
            with SessionLocal(expire_on_commit=False) as db, db.begin():
                repo = TaxonomyRepository(db)
                if repo.read_taxon_by_gbif_key(gbif_key):
                    raise TaxonAlreadyExistException(message="This GBIF taxon already exists.", code=409)
                parent_id = None
                if rank != TaxonRank.KINGDOM:
                    parent = repo.read_taxon_by_gbif_key(str(data.get("parentKey")))
                    if parent is None:
                        raise TaxonDoesNotExistException(
                            message="The GBIF parent is missing. Import the hierarchy first.", code=404
                        )
                    parent_id = parent.taxon_id
                return TaxonomyService._add_taxon(repo, data, rank, parent_id)
        except IntegrityError as error:
            raise TaxonomyServiceException(message="The GBIF taxon could not be stored.", code=409) from error

    @staticmethod
    def search_gbif(query: str, limit: int = 10):
        """Names from the GBIF backbone for a lookup field, accepted names first, marked when already imported."""
        found = _gbif(f"suggest:{' '.join(query.lower().split())}",
                      lambda: _expect(list)(species.name_suggest(q=query, limit=40, timeout=timeout())),
                      "GBIF can't be reached right now. Taxa already in this herbarium are still listed.").data
        rows = [item for item in found if isinstance(item, dict) and item.get("key") is not None
                and item.get("kingdom") in HERBARIUM_KINGDOMS and item.get("rank") in TAXON_DICT
                and isinstance(item.get("scientificName"), str)]
        rows.sort(key=lambda item: STATUS_ORDER.get(item.get("status"), 2))
        rows = rows[:limit]
        with SessionLocal() as db:
            repository = TaxonomyRepository(db)
            local = {str(item["key"]): repository.read_taxon_by_gbif_key(str(item["key"])) for item in rows}
        return [{
            "gbif_key": str(item["key"]), "name": item["scientificName"], "canonical_name": item.get("canonicalName"),
            "rank": item["rank"].lower(), "status": (item.get("status") or "").lower(),
            "kingdom": item.get("kingdom"), "phylum": item.get("phylum"), "family": item.get("family"),
            "taxon_id": local[str(item["key"])].taxon_id if local[str(item["key"])] else None,
        } for item in rows]

    @staticmethod
    def match_gbif(name: str, kingdom: str | None = None):
        """Match a name as written (on a label or in a list) to the GBIF Backbone. Only the GBIF answer is
        cached; the curator reviews the match and imports it with import_from_gbif."""
        name = " ".join(name.split())
        result = _gbif(f"match:{(kingdom or '').lower()}:{name.lower()}",
                       lambda: _expect(dict)(species.name_backbone(scientificName=name, kingdom=kingdom, verbose=True,
                                                                   timeout=timeout())),
                       "GBIF can't be reached right now, so the name can't be matched.")
        data = _as_v2(result.data)
        diagnostics = data.get("diagnostics") or {}
        match_type = str(diagnostics.get("matchType") or "NONE").upper()
        confidence = diagnostics.get("confidence")
        usage = data.get("usage") if match_type != "NONE" and isinstance(data.get("usage"), dict) else None
        synonym = bool(usage and (data.get("synonym") or str(usage.get("status") or "").upper() == "SYNONYM"))
        accepted = data.get("acceptedUsage") if synonym and isinstance(data.get("acceptedUsage"), dict) else None
        ranks = _ranks(data.get("classification"))

        with SessionLocal() as db:
            repository = TaxonomyRepository(db)

            def entry(item, item_ranks):
                key = str(item.get("key") or "")
                local = repository.read_taxon_by_gbif_key(key) if key else None
                rank = str(item.get("rank") or "").upper()
                return {"gbif_key": key, "name": item.get("name"), "canonical_name": item.get("canonicalName"),
                        "authorship": item.get("authorship"), "rank": rank.lower(),
                        "status": str(item.get("status") or "").lower(), "kingdom": item_ranks.get("KINGDOM"),
                        "family": item_ranks.get("FAMILY"), "importable": key.isdigit() and rank in TAXON_DICT,
                        "taxon_id": local.taxon_id if local else None,
                        "url": f"https://www.gbif.org/species/{key}" if key else None}

            match = entry(usage, ranks) if usage else None
            accepted_entry = entry(accepted, ranks) if accepted else None
            alternatives = []
            for item in diagnostics.get("alternatives") or []:
                item = _as_v2(item) if isinstance(item, dict) else {}
                item_ranks = _ranks(item.get("classification"))
                if (not isinstance(item.get("usage"), dict)
                        or item_ranks.get("KINGDOM") not in (None, *HERBARIUM_KINGDOMS)):
                    continue
                alternative = entry(item["usage"], item_ranks)
                alternative["confidence"] = (item.get("diagnostics") or {}).get("confidence")
                if match is None or alternative["gbif_key"] != match["gbif_key"]:
                    alternatives.append(alternative)

        return {"query": name, "kingdom": kingdom, "match_type": match_type.lower(), "confidence": confidence,
                "synonym": synonym, "match": match, "accepted": accepted_entry,
                "alternatives": alternatives[:MAX_ALTERNATIVES],
                "review": _review(match, accepted_entry, match_type, confidence, synonym, diagnostics.get("note"),
                                  alternatives),
                "source": attribution(result, match["url"] if match else None)}

    @staticmethod
    def import_from_gbif(gbif_key: str, actor_id: str | None = None, matched_name: str | None = None):
        """Add a GBIF taxon with its missing parents and return the local record. A synonym is linked to
        its accepted name, so the determination points at the current concept; the note says so.
        When taxa are added, the curator's confirmation is recorded with where they came from."""
        key = str(gbif_key)
        data = TaxonomyService._fetch_taxon(key)
        note = None
        if data.get("synonym") and data.get("acceptedKey"):
            key = str(data["acceptedKey"])
            note = (f"{data['scientificName']} is a synonym in GBIF; the accepted name "
                    f"{data.get('accepted') or key} was linked instead.")
        created = TaxonomyService.build_taxonomic_tree(key)
        with SessionLocal(expire_on_commit=False) as db:
            taxon = TaxonomyRepository(db).read_taxon_by_gbif_key(key)
            if taxon is None:
                raise TaxonomyServiceException(message="The GBIF taxon could not be added.", code=409)
            if created and actor_id:
                fields = {"added": [{"gbif_key": item.gbif_key, "name": item.taxon_name,
                                     "rank": item.taxon_rank.value} for item in created]}
                if key != str(gbif_key):
                    fields["requested_synonym"] = {"gbif_key": str(gbif_key), "name": data.get("scientificName")}
                if matched_name:
                    fields["matched_name"] = matched_name
                record_import(db, provider="gbif", external_id=key, record_type="taxon", record_id=taxon.taxon_id,
                              fields=fields, confirmed_by=actor_id,
                              retrieved_at=TaxonomyService._usage(key).retrieved_at)
                db.commit()
        return taxon, note

    @staticmethod
    def build_taxonomic_tree(gbif_key: str):
        key = str(gbif_key)
        ancestors = []
        seen = set()
        try:
            with SessionLocal(expire_on_commit=False) as db, db.begin():
                repository = TaxonomyRepository(db)
                parent_id = None
                while key:
                    if key in seen:
                        raise GBIFServiceException(message="GBIF returned a cyclic taxonomy.", code=502)
                    seen.add(key)
                    existing = repository.read_taxon_by_gbif_key(key)
                    if existing is not None:
                        parent_id = existing.taxon_id
                        break
                    data = TaxonomyService._fetch_taxon(key)
                    rank = TAXON_DICT.get(data.get("rank"))
                    if rank is None and len(seen) == 1:
                        raise TaxonomyServiceException(message="This GBIF rank is unsupported.", code=422)
                    if rank is not None:
                        ancestors.append((data, rank))
                    if rank == TaxonRank.KINGDOM:
                        break
                    parent_key = data.get("parentKey")
                    if parent_key is None:
                        raise TaxonomyServiceException(message="GBIF taxonomy has no supported root.", code=422)
                    key = str(parent_key)

                created = []
                for data, rank in reversed(ancestors):
                    taxon = TaxonomyService._add_taxon(repository, data, rank, parent_id)
                    created.append(taxon)
                    parent_id = taxon.taxon_id
                return created
        except IntegrityError as error:
            raise TaxonomyServiceException(
                message="The GBIF hierarchy could not be stored. Retry if another import is in progress.", code=409
            ) from error

    @staticmethod
    def delete_taxon(taxon_id):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_taxon_id(taxon_id)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with id: {taxon_id} does not exist in the database."
                    )
                return repository.delete_taxon(taxon_id)
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_by_taxon(taxon_name: str):
        with SessionLocal() as db:
            specimens = TaxonomyRepository(db).get_specimens_by_taxon_name(taxon_name)
            if specimens is None:
                raise TaxonDoesNotExistException(message=f"No taxon with name {taxon_name} was found.", code=404)
            return specimens
