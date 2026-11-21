"""Darwin Core Archive of released vouchers, for GBIF and other aggregators.

Built from live released records with the public catalog's rules: only released vouchers, location only when
the voucher's release allows its region, no exact coordinates, no staff or collector names. Released chemistry
is added as measurements. Deposition snapshots are never read or changed; each published version keeps its own
frozen record.
"""

import csv
import io
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog import public_location
from app.chemistry.models import SampleVoucher
from app.chemistry.repository import ChemistryRepository
from app.config import settings
from app.field_loc.models import FieldLoc
from app.image.models import Image
from app.publication.models import Publication
from app.specimen.models import Specimen, SpecimenPublication
from app.taxonomy.models import Taxonomy

DWC = "http://rs.tdwg.org/dwc/terms/"
DC = "http://purl.org/dc/terms/"
LICENSES = {
    "CC0-1.0": ("http://creativecommons.org/publicdomain/zero/1.0/legalcode", "Public Domain (CC0 1.0)"),
    "CC-BY-4.0": ("http://creativecommons.org/licenses/by/4.0/legalcode", "Creative Commons Attribution (CC-BY) 4.0"),
    "CC-BY-NC-4.0": ("http://creativecommons.org/licenses/by-nc/4.0/legalcode",
                     "Creative Commons Attribution Non Commercial (CC-BY-NC) 4.0"),
}
OCCURRENCE_TERMS = [
    ("occurrenceID", DWC), ("basisOfRecord", DWC), ("institutionCode", DWC), ("collectionCode", DWC),
    ("catalogNumber", DWC), ("otherCatalogNumbers", DWC), ("recordNumber", DWC), ("eventDate", DWC),
    ("verbatimEventDate", DWC), ("scientificName", DWC), ("verbatimIdentification", DWC), ("taxonRank", DWC),
    ("taxonID", DWC), ("kingdom", DWC), ("phylum", DWC), ("class", DWC), ("order", DWC), ("family", DWC),
    ("genus", DWC), ("dateIdentified", DWC), ("typeStatus", DWC), ("country", DWC), ("stateProvince", DWC),
    ("informationWithheld", DWC), ("associatedReferences", DWC), ("associatedMedia", DWC), ("license", DC),
    ("references", DC),
]
MOF_TERMS = ["measurementID", "measurementType", "measurementValue", "measurementUnit", "measurementMethod",
             "measurementRemarks"]
MAX_RECORDS = 100_000
TYPE_STATUS = {"type": "type"}


def _base() -> str:
    base = settings.PUBLIC_BASE_URL.strip().rstrip("/")
    if not base.startswith(("https://", "http://")):
        raise HTTPException(409, "Set PUBLIC_BASE_URL to this instance's public address before exporting Darwin Core: "
                                 "occurrence IDs are built from it and must not change.")
    return base


def _classification(db: Session, taxon: Taxonomy | None) -> dict:
    ranks, seen = {}, set()
    while taxon is not None and taxon.taxon_id not in seen:
        seen.add(taxon.taxon_id)
        ranks[taxon.taxon_rank.value] = taxon.taxon_name
        taxon = db.get(Taxonomy, taxon.parent_taxon_key) if taxon.parent_taxon_key else None
    return ranks


def _genus_name(value: str | None) -> str | None:
    return value.split()[0] if value else None


def _vouchers(db: Session, holding_institution: str, collection: str):
    query = (select(Specimen, Taxonomy, FieldLoc)
             .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
             .outerjoin(FieldLoc, FieldLoc.field_loc_id == Specimen.field_loc_id)
             .where(Specimen.is_public.is_(True)).order_by(Specimen.specimen_id))
    if holding_institution:
        query = query.where(Specimen.holding_institution == holding_institution)
    if collection:
        query = query.where(Specimen.collection == collection)
    return db.execute(query.limit(MAX_RECORDS + 1)).all()


