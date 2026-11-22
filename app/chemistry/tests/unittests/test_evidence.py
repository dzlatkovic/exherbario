import pytest

from app.chemistry.names import cas_numbers, name_key, stereo_unspecified, valid_cas
from app.chemistry.services.profile_import import parse_evidence, read_measurements

GC = {"polarity_class": "non-polar"}


def evidence(raw, technique="GC-MS", run=GC):
    return parse_evidence(raw, "Row 2", technique, run)


def test_name_keys_match_spelling_variants():
    assert name_key("α-Pinene") == name_key("alpha-pinene") == name_key("  ALPHA–pinene ")
    assert name_key("β-Caryophyllene") == "beta-caryophyllene"
    assert valid_cas("80-56-8") and not valid_cas("80-56-7") and not valid_cas("8056-8")
    assert cas_numbers(["alpha-Pinene", "80-56-8", "80-56-7"]) == ["80-56-8"]
    assert stereo_unspecified("GRWFGVWFFZKLTI-UHFFFAOYSA-N") and not stereo_unspecified("GRWFGVWFFZKLTI-IUCAKERBSA-N")


def test_gc_evidence_is_normalized_and_checked():
    identifiers, fields, warnings = evidence({
        "cid": "6654", "cas": "80-56-8", "ri_exp": "932", "ri_ref": "939", "ri_ref_source": "Adams 2007",
        "ri_ref_polarity": "Non-polar", "id_basis": "ms; RI", "id_level": "2", "qualifier": "tr", "sd": "0,4", "n": "3",
        "library_match": "alpha-Pinene", "library_score": "94"})
    assert identifiers == {"cid": 6654, "cas": "80-56-8"}
    assert fields["id_basis"] == "RI;MS" and fields["qualifier"] == "trace" and fields["sd"] == 0.4
    assert fields["ri_ref_polarity"] == "non-polar" and warnings == []
    _, _, warnings = evidence({"ri_exp": "932", "ri_ref": "960"})
    assert warnings and "differs from the reference 960 by more than 20" in warnings[0]


@pytest.mark.parametrize("raw, technique, message", [
    ({"id_basis": "RI;MS"}, "GC-MS", "experimental RI"),
    ({"ri_exp": "932", "ri_ref": "935", "ri_ref_polarity": "polar"}, "GC-MS", "polar column, but the run used a non-polar"),
    ({"id_level": "1", "id_basis": "MS"}, "GC-MS", "reference standard"),
    ({"id_level": "5"}, "GC-MS", "MSI level"),
    ({"mz_obs": "205.19"}, "GC-MS", "cannot be recorded for GC-MS"),
    ({"library_match": "x"}, "GC-FID", "cannot be recorded for GC-FID"),
    ({"ri_exp": "932"}, "LC-MS", "cannot be recorded for LC-MS"),
    ({"mz_obs": "205.19"}, "HPLC-DAD", "cannot be recorded for HPLC-DAD"),
    ({"id_basis": "smell"}, "GC-MS", "unknown identification basis"),
    ({"qualifier": "approx"}, "GC-MS", "trace or <LOQ"),
    ({"cas": "80-56-7"}, "GC-MS", "check digit"),
    ({"inchikey": "GRWFGVWFFZKLTI"}, "GC-MS", "27-character"),
    ({"cid": "-4"}, "GC-MS", "out of range"),
])
def test_invalid_evidence_is_rejected(raw, technique, message):
    with pytest.raises(ValueError, match=message):
        evidence(raw, technique, GC if technique.startswith("GC") else {})


def test_lc_evidence_and_identification_by_standard():
    _, fields, _ = evidence({"mz_obs": "355.1024", "adduct": "[M+H]+", "mass_error_ppm": "-1.2",
                             "msms_match": "MoNA", "id_basis": "standard;MS/MS", "id_level": "1"}, "LC-MS/MS", {})
    assert fields == {"mz_obs": 355.1024, "adduct": "[M+H]+", "mass_error_ppm": -1.2, "msms_match": "MoNA",
                      "id_basis": "standard;MS/MS", "id_level": 1}


def test_csv_accepts_trace_rows_and_old_three_column_files():
    old = read_measurements(b"feature,value,confidence\nA,60,annotated\nB,40,annotated\n", "peak_area_percent")
    assert [row["value"] for row in old[1]] == [60, 40] and old[2] == []
    source = ("feature,value,confidence,cid,rt_min,ri_exp,ri_ref,ri_ref_source,id_basis,id_level,qualifier\n"
              "α-Pinene,12.4,annotated,6654,7.82,932,932,Adams 2007,RI;MS,2,\n"
              "Unidentified sesquiterpene,0.4,tentative,,25.03,1498,,,MS,3,\n"
              "β-Elemene,,annotated,,22.91,1390,1389,Adams 2007,RI;MS,2,trace\n").encode()
    _, rows, warnings = read_measurements(source, "peak_area_percent", "GC-MS", GC)
    assert [(row["feature"], row["value"], row.get("qualifier")) for row in rows] == [
        ("α-Pinene", 12.4, None), ("Unidentified sesquiterpene", 0.4, None), ("β-Elemene", None, "trace")]
    assert rows[0]["identifiers"] == {"cid": 6654} and rows[1]["identifiers"] == {} and warnings == []
    with pytest.raises(ValueError, match="ri_ref_source cannot be recorded for LC-MS"):
        read_measurements(source, "peak_area_percent", "LC-MS", {})
    with pytest.raises(ValueError, match="Use the CSV columns"):
        read_measurements(b"feature,value,confidence,colour\nA,1,x,red\n", "concentration")


@pytest.mark.parametrize("given, expected", [
    ("RI; MS; CoI", "RI;MS;co-injection"),
    ("KI, MS (NIST 17)", "RI;MS"),
    ("RI/MS", "RI;MS"),
    ("LRI + Co-GC", "RI;co-injection"),
    ("Std. and Lit.", "standard;literature"),
    ("MS/MS", "MS/MS"),
])
def test_identification_abbreviations_used_in_papers(given, expected):
    _, fields, _ = evidence({"ri_exp": "932", "id_basis": given})
    assert fields["id_basis"] == expected


def test_unknown_identification_basis_is_refused():
    with pytest.raises(ValueError, match="unknown identification basis 'b'"):
        evidence({"ri_exp": "932", "id_basis": "RI; b"})
