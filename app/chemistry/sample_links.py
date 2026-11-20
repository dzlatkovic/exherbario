"""Sample–voucher links: determinations recorded at linking, redetermination checks and public sample fields."""

from datetime import datetime, timezone

from app.catalog import public_location
from app.chemistry.models import LabSample, SampleVoucher

# Sample provenance shown publicly. Collection notes, the field location and its ID stay private.
PROVENANCE = ("plant_part", "plant_part_note", "material_state", "collection_date", "phenological_stage",
              "drying_notes", "storage_notes")


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_link(sample_id: str, specimen, taxon_name: str | None, role: str) -> SampleVoucher:
    return SampleVoucher(
        sample_id=sample_id, specimen_id=specimen.specimen_id, role=role, linked_at=utc_now(),
        taxon_id_at_link=specimen.taxon_id, taxon_name_at_link=taxon_name, name_at_link=specimen.subnomen,
        determination_date_at_link=specimen.determination_date, determination_recorded="at_link",
    )


def determination_at_link(link: SampleVoucher) -> dict:
    return {
        "taxon_id": link.taxon_id_at_link, "taxon_name": link.taxon_name_at_link,
        "name_as_recorded": link.name_at_link, "date": link.determination_date_at_link,
        "recorded": link.determination_recorded,
    }


def current_determination(specimen, taxon_name: str | None) -> dict:
    return {
        "taxon_id": specimen.taxon_id, "taxon_name": taxon_name,
        "name_as_recorded": specimen.subnomen, "date": specimen.determination_date,
    }


def redetermined(link: SampleVoucher, specimen) -> bool:
    """True when the voucher's determination changed after the sample was linked."""
    return ((link.taxon_id_at_link, link.name_at_link, link.determination_date_at_link)
            != (specimen.taxon_id, specimen.subnomen, specimen.determination_date))


def public_site(sample: LabSample, links) -> dict | None:
    """A linked voucher's site follows that voucher's public location setting; a sample's own site is withheld."""
    if sample.site_specimen_id:
        voucher = next(specimen for link, specimen, _ in links if link.specimen_id == sample.site_specimen_id)
        return {"source": "voucher", "specimen_id": sample.site_specimen_id,
                "location": public_location(voucher, voucher.field_loc)}
    if sample.field_loc_id:
        return {"source": "field_location", "location": None}
    return None
