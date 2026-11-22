from app.chemistry.tests.integration_tests.test_sample_vouchers import BASE, headers_for
from app.tests import TestClass, client
from app.users.services import UserServices

URL = f"{BASE}/condition-presets"
GC = {"technique": "GC-MS", "analytical_method": "GC-MS, HP-5MS", "measurement_basis": "peak_area_percent",
      "unit": "%", "run_metadata": {"polarity_class": "non-polar", "column": "HP-5MS"}}


class TestConditionPresets(TestClass):
    def test_save_replace_list_and_delete(self):
        owner = headers_for(UserServices.create_user("Lab", "Owner", "lab@example.org", "password"))
        other = headers_for(UserServices.create_user("Other", "Lab", "other@example.org", "password"))

        saved = client.put(URL, headers=owner, json={"kind": "run", "name": "HP-5MS oils", "values": GC})
        assert saved.status_code == 200, saved.text
        assert saved.json()["values"]["run_metadata"] == {"polarity_class": "non-polar", "column": "HP-5MS"}
        again = client.put(URL, headers=owner, json={"kind": "run", "name": "HP-5MS oils",
                                                     "values": {**GC, "unit": "%", "analytical_method": "GC-MS 2"}})
        assert again.json()["id"] == saved.json()["id"]
        assert again.json()["values"]["analytical_method"] == "GC-MS 2"

        method = {"kind": "essential_oil", "method_reference": "European Pharmacopoeia 2.8.12",
                  "method_parameters": "Clevenger, 3 h"}
        assert client.put(URL, headers=owner, json={"kind": "preparation", "name": "HD 3 h", "values": method}).status_code == 200
        assert [preset["name"] for preset in client.get(URL, headers=owner).json()] == ["HD 3 h", "HP-5MS oils"]
        assert [preset["kind"] for preset in client.get(f"{URL}?kind=run", headers=owner).json()] == ["run"]
        assert client.get(URL, headers=other).json() == []

        # GC conditions need the column polarity; preparation presets hold only the method, not the batch.
        no_polarity = {**GC, "run_metadata": {"column": "HP-5MS"}}
        assert client.put(URL, headers=owner, json={"kind": "run", "name": "x", "values": no_polarity}).status_code == 422
        assert client.put(URL, headers=owner, json={"kind": "preparation", "name": "x",
                                                    "values": {**method, "batch_code": "B1"}}).status_code == 422
        assert client.put(URL, headers=owner, json={"kind": "run", "name": "x",
                                                    "values": {**GC, "technique": "NMR"}}).status_code == 422

        preset_id = saved.json()["id"]
        assert client.delete(f"{URL}/{preset_id}", headers=other).status_code == 404
        assert client.delete(f"{URL}/{preset_id}", headers=owner).status_code == 204
        assert [preset["name"] for preset in client.get(URL, headers=owner).json()] == ["HD 3 h"]
