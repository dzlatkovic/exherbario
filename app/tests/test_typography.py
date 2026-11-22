import pytest

from app.web.typography import compound, decimal, formula, taxon


@pytest.mark.parametrize("name, authority, expected", [
    ("Achillea millefolium", "L.", "<em>Achillea millefolium</em> L."),
    ("Achillea collina (Becker ex Rchb.f.) Heimerl", None, "<em>Achillea collina</em> (Becker ex Rchb.f.) Heimerl"),
    ("Achillea millefolium L. subsp. ceretanica Sennen", None,
     "<em>Achillea millefolium</em> L. subsp. <em>ceretanica</em> Sennen"),
    ("Thymus sp.", None, "<em>Thymus</em> sp."),
    ("Mentha × piperita L.", None, "<em>Mentha</em> × <em>piperita</em> L."),
    ("Asteraceae", None, "Asteraceae"),
    ("Plantae", None, "Plantae"),
    ("Unidentified specimen", None, "Unidentified specimen"),
    ("Salvia <b>", None, "<em>Salvia</em> &lt;b&gt;"),
])
def test_botanical_names(name, authority, expected):
    assert str(taxon(name, authority)) == expected


def test_formulas_and_compound_names():
    assert str(formula("C15H10O5")) == "C<sub>15</sub>H<sub>10</sub>O<sub>5</sub>"
    assert str(compound("(2E,6E)-Farnesol")) == "(2<i>E</i>,6<i>E</i>)-Farnesol"
    assert str(compound("(E)-β-Ocimene")) == "(<i>E</i>)-β-Ocimene"
    assert str(compound("p-Cymene")) == "<i>p</i>-Cymene"
    assert str(compound("trans-Sabinene hydrate")) == "<i>trans</i>-Sabinene hydrate"
    assert str(compound("4-O-Methylcedrusin")) == "4-<i>O</i>-Methylcedrusin"
    assert str(compound("(1R,5S)-(+)-Camphor")) == "(1<i>R</i>,5<i>S</i>)-(+)-Camphor"
    assert str(compound("Limonene")) == "Limonene" and str(compound("1,8-Cineole")) == "1,8-Cineole"
    assert str(compound("Germacrene D")) == "Germacrene D"


def test_decimals_align_on_the_point():
    assert str(decimal(12.4)) == '12<span class="fraction">.4</span>'
    assert str(decimal(5.0)) == '5<span class="fraction"></span>'
