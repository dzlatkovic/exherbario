"""Published versions keep their snapshot schema: versions 2 and 3 must both validate and render."""

from hashlib import sha256

import pytest

from app.deposition.archive import build_archive, manifest_for, canonical_json
from app.web.routes import profile_vouchers, templates

SOURCE = b"feature,value,confidence\r\nA,100,annotated\r\n"
FILE = {"name": "source.csv", "size": len(SOURCE), "sha256": sha256(SOURCE).hexdigest(),
        "source_fidelity": "byte-preserved", "url": "https://herbar.example.edu/files/p1"}


def voucher(voucher_id, name):
    return {"id": voucher_id, "reg_no": voucher_id, "location": None,
            "determination": {"name_as_recorded": name, "date": None, "taxonomy": None}}


def profile(sample, **extra):
    return {"id": "p1", "run_code": "R", "analytical_method": "GC-MS", "measurement_basis": "peak_area_percent",
            "unit": "%", "measurements": [], "study": {"id": "s", "title": "S"}, "sample": sample,
            "preparation": {"id": "b", "batch_code": "B", "kind": "essential_oil", "method_reference": "M"},
            "file": FILE, **extra}


def snapshot(schema, profiles, vouchers):
    return {"schema_version": schema, "institution": "EXU", "accession": "a", "version": 1, "title": "T",
            "description": "", "license": "CC BY 4.0", "contributors": [], "correction_reason": None,
            "supersedes": None, "profiles": profiles, "vouchers": vouchers}


V2 = snapshot(2, [profile({"id": "x", "code": "S-1", "plant_part": "leaf",
                           "voucher_relationship": "collected_alongside"}, voucher=voucher("v1", "Achillea atrata"))],
              [voucher("v1", "Achillea atrata"), voucher("v9", "Listed only")])
V3_SAMPLE = {"id": "x", "code": "S-1", "plant_part": "other", "plant_part_note": "Needles", "material_state": "fresh",
             "collection_date": "2024-06-12", "phenological_stage": None, "drying_notes": None, "storage_notes": None,
             "site": None, "vouchers": [
                 {"id": "v1", "role": "sampled_from_voucher", "redetermined_since_linking": False,
                  "determination_at_link": {"name_as_recorded": "Achillea atrata", "taxon_name": None, "taxon_id": None,
                                            "date": None, "recorded": "at_link"}},
                 {"id": "v2", "role": "same_population", "redetermined_since_linking": True,
                  "determination_at_link": {"name_as_recorded": "Achillea sp.", "taxon_name": None, "taxon_id": None,
                                            "date": None, "recorded": "at_migration"}}]}
V3 = snapshot(3, [profile(V3_SAMPLE)], [voucher("v1", "Achillea atrata"), voucher("v2", "Achillea clavennae")])


def render(data):
    linked, unprofiled = profile_vouchers(data)
    record = {"title": "T", "institution": "EXU", "institution_name": "Example", "accession": "a", "version": 1,
              "status": "current", "published_at": "2026-11-20T00:00:00", "url": "u", "article_dois": []}
    return templates.get_template("deposition.html").render(
        record=record, snapshot=data, citation="c", linked=linked, unprofiled=unprofiled,
        current_url="u", latest_url="u", previous_url=None)


def test_schema_2_snapshots_still_validate_and_render():
    assert build_archive(V2, {"p1": SOURCE})
    linked, unprofiled = profile_vouchers(V2)
    assert [voucher["id"] for voucher, _ in linked["p1"]] == ["v1"]
    assert [voucher["id"] for voucher in unprofiled] == ["v9"]
    page = render(V2)
    assert "Collected alongside the voucher" in page and "Listed only" in page


def test_schema_3_lists_every_linked_voucher():
    assert build_archive(V3, {"p1": SOURCE})
    page = render(V3)
    for text in ("Sampled from the voucher", "Same population as the voucher", "Needles",
                 "redetermined after this sample was linked", "recorded when sample links were introduced"):
        assert text in page
    missing = {**V3, "vouchers": V3["vouchers"][:1]}
    with pytest.raises(ValueError, match="linked to a profile's sample must be listed"):
        manifest_for(missing, canonical_json(missing))
    unlinked = {**V3, "profiles": [profile({**V3_SAMPLE, "vouchers": []})]}
    with pytest.raises(ValueError, match="linked to a profile's sample must be listed"):
        manifest_for(unlinked, canonical_json(unlinked))
