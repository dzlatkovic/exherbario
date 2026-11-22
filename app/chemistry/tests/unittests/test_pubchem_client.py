import json

import pubchempy

from app.chemistry import pubchem
from app.chemistry.pubchem import PubChemClient


class Answer:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode()


def test_same_connectivity_asks_for_the_cid_list(monkeypatch):
    calls = []

    def request(identifier, namespace, domain, operation, output, searchtype=None, **kwargs):
        calls.append((identifier, namespace, operation, searchtype, kwargs))
        return Answer({"IdentifierList": {"CID": [6654, 82227, 440968]}})

    monkeypatch.setattr(pubchempy, "request", request)
    assert PubChemClient().same_connectivity(6654) == [6654, 82227, 440968]
    assert calls == [(6654, "cid", "cids", "fastidentity", {"identity_type": "same_connectivity"})]


def test_same_connectivity_follows_a_list_key(monkeypatch):
    answers = iter([{"Waiting": {"ListKey": "123"}}, {"IdentifierList": {"CID": [1, 2]}}])
    monkeypatch.setattr(pubchempy, "request", lambda *args, **kwargs: Answer(next(answers)))
    monkeypatch.setattr(pubchem.time, "sleep", lambda seconds: None)
    assert PubChemClient().same_connectivity(1) == [1, 2]


def test_same_connectivity_without_matches(monkeypatch):
    monkeypatch.setattr(pubchempy, "request", lambda *args, **kwargs: Answer({}))
    assert PubChemClient().same_connectivity(1) == []


def test_racemic_prefix_counts_as_the_same_name():
    from app.chemistry.services.compounds import same_preferred_name

    racemic = {"title": "(+-)-alpha-Pinene", "inchikey": "GRWFGVWFFZKLTI-UHFFFAOYSA-N"}
    assert same_preferred_name(racemic, "α-Pinene") and same_preferred_name(racemic, "alpha-pinene")
    assert not same_preferred_name({**racemic, "inchikey": "GRWFGVWFFZKLTI-IUCAKERBSA-N"}, "α-Pinene")
    assert not same_preferred_name(racemic, "β-Pinene")
    assert same_preferred_name({"title": "Limonene", "inchikey": "XMGQYMWWDOXHJM-UHFFFAOYSA-N"}, "limonene")


def test_the_timeout_is_per_request_and_leaves_the_process_default(monkeypatch):
    import socket
    import threading

    seen = []

    def urlopen(url, data=None, timeout=None, **kwargs):
        seen.append(timeout)
        return Answer({"IdentifierList": {"CID": [1]}})

    monkeypatch.setattr(pubchem, "_urlopen", urlopen)
    before = socket.getdefaulttimeout()
    barrier = threading.Barrier(2)

    def call():
        barrier.wait()
        PubChemClient(timeout=7).same_connectivity(1)

    threads = [threading.Thread(target=call) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert socket.getdefaulttimeout() == before
    assert seen == [7, 7]


def test_names_are_searched_without_greek_letters(monkeypatch):
    from app.chemistry.names import pubchem_query

    assert pubchem_query("α-Pinene") == "alpha-Pinene"
    assert pubchem_query("(E)–β-Ocimene") == "(E)-beta-Ocimene"
    assert pubchem_query("Δ3-Carene") == "delta3-Carene"
    assert pubchem_query("2′-hydroxy  γ-terpinene") == "2'-hydroxy gamma-terpinene"
    searched = []

    def properties(properties, identifier, namespace):
        searched.append(identifier)
        return []
    monkeypatch.setattr(pubchempy, "get_properties", properties)
    PubChemClient().compounds("name", "β-Caryophyllene")
    assert searched == ["beta-Caryophyllene"]


class Busy:
    headers = {"X-Throttling-Control": "Request Count status: Yellow (60%)"}

    def read(self):
        return json.dumps({"IdentifierList": {"CID": [1]}}).encode()


def test_a_busy_pubchem_is_retried_and_requests_are_paced(monkeypatch):
    from urllib.error import HTTPError

    answers = [HTTPError("u", 503, "PUGREST.ServerBusy", {}, None), Busy()]
    pauses = []

    def urlopen(url, data=None, **kwargs):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
    monkeypatch.setattr(pubchem, "_urlopen", urlopen)
    monkeypatch.setattr(pubchem.time, "sleep", pauses.append)
    monkeypatch.setitem(pubchem._pace_state, "next", 0.0)
    assert PubChemClient().same_connectivity(1) == [1]
    assert 1 in pauses  # waited before the retry
    assert pubchem._pace_state["factor"] == 2.0  # and slows down while PubChem reports load
    monkeypatch.setitem(pubchem._pace_state, "factor", 1.0)


def test_pubchem_unavailable_after_the_retries(monkeypatch):
    from urllib.error import HTTPError

    import pytest

    def urlopen(url, data=None, **kwargs):
        raise HTTPError("u", 503, "PUGREST.ServerBusy", {}, None)
    monkeypatch.setattr(pubchem, "_urlopen", urlopen)
    monkeypatch.setattr(pubchem.time, "sleep", lambda seconds: None)
    with pytest.raises(pubchem.PubChemUnavailable):
        PubChemClient().same_connectivity(1)
