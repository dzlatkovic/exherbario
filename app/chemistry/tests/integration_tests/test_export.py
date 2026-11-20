import csv
from io import StringIO

from app.chemistry.tests.integration_tests import test_compounds
from app.chemistry.tests.integration_tests.test_compounds import GC_RUN
from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, release_voucher
from app.tests import TestClass, client

EXPORT = f"{BASE}/public/export"
SECOND = ("feature,value,confidence,cid,ri_exp,id_basis\n"
          "α-Pinene,55,annotated,6654,931,RI;MS\nPinene,45,annotated,6654,,MS\n").encode()


def rows(response):
    assert response.status_code == 200, response.text
    return list(csv.DictReader(StringIO(response.text)))


class TestExport(TestClass):
    setup_profile = test_compounds.TestCompounds.setup_profile

    def test_long_and_wide_exports(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        owner, curator, voucher, study, upload = self.setup_profile()
        first = upload.json()["id"]
        preparation = upload.json()["preparation_id"]
        second = client.post(f"{BASE}/preparations/{preparation}/profiles", headers=owner,
                             data={"run_code": "R-2", "analytical_method": "GC-MS 1", "unit": "%",
                                   "measurement_basis": "peak_area_percent", "technique": "GC-MS",
                                   "run_metadata": GC_RUN},
                             files={"file": ("second.csv", SECOND, "text/csv")}).json()["id"]
        assert client.get(EXPORT, params={"profile_id": [first]}).status_code == 404
        assert client.get(EXPORT).status_code == 422
        for url in (f"{BASE}/studies/{study}/visibility", f"{BASE}/profiles/{first}/visibility",
                    f"{BASE}/profiles/{second}/visibility"):
            assert client.put(url, headers=curator, json={"is_public": True}).status_code == 200
        release_voucher(curator, voucher)

        long = rows(client.get(EXPORT, params={"study_id": study}))
        assert [(row["run_code"], row["feature"]) for row in long] == [
            ("R-1", "Limonene"), ("R-1", "Unidentified sesquiterpene"), ("R-1", "α-Pinene"), ("R-1", "β-Elemene"),
            ("R-2", "Pinene"), ("R-2", "α-Pinene")]
        pinene = long[2]
        assert (pinene["cid"], pinene["compound_title"], pinene["value"], pinene["ri_exp"], pinene["voucher_ids"],
                pinene["voucher_roles"], pinene["taxa"], pinene["yield_percent"], pinene["redetermined"]) == (
            "6654", "alpha-Pinene", "60", "932", voucher, "sampled_from_voucher", "Acer rubrum", "0.42", "false")
        assert (long[3]["value"], long[3]["qualifier"], long[3]["cid"]) == ("", "trace", "")
        assert client.get(EXPORT, params={"study_id": study}).text == client.get(EXPORT, params={"study_id": study}).text

        clash = client.get(EXPORT, params={"study_id": study, "format": "wide"})
        assert clash.status_code == 409 and "cid:6654" in clash.json()["detail"]
        assert client.put(f"{BASE}/profiles/{second}/measurements/Pinene/compound", headers=owner,
                          json={"cid": None, "reason": "Not separated from alpha-pinene"}).status_code == 200
        wide = client.get(EXPORT, params={"profile_id": [second, first], "format": "wide"})
        header = next(csv.reader(StringIO(wide.text)))
        assert header[-5:] == ["cid:6654", "cid:22311", "name:Pinene", "name:Unidentified sesquiterpene @RI 1498",
                               "name:β-Elemene @RI 1390"]
        table = rows(wide)
        assert [row["run_code"] for row in table] == ["R-1", "R-2"]
        assert (table[0]["cid:6654"], table[0]["name:β-Elemene @RI 1390"], table[0]["name:Pinene"]) == ("60", "tr", "")
        assert (table[1]["cid:6654"], table[1]["name:Pinene"], table[1]["cid:22311"]) == ("55", "45", "")
        assert wide.headers["content-type"].startswith("text/csv")