def _occurrence(db, base, license_url, specimen, taxon, location, references, media):
    ranks = _classification(db, taxon)
    region = public_location(specimen, location)
    withheld = ("Locality and coordinates withheld; country and region given." if region
                else "Location withheld.")
    accession = specimen.accession or specimen.reg_no
    return {
        "occurrenceID": f"{base}/specimens/{specimen.specimen_id}", "basisOfRecord": "PreservedSpecimen",
        "institutionCode": specimen.holding_institution, "collectionCode": specimen.collection,
        "catalogNumber": accession,
        "otherCatalogNumbers": specimen.reg_no if specimen.accession and specimen.reg_no else None,
        "recordNumber": specimen.collector_number,
        "eventDate": specimen.collection_date.isoformat() if specimen.collection_date else None,
        "verbatimEventDate": specimen.verbatim_collection_date,
        "scientificName": taxon.taxon_name if taxon else specimen.subnomen,
        "verbatimIdentification": specimen.subnomen,
        "taxonRank": taxon.taxon_rank.value if taxon else None,
        "taxonID": f"https://www.gbif.org/species/{taxon.gbif_key}" if taxon else None,
        "kingdom": ranks.get("kingdom"), "phylum": ranks.get("phylum"), "class": ranks.get("class"),
        "order": ranks.get("order"), "family": ranks.get("family"), "genus": _genus_name(ranks.get("genus")),
        "dateIdentified": specimen.determination_date.isoformat() if specimen.determination_date else None,
        "typeStatus": specimen.type_status,
        "country": region["country"] if region else None, "stateProvince": region["region"] if region else None,
        "informationWithheld": withheld,
        "associatedReferences": " | ".join(references) or None,
        "associatedMedia": " | ".join(media) or None,
        "license": license_url, "references": f"{base}/specimens/{specimen.specimen_id}",
    }


def _measurements(db, base, occurrence_ids):
    """Released measurements for each released voucher linked to the measured sample."""
    repository = ChemistryRepository(db)
    rows = []
    for specimen_id, occurrence_id in occurrence_ids.items():
        for profile, _preparation, sample in repository.list_released_specimen_profiles(specimen_id):
            role = db.scalar(select(SampleVoucher.role).where(SampleVoucher.sample_id == sample.id,
                                                              SampleVoucher.specimen_id == specimen_id))
            method = "; ".join(part for part in (profile.technique, profile.analytical_method) if part)
            for measurement, compound in repository.list_measurements([profile.id]):
                if measurement.value is None and not measurement.qualifier:
                    continue  # not detected or not measured: nothing was found to report
                name = compound.title if compound else measurement.feature
                remarks = [f"Profile {base}/profiles/{profile.id}", f"sample {sample.code}",
                           f"voucher role: {(role or '').replace('_', ' ')}"]
                if measurement.cid:
                    remarks.append(f"PubChem CID {measurement.cid}")
                if measurement.ri_exp is not None:
                    remarks.append(f"RI {measurement.ri_exp:g}")
                rows.append({
                    "coreid": occurrence_id,
                    "measurementID": f"{base}/profiles/{profile.id}#{measurement.feature}",
                    "measurementType": f"{profile.measurement_basis.replace('_', ' ')} of {name}",
                    "measurementValue": f"{measurement.value:g}" if measurement.value is not None else measurement.qualifier,
                    "measurementUnit": profile.unit, "measurementMethod": method or None,
                    "measurementRemarks": "; ".join(remarks),
                })
    return rows


def _table(header, rows) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
    writer.writerow(header)
    for row in rows:
        writer.writerow(["" if value is None else " ".join(str(value).split()) for value in row])
    return output.getvalue().encode("utf-8")


def _meta(with_measurements: bool) -> str:
    fields = "\n".join(f'    <field index="{index}" term="{namespace}{term}"/>'
                       for index, (term, namespace) in enumerate(OCCURRENCE_TERMS))
    extension = ""
    if with_measurements:
        mof = "\n".join(f'    <field index="{index + 1}" term="{DWC}{term}"/>' for index, term in enumerate(MOF_TERMS))
        extension = f"""
  <extension encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" fieldsEnclosedBy="" ignoreHeaderLines="1" rowType="{DWC}MeasurementOrFact">
    <files><location>measurementorfact.txt</location></files>
    <coreid index="0"/>
{mof}
  </extension>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/" metadata="eml.xml">
  <core encoding="UTF-8" fieldsTerminatedBy="\\t" linesTerminatedBy="\\n" fieldsEnclosedBy="" ignoreHeaderLines="1" rowType="{DWC}Occurrence">
    <files><location>occurrence.txt</location></files>
    <id index="0"/>
{fields}
  </core>{extension}
</archive>
"""


