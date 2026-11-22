"""Structures supplied by authors: validated and identified locally with RDKit, so no service is needed."""

import re
from functools import lru_cache

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

RDLogger.DisableLog("rdApp.*")

MAX_STRUCTURE_LENGTH = 20000  # A molfile of a large natural product; SMILES are far shorter.
HRMS_TOLERANCE_PPM = 10.0

ELECTRON = 0.000548579909
H = 1.00782503207
ADDUCTS = {
    # Normalized adduct → (molecules, mass added to n·M before removing or adding electrons, charge)
    "[M]+": (1, 0.0, 1), "[M]-": (1, 0.0, -1),
    "[M+H]+": (1, H, 1), "[M+Na]+": (1, 22.9897692809, 1), "[M+K]+": (1, 38.96370668, 1),
    "[M+NH4]+": (1, 14.0030740048 + 4 * H, 1), "[M+H-H2O]+": (1, H - (2 * H + 15.99491461956), 1),
    "[M+2H]2+": (1, 2 * H, 2), "[2M+H]+": (2, H, 1), "[2M+Na]+": (2, 22.9897692809, 1),
    "[M-H]-": (1, -H, -1), "[M+Cl]-": (1, 34.96885268, -1),
    "[M+HCOO]-": (1, 12 + H + 2 * 15.99491461956, -1), "[M+FA-H]-": (1, 12 + H + 2 * 15.99491461956, -1),
    "[M+CH3COO]-": (1, 24 + 3 * H + 2 * 15.99491461956, -1),
}


class StructureError(ValueError):
    pass


def _molecule(text: str):
    text = (text or "").strip()
    if not text:
        raise StructureError("The structure is empty.")
    if len(text) > MAX_STRUCTURE_LENGTH:
        raise StructureError("The structure is too long.")
    if "M  END" in text:
        molecule = Chem.MolFromMolBlock(text)
        kind = "molfile"
    else:
        if any(character.isspace() for character in text):
            # A SMILES may be followed by a name; anything else with spaces is not a SMILES.
            text = text.split()[0]
        molecule = Chem.MolFromSmiles(text)
        kind = "SMILES"
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise StructureError(f"The {kind} could not be read as a valid structure (check atoms, bonds, rings and valences).")
    return molecule


@lru_cache(maxsize=4096)
def _parse(text: str) -> tuple:
    molecule = _molecule(text)
    inchi = Chem.MolToInchi(molecule)
    if not inchi:
        raise StructureError("No InChI could be computed for this structure.")
    centres = Chem.FindMolChiralCenters(molecule, includeUnassigned=True, useLegacyImplementation=False)
    return (Chem.MolToSmiles(molecule), inchi, Chem.InchiToInchiKey(inchi),
            rdMolDescriptors.CalcMolFormula(molecule), Descriptors.ExactMolWt(molecule),
            sum(label == "?" for _, label in centres), len(centres))


def parse_structure(text: str) -> dict:
    """Canonical SMILES, standard InChI and InChIKey, formula and monoisotopic mass of a SMILES or molfile."""
    smiles, inchi, inchikey, formula, mass, unassigned, centres = _parse((text or "").strip())
    return {"smiles": smiles, "inchi": inchi, "inchikey": inchikey, "molecular_formula": formula,
            "monoisotopic_mass": mass, "unassigned_stereocentres": unassigned, "stereocentres": centres}


def normalize_adduct(adduct: str) -> str:
    text = re.sub(r"\s+", "", adduct or "").replace("−", "-").replace("⁺", "+").replace("⁻", "-")
    text = text.rstrip("·.•")
    match = re.fullmatch(r"\[?(\d?M[^\]]*?)\]?(\d?[+-])?", text)
    if match is None:
        return text
    body, charge = match.groups()
    if charge is None:
        if body in ("M", "2M"):
            return text
        # "M+H" and "M-H" as commonly written: the charge follows the sign of the first change.
        charge = "-" if body.lstrip("2").startswith("M-") else "+"
    return f"[{body}]{charge}"


def expected_mz(monoisotopic_mass: float, adduct: str) -> float | None:
    """The m/z of an ion of a neutral molecule, or None for an adduct this check does not know."""
    known = ADDUCTS.get(normalize_adduct(adduct))
    if known is None:
        return None
    molecules, added, charge = known
    return (molecules * monoisotopic_mass + added - charge * ELECTRON) / abs(charge)


def mass_error_ppm(observed: float, expected: float) -> float:
    return (observed - expected) / expected * 1e6


def depiction_svg(smiles: str, width: int = 260, height: int = 200) -> str:
    """An SVG drawing of a structure, for review and record pages (no external images needed)."""
    molecule = _molecule(smiles)
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.addStereoAnnotation = True
    drawer.DrawMolecule(molecule)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    return svg[svg.index("<svg"):]
