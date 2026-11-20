"""Record live PubChem responses as test fixtures, or check that PubChem answers.

    python -m app.chemistry.pubchem_record --check
    python -m app.chemistry.pubchem_record --out app/chemistry/tests/fixtures/pubchem.json alpha-pinene 82227 440968 limonene

Numbers are looked up as CIDs; anything else as a name (the best match is recorded).
"""

import argparse
import json
from pathlib import Path

from app.chemistry.pubchem import PubChemClient


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("identifiers", nargs="*")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--check", action="store_true", help="look up alpha-pinene and its parent and print them")
    arguments = parser.parse_args()
    client = PubChemClient()
    if arguments.check:
        record = client.compounds("name", "alpha-pinene")[0]
        print(f"PubChem answered: CID {record['cid']} {record['title']} {record['inchikey']}")
        print("Same connectivity:", client.same_connectivity(record["cid"])[:10])
        return
    records = []
    for identifier in arguments.identifiers:
        found = client.compounds("cid" if identifier.isdigit() else "name", int(identifier) if identifier.isdigit() else identifier)
        if not found:
            raise SystemExit(f"PubChem has no compound for {identifier!r}.")
        records.append(found[0])
        print(f"{identifier}: CID {found[0]['cid']} {found[0]['title']}")
    data = {"note": "Recorded from PubChem with app.chemistry.pubchem_record.", "records": records}
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if arguments.out:
        arguments.out.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