def _eml(base, license_key, count, filters) -> str:
    url, label = LICENSES[license_key]
    title = settings.DWC_DATASET_TITLE.strip() or "Ex Herbario voucher specimens"
    if filters:
        title += " (" + ", ".join(filters) + ")"
    description = settings.DWC_DATASET_DESCRIPTION.strip() or (
        "Herbarium voucher specimens released by this Ex Herbario instance, with released phytochemical measurements.")
    publisher = settings.DWC_PUBLISHER.strip() or base
    contact = settings.DWC_CONTACT_EMAIL.strip() or settings.EXTERNAL_CONTACT_EMAIL.strip()
    party = f"""<organizationName>{escape(publisher)}</organizationName>{f"<electronicMailAddress>{escape(contact)}</electronicMailAddress>" if contact else ""}"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="https://eml.ecoinformatics.org/eml-2.2.0 https://eml.ecoinformatics.org/eml-2.2.0/eml.xsd"
  packageId="{escape(base)}/api/dwca.zip" system="{escape(base)}" xml:lang="en">
  <dataset>
    <alternateIdentifier>{escape(base)}/api/dwca.zip</alternateIdentifier>
    <title xml:lang="en">{escape(title)}</title>
    <creator>{party}</creator>
    <metadataProvider>{party}</metadataProvider>
    <pubDate>{datetime.now(timezone.utc).date().isoformat()}</pubDate>
    <language>en</language>
    <abstract><para>{escape(description)} {count} records.</para></abstract>
    <intellectualRights><para>This work is licensed under a <ulink url="{url}"><citetitle>{escape(label)}</citetitle></ulink>.</para></intellectualRights>
    <distribution scope="document"><online><url function="information">{escape(base)}/specimens</url></online></distribution>
    <contact>{party}</contact>
  </dataset>
</eml:eml>
"""


def build(db: Session, holding_institution: str = "", collection: str = "", measurements: bool = True) -> bytes:
    base = _base()
    license_key = settings.DWC_LICENSE.strip()
    if license_key not in LICENSES:
        raise HTTPException(409, f"Set DWC_LICENSE to one of {', '.join(LICENSES)}; GBIF accepts only these.")
    records = _vouchers(db, holding_institution, collection)
    if len(records) > MAX_RECORDS:
        raise HTTPException(422, f"More than {MAX_RECORDS:,} released vouchers; export one holding institution or collection at a time.")
    ids = [specimen.specimen_id for specimen, _, _ in records]
    references, media = {}, {}
    if ids:
        for specimen_id, doi in db.execute(select(SpecimenPublication.specimen_id, Publication.doi)
                                           .join(Publication, Publication.pub_id == SpecimenPublication.publication_id)
                                           .where(SpecimenPublication.specimen_id.in_(ids))):
            if doi:
                references.setdefault(specimen_id, []).append(f"https://doi.org/{doi.removeprefix('https://doi.org/')}")
        for specimen_id, image_id in db.execute(select(Image.specimen_id, Image.image_id)
                                                .where(Image.specimen_id.in_(ids), Image.is_public.is_(True))
                                                .order_by(Image.upload_date, Image.image_id)):
            media.setdefault(specimen_id, []).append(f"{base}/api/image/{image_id}/content")
    license_url = LICENSES[license_key][0]
    occurrences = [_occurrence(db, base, license_url, specimen, taxon, location,
                               references.get(specimen.specimen_id, []), media.get(specimen.specimen_id, []))
                   for specimen, taxon, location in records]
    terms = [term for term, _ in OCCURRENCE_TERMS]
    mof = _measurements(db, base, {row_id: row["occurrenceID"] for row_id, row in zip(ids, occurrences)}) if measurements else []
    filters = [value for value in (holding_institution, collection) if value]
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("meta.xml", _meta(bool(mof)))
        bundle.writestr("eml.xml", _eml(base, license_key, len(occurrences), filters))
        bundle.writestr("occurrence.txt", _table(terms, ([row[term] for term in terms] for row in occurrences)))
        if mof:
            bundle.writestr("measurementorfact.txt",
                            _table(["coreid", *MOF_TERMS], ([row["coreid"], *(row[term] for term in MOF_TERMS)] for row in mof)))
    return archive.getvalue()
