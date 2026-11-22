"""Serialized measurements, corrections and preparations, shared by the API and deposition snapshots."""

from app.chemistry.models import Measurement, Preparation
from app.chemistry.services.compounds import compound_summary, structure_summary
from app.chemistry.services.profile_import import EVIDENCE


def preparation_summary(preparation: Preparation):
    return {
        "id": preparation.id, "sample_id": preparation.sample_id, "batch_code": preparation.batch_code,
        "kind": preparation.kind, "method_reference": preparation.method_reference,
        "plant_material_mass_g": preparation.plant_material_mass_g,
        "method_parameters": preparation.method_parameters, "yield_percent": preparation.yield_percent,
    }


def measurement_record(row: Measurement, compound) -> dict:
    record = {"feature": row.feature, "value": row.value, "confidence": row.confidence, "status": row.status,
              "cid": row.cid, "compound_match": row.compound_match}
    record.update({name: getattr(row, name) for name in EVIDENCE if getattr(row, name) is not None})
    if compound is not None:
        record["compound"] = {key: value for key, value in compound_summary(compound).items()
                              if key not in ("inchi", "retrieved_at")}
    if row.structure_id is not None:
        record["structure_id"] = row.structure_id
        record["structure"] = structure_summary(row.structure)
    return record


def correction_record(correction) -> dict:
    record = {"feature": correction.feature, "old_cid": correction.old_cid, "new_cid": correction.new_cid,
              "reason": correction.reason, "corrected_at": correction.corrected_at}
    # Only present for corrections involving author-supplied structures, so older records serialize as before.
    for name in ("old_structure_id", "new_structure_id"):
        if getattr(correction, name) is not None:
            record[name] = getattr(correction, name)
    return record
