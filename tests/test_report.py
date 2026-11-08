"""
Tests du rapport (risk-report) : contenu des sections, Markdown et HTML, sécurité du HTML
(échappement, CSP), contraste des couleurs, ligne de commande.
"""

import base64
import hashlib
import re
import tomllib
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import pytest

from risk_matrix import report
from risk_matrix.method import parse_method
from risk_matrix.register import parse_register
from risk_matrix.report import Bullets, Heading, Paragraph, Table, build_report, md, render_html, render_markdown

ROOT = Path(__file__).parents[1]
REGISTRE = ROOT / "tests" / "data" / "registre-valide.toml"
TODAY = date(2026, 11, 8)


def load(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


METHODS = {m.id: m for m in (parse_method(load(p))[0] for p in sorted((ROOT / "methods").glob("*.toml")))}


@pytest.fixture
def data() -> dict:
    return load(REGISTRE)


def build(data: dict, today: date = TODAY):
    register, findings = parse_register(data, METHODS, today)
    assert findings.errors == []
    return register, build_report(register, findings.warnings, today)


def headings(rep) -> list[str]:
    return [b.text for b in rep.blocks if isinstance(b, Heading)]


def table_after(rep, title: str) -> Table:
    i = next(i for i, b in enumerate(rep.blocks) if isinstance(b, Heading) and b.text == title)
    return next(b for b in rep.blocks[i + 1 :] if isinstance(b, Table | Paragraph))


# ── 1. Contenu ──────────────────────────────────────────────
def test_sections_dans_l_ordre(data):
    _register, rep = build(data)
    assert rep.title == "Rapport de risques — Organisation de test"
    assert headings(rep) == [
        "Synthèse", "Cartographie — risque inhérent", "Cartographie — risque résiduel", "Risques par niveau résiduel",
        "Au-dessus de l'appétence", "Plan d'action", "Calendrier des revues", "Références",
        "ISO/IEC 27001:2022, annexe A", "Playbooks de réponse aux incidents", "Techniques MITRE ATT&CK",
    ]  # fmt: skip
    synthese = next(b for b in rep.blocks if isinstance(b, Bullets))
    assert synthese.items == (
        "3 risque(s) actif(s), 0 clos",
        "2 au-dessus de l'appétence (« Faible »)",
        "1 mesure(s) ouverte(s), dont 0 en retard",
        "0 avertissement(s) à traiter",
    )


def test_cartographie_place_chaque_risque(data):
    _register, rep = build(data)
    inherent = table_after(rep, "Cartographie — risque inhérent")
    # Lignes : vraisemblance 5 → 1 ; colonnes : libellé, puis impact 1 → 5
    assert inherent.rows[1][0].text == "Probable"  # vraisemblance 4
    assert inherent.rows[1][5].text == "R01"  # R01 inhérent : 4 × 5
    assert inherent.rows[1][5].level == "critical"
    assert inherent.rows[1][3].text == "R02"  # R02 inhérent : 4 × 3
    residual = table_after(rep, "Cartographie — risque résiduel")
    assert residual.rows[2][4].text == "R01"  # R01 résiduel : 3 × 4
    assert residual.rows[0][1].text == ""  # case vide


def test_risques_tries_du_plus_grave_au_moins_grave(data):
    _register, rep = build(data)
    rows = table_after(rep, "Risques par niveau résiduel").rows
    assert [r[0].text for r in rows] == ["R01", "R02", "R03"]
    assert [r[4].level for r in rows] == ["high", "moderate", "low"]


def test_situations_au_dessus_de_l_appetence(data):
    _register, rep = build(data)
    rows = table_after(rep, "Au-dessus de l'appétence").rows
    assert rows[0][3].text == "Réduction en cours (1 mesure(s) ouverte(s))"
    assert rows[1][3].text == "Accepté par Claire Martin (Responsable du risque) jusqu'au 15/09/2027"
    _register, rep = build(data, date(2027, 10, 1))
    expired = table_after(rep, "Au-dessus de l'appétence").rows[1][3]
    assert expired.text == "Acceptation expirée le 15/09/2027 — à renouveler ou à traiter"
    assert expired.strong


def test_retards_mis_en_evidence(data):
    _register, rep = build(data, date(2027, 2, 15))
    (mesure,) = table_after(rep, "Plan d'action").rows
    assert (mesure[0].strong, mesure[4].text) == (True, "En retard")
    revue = table_after(rep, "Calendrier des revues").rows[0]
    assert revue[0].text == "01/01/2027 — En retard"
    assert headings(rep)[-1] == "Avertissements"


def test_risque_clos_a_part(data):
    data["risks"][2]["status"] = "closed"
    _register, rep = build(data)
    assert "Risques clos" in headings(rep)
    assert [r[0].text for r in table_after(rep, "Risques par niveau résiduel").rows] == ["R01", "R02"]


def test_sans_reference(data):
    for risk in data["risks"]:
        for key in ("iso27001", "attack", "playbooks"):
            risk.pop(key, None)
        for measure in risk.get("measures", []):
            measure.pop("iso27001", None)
    _register, rep = build(data)
    assert table_after(rep, "Références") == Paragraph("Aucune référence renseignée.")


def test_rapport_en_anglais(data):
    data["lang"] = "en"
    data["risks"][1]["acceptance"]["role"] = "Risk owner"
    _register, rep = build(data)
    assert rep.title == "Risk report — Organisation de test"
    assert rep.meta[2] == "Status as of: 2026-11-08"
    assert "Heat map — residual risk" in headings(rep)
    assert "Accepted by Claire Martin (Risk owner) until 2027-09-15" in render_markdown(rep)


def test_methode_ebios(data):
    data["method"] = "ebios-rm-4x4"
    # (inhérent, résiduel) : R01 inacceptable → inacceptable, R02 inacceptable → tolérable, R03 → acceptable
    notes = [((4, 4), (3, 3)), ((4, 3), (2, 3)), ((3, 2), (1, 2))]
    for risk, (inh, res) in zip(data["risks"], notes, strict=True):
        risk["inherent"] = dict(zip(("likelihood", "impact"), inh, strict=True))
        risk["residual"] = dict(zip(("likelihood", "impact"), res, strict=True))
    data["risks"][1]["acceptance"]["role"] = "Responsable du risque, après avis du RSSI"
    _register, rep = build(data)
    assert table_after(rep, "Cartographie — risque inhérent").rows[0][0].text == "V4 — Quasi certain"
    assert [r[4].level for r in table_after(rep, "Risques par niveau résiduel").rows] == [
        "unacceptable", "tolerable", "acceptable",
    ]  # fmt: skip


# ── 2. Markdown ─────────────────────────────────────────────
def test_markdown_lisible(data):
    _register, rep = build(data)
    text = render_markdown(rep)
    assert text.startswith("# Rapport de risques — Organisation de test\n")
    assert "| Probable | Faible | Modéré | Élevé · **R02** | Élevé | Critique · **R01** |" in text
    assert "[P02 — Attaque par rançongiciel](https://github.com/Aiyeesha/incident-response-playbook/" in text


@pytest.mark.parametrize(
    ("texte", "attendu"),
    [
        ("A | B", r"A \| B"),
        ("**gras** et _it_", r"\*\*gras\*\* et \_it\_"),
        ("<script>alert(1)</script>", r"\<script\>alert(1)\</script\>"),
        ("[clic](http://exemple.invalid)", r"\[clic\](http://exemple.invalid)"),
        ("ligne 1\nligne 2", "ligne 1 ligne 2"),
    ],
)
def test_markdown_echappe(texte, attendu):
    assert md(texte) == attendu


def test_markdown_tableau_non_casse(data):
    data["risks"][0]["title"] = "Fuite | colonne en plus\n# titre"
    _register, rep = build(data)
    ligne = next(line for line in render_markdown(rep).splitlines() if line.startswith("| R01 |"))
    cellules = re.split(r"(?<!\\)\|", ligne)[1:-1]  # séparateurs non échappés seulement
    assert len(cellules) == 7  # autant de cellules que de colonnes : le « | » du titre est échappé
    assert cellules[1].strip() == r"Fuite \| colonne en plus \# titre"


# ── 3. HTML : sécurité et structure ─────────────────────────
class _Collect(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict]] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


