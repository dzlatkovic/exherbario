"""Compound name keys and identifier formats shared by imports, aliases and the registry."""

import re
import unicodedata

GREEK = {"α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon", "ζ": "zeta", "η": "eta",
         "θ": "theta", "κ": "kappa", "λ": "lambda", "μ": "mu", "ρ": "rho", "σ": "sigma", "τ": "tau",
         "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega"}
GREEK_CAPITALS = {"Δ": "delta", "Ω": "omega", "Ψ": "psi", "Φ": "phi", "Γ": "gamma", "Λ": "lambda"}
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")
PRIMES = dict.fromkeys(map(ord, "′’‘ʹ"), "'") | {ord("″"): "''"}
INCHIKEY = re.compile(r"^[A-Z]{14}-[A-Z]{10}-[A-Z]$")
CAS = re.compile(r"^(\d{2,7})-(\d{2})-(\d)$")
NO_STEREO_BLOCK = "UHFFFAOYSA"


def name_key(name: str) -> str:
    """Case-, dash-, spacing- and Greek-letter-insensitive key, so α-pinene matches alpha-Pinene."""
    text = unicodedata.normalize("NFKC", name).translate(DASHES).casefold()
    text = "".join(GREEK.get(char, char) for char in text)
    return re.sub(r"\s+", " ", text).strip()[:300]


def pubchem_query(name: str) -> str:
    """A name as PubChem's name search understands it: Greek letters spelled out (α-pinene → alpha-pinene,
    Δ3-carene → delta3-carene), plain hyphens and apostrophes. Only for searching; names are stored as written."""
    text = unicodedata.normalize("NFKC", name).translate(DASHES).translate(PRIMES)
    text = "".join(GREEK.get(char) or GREEK_CAPITALS.get(char) or char for char in text)
    return re.sub(r"\s+", " ", text).strip()


def valid_cas(value: str) -> bool:
    match = CAS.match(value.strip())
    if not match:
        return False
    digits = (match[1] + match[2])[::-1]
    return sum(int(digit) * position for position, digit in enumerate(digits, 1)) % 10 == int(match[3])


def cas_numbers(synonyms) -> list[str]:
    return sorted({synonym for synonym in synonyms if valid_cas(synonym)})


def stereo_unspecified(inchikey: str | None) -> bool:
    return bool(inchikey) and inchikey.split("-")[1] == NO_STEREO_BLOCK
