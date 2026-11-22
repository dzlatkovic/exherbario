"""Scientific typesetting for pages: botanical names, molecular formulas, compound names and aligned decimals.

Each filter escapes its input and returns markup, so templates use them instead of writing <em> by hand.
"""

import re

from markupsafe import Markup, escape

# Words that stay upright in a botanical name: ranks and qualifiers (ICN, Art. 60 and Rec. 60A).
RANK_WORDS = {"subsp.", "ssp.", "var.", "subvar.", "f.", "forma", "subf.", "cv.", "convar.", "nothosubsp.",
              "nothovar.", "sect.", "subsect.", "subg.", "ser.", "agg.", "s.l.", "s.str.", "s.lat.", "sp.", "spp.",
              "aff.", "cf.", "×", "x"}
EPITHET = re.compile(r"[a-zà-öø-ÿ][a-zà-öø-ÿ-]*")
# Above genus, names are set upright.
HIGHER_ENDINGS = ("aceae", "ales", "ineae", "oideae", "phyta", "phytina", "opsida", "idae", "anae", "eae", "inae")
HIGHER_NAMES = {"Plantae", "Fungi", "Chromista", "Protozoa"}
NOT_NAMES = {"undetermined", "unidentified", "unidentified specimen", "indet.", "—", "-"}


def _join(parts):
    """Adjacent italic words share one <em>."""
    html, open_ = [], False
    for word, italic in parts:
        if italic and not open_:
            html.append("<em>")
        elif not italic and open_:
            html[-1] = html[-1].rstrip()
            html.append("</em> ")
        html.append(f"{escape(word)} ")
        open_ = italic
    text = "".join(html).rstrip()
    return text + ("</em>" if open_ else "")


def taxon(name, authority=None):
    """Genus, species and infraspecific epithets in italics; authors, ranks and higher taxa upright:
    *Achillea millefolium* L. subsp. *ceretanica* Sennen."""
    if not name:
        return ""
    text = str(name).strip()
    if text.casefold() in NOT_NAMES or text.casefold().startswith("unidentified"):
        return escape(text)
    words = text.split()
    parts = []
    first = words[0]
    if first in HIGHER_NAMES or (len(words) == 1 and first.endswith(HIGHER_ENDINGS)):
        parts.append((first, False))
        in_authority = True
    else:
        parts.append((first, first[:1].isupper() or first[:1] == "×"))
        in_authority = not parts[0][1]
    expect_epithet = not in_authority
    for word in words[1:]:
        if word.casefold() in RANK_WORDS:
            parts.append((word, False))
            expect_epithet = True
        elif expect_epithet and EPITHET.fullmatch(word):
            parts.append((word, True))
        else:
            parts.append((word, False))
            expect_epithet = False
    html = _join(parts)
    if authority:
        html += f" {escape(authority)}"
    return Markup(html)


def formula(text):
    """Counts in a molecular formula as subscripts: C₁₀H₁₆O."""
    if not text:
        return ""
    return Markup(re.sub(r"(?<=[A-Za-z)\]])(\d+)", r"<sub>\1</sub>", str(escape(text))))


# Italic descriptors in compound names (IUPAC P-93): n-, sec-, tert-, o-/m-/p-, cis-/trans-, endo-/exo-, rel-, rac-,
# heteroatom locants (N-, O-, S-), and E/Z and R/S in parentheses, e.g. (2E,6E)-, (1R,5S)-, (E)-.
PREFIX = re.compile(r"(?<![A-Za-zÀ-ÿ])(n|sec|tert|o|m|p|cis|trans|endo|exo|syn|anti|ent|epi|rel|rac|meso|N|O|S|E|Z)"
                    r"(?=-)")
STEREO_GROUP = re.compile(r"\(((?:\d*[a-z]?(?:RS|SR|R|S|E|Z|r|s)\*?)(?:,\s?\d*[a-z]?(?:RS|SR|R|S|E|Z|r|s)\*?)*)\)")
STEREO_LETTERS = re.compile(r"(RS|SR|R|S|E|Z|r|s)(?=\*?(?:,|$))")


def compound(name):
    if not name:
        return ""
    html = str(escape(name))
    html = STEREO_GROUP.sub(lambda match: "(" + STEREO_LETTERS.sub(r"<i>\1</i>", match[1]) + ")", html)
    html = PREFIX.sub(r"<i>\1</i>", html)
    return Markup(html)


def decimal(value):
    """A number whose decimal point lines up with the others in a right-aligned column."""
    if value is None:
        return ""
    text = value if isinstance(value, str) else f"{value:g}"
    whole, point, fraction = text.partition(".")
    return Markup(f'{escape(whole)}<span class="fraction">{escape(point + fraction)}</span>')


FILTERS = {"taxon": taxon, "formula": formula, "compound": compound, "decimal": decimal}