@pytest.fixture
def piege(data) -> dict:
    """Registre dont les textes tentent d'injecter du HTML."""
    data["organisation"] = '<script>alert("org")</script>'
    data["risks"][0]["title"] = '<img src=x onerror=alert(1)> & "guillemets"'
    data["risks"][0]["owner"] = "</td></tr></table><iframe src=//exemple.invalid>"
    return data


def test_html_echappe_tout_le_texte(piege):
    register, rep = build(piege)
    page = render_html(rep, register.method)
    parser = _Collect()
    parser.feed(page)
    tags = {tag for tag, _ in parser.tags}
    assert not tags & {"script", "img", "iframe", "object", "embed", "link"}
    assert "&lt;img src=x onerror=alert(1)&gt; &amp; &quot;guillemets&quot;" in page
    assert not any("style" in attrs or any(k.startswith("on") for k in attrs) for _, attrs in parser.tags)


def test_csp_autorise_exactement_la_feuille_de_style(data):
    register, rep = build(data)
    page = render_html(rep, register.method)
    csp = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', page)[1]
    assert csp.startswith("default-src 'none'; ")
    style = re.search(r"<style>(.*?)</style>", page, re.S)[1]
    digest = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    assert f"style-src 'sha256-{digest}'" in csp
    assert ".lv-critical { background: #b3261e; color: #ffffff; }" in style


def test_liens_externes_sans_referent(data):
    register, rep = build(data)
    parser = _Collect()
    parser.feed(render_html(rep, register.method))
    links = [attrs for tag, attrs in parser.tags if tag == "a"]
    assert len(links) == 7  # 3 playbooks + 4 techniques
    assert all(a["href"].startswith("https://") and a["rel"] == "noopener noreferrer" for a in links)


@pytest.mark.parametrize("method_id", ["iso27005-5x5", "ebios-rm-4x4"])
def test_contraste_des_niveaux_wcag_aa(method_id):
    for level in METHODS[method_id].levels:
        fg = report.text_color(level.color)
        lum_bg, lum_fg = report._luminance(level.color), report._luminance(fg)
        ratio = (max(lum_bg, lum_fg) + 0.05) / (min(lum_bg, lum_fg) + 0.05)
        assert ratio >= 4.5, (level.id, level.color, fg, round(ratio, 2))
        assert fg == "#ffffff"  # même couleur de texte sur toutes les cases : lecture homogène


# ── 4. Ligne de commande ────────────────────────────────────
OPTIONS = ["--methods", str(ROOT / "methods"), "--today", "2026-11-08"]


def test_rapport_markdown_sur_la_sortie_standard(capsys):
    assert report.main([str(REGISTRE), *OPTIONS]) == 0
    assert capsys.readouterr().out.startswith("# Rapport de risques — Organisation de test")


def test_rapport_html_dans_un_fichier(tmp_path):
    sortie = tmp_path / "rapports" / "rapport.html"
    assert report.main([str(REGISTRE), "--format", "html", "-o", str(sortie), *OPTIONS]) == 0
    page = sortie.read_text(encoding="utf-8")
    assert page.startswith('<!doctype html>\n<html lang="fr">')
    assert report.main([str(REGISTRE), "--format", "html", "-o", str(sortie), *OPTIONS]) == 2  # pas d'écrasement


def test_rapport_refuse_un_registre_invalide(tmp_path, capsys):
    casse = tmp_path / "r.toml"
    casse.write_text(REGISTRE.read_text(encoding="utf-8").replace('method = "iso27005-5x5"', 'method = "x"'),
                     encoding="utf-8")  # fmt: skip
    assert report.main([str(casse), *OPTIONS]) == 1
    assert "Rapport impossible" in capsys.readouterr().err
