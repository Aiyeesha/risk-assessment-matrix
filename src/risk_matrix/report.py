"""
Rapport de risques (commande « risk-report ») : Markdown ou HTML, dans la langue du registre.

Le rapport est d'abord décrit comme une suite de BLOCS (titres, paragraphes, listes, tableaux),
puis rendu par l'un des deux moteurs : les deux formats montrent donc exactement le même contenu.

Sections : synthèse, cartographies (risque inhérent et résiduel), risques par niveau, risques
au-dessus de l'appétence et leurs acceptations, plan d'action, calendrier des revues, références
(annexe A, playbooks, ATT&CK), risques clos, avertissements.

SÉCURITÉ du HTML : un seul fichier, sans script ni ressource externe. Tout texte du registre est
échappé ; la politique de sécurité du contenu (CSP) interdit tout sauf la feuille de style
intégrée, autorisée par son empreinte SHA-256. Les couleurs des niveaux passent par des classes
CSS (et non par des attributs « style », que cette CSP bloquerait).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from risk_matrix import __version__
from risk_matrix.check import load_register
from risk_matrix.cli import add_common_options, methods_dirs, missing_paths, write_output
from risk_matrix.console import setup_streams
from risk_matrix.method import Method
from risk_matrix.references import ANNEX_A, PLAYBOOKS, annex_a_theme, attack_url, playbook_url
from risk_matrix.register import Register, Risk, Score

# ─────────────────────────────────────────────────────────────
# 1. Textes du rapport, en français et en anglais
# ─────────────────────────────────────────────────────────────
LABELS = {
    "fr": {
        "title": "Rapport de risques — {org}",
        "method": "Méthode", "assessed": "Évaluation", "by": "par", "as_of": "Situation au",
        "summary": "Synthèse",
        "s_active": "{n} risque(s) actif(s), {c} clos",
        "s_above": "{n} au-dessus de l'appétence (« {appetite} »)",
        "s_measures": "{n} mesure(s) ouverte(s), dont {late} en retard",
        "s_warnings": "{n} avertissement(s) à traiter",
        "level": "Niveau résiduel", "risks": "Risques",
        "map_inherent": "Cartographie — risque inhérent", "map_residual": "Cartographie — risque résiduel",
        "map_note": "Chaque case indique son niveau et les risques actifs qui s'y trouvent.",
        "by_level": "Risques par niveau résiduel",
        "c_id": "ID", "c_risk": "Risque", "c_owner": "Responsable", "c_inherent": "Inhérent",
        "c_residual": "Résiduel", "c_treatment": "Traitement", "c_review": "Prochaine revue",
        "above": "Au-dessus de l'appétence", "c_situation": "Situation",
        "none_above": "Aucun risque actif au-dessus de l'appétence.",
        "accepted": "Accepté par {by} ({role}) jusqu'au {until}",
        "expired": "Acceptation expirée le {until} — à renouveler ou à traiter",
        "reducing": "Réduction en cours ({n} mesure(s) ouverte(s))",
        "plan": "Plan d'action", "c_due": "Échéance", "c_measure": "Mesure", "c_status": "État",
        "late": "En retard", "none_plan": "Aucune mesure ouverte.",
        "reviews": "Calendrier des revues", "c_date": "Date", "overdue": "En retard",
        "references": "Références",
        "annex_a": "ISO/IEC 27001:2022, annexe A", "c_theme": "Thème", "c_controls": "Mesures citées",
        "playbooks": "Playbooks de réponse aux incidents", "c_playbook": "Playbook",
        "attack": "Techniques MITRE ATT&CK", "c_technique": "Technique",
        "none_refs": "Aucune référence renseignée.",
        "closed": "Risques clos",
        "warnings": "Avertissements",
        "footer": "Généré par risk-assessment-matrix {version} le {today}.",
        "treatments": {"reduce": "Réduire", "accept": "Accepter", "transfer": "Transférer", "avoid": "Éviter"},
        "statuses": {"planned": "Prévue", "in-progress": "En cours", "done": "Terminée"},
    },
    "en": {
        "title": "Risk report — {org}",
        "method": "Method", "assessed": "Assessment", "by": "by", "as_of": "Status as of",
        "summary": "Summary",
        "s_active": "{n} active risk(s), {c} closed",
        "s_above": "{n} above the appetite (“{appetite}”)",
        "s_measures": "{n} open measure(s), {late} overdue",
        "s_warnings": "{n} warning(s) to address",
        "level": "Residual level", "risks": "Risks",
        "map_inherent": "Heat map — inherent risk", "map_residual": "Heat map — residual risk",
        "map_note": "Each cell shows its level and the active risks it holds.",
        "by_level": "Risks by residual level",
        "c_id": "ID", "c_risk": "Risk", "c_owner": "Owner", "c_inherent": "Inherent",
        "c_residual": "Residual", "c_treatment": "Treatment", "c_review": "Next review",
        "above": "Above the appetite", "c_situation": "Status",
        "none_above": "No active risk above the appetite.",
        "accepted": "Accepted by {by} ({role}) until {until}",
        "expired": "Acceptance expired on {until} — renew or treat",
        "reducing": "Reduction under way ({n} open measure(s))",
        "plan": "Action plan", "c_due": "Due", "c_measure": "Measure", "c_status": "Status",
        "late": "Overdue", "none_plan": "No open measure.",
        "reviews": "Review schedule", "c_date": "Date", "overdue": "Overdue",
        "references": "References",
        "annex_a": "ISO/IEC 27001:2022, Annex A", "c_theme": "Theme", "c_controls": "Controls cited",
        "playbooks": "Incident response playbooks", "c_playbook": "Playbook",
        "attack": "MITRE ATT&CK techniques", "c_technique": "Technique",
        "none_refs": "No reference given.",
        "closed": "Closed risks",
        "warnings": "Warnings",
        "footer": "Generated by risk-assessment-matrix {version} on {today}.",
        "treatments": {"reduce": "Reduce", "accept": "Accept", "transfer": "Transfer", "avoid": "Avoid"},
        "statuses": {"planned": "Planned", "in-progress": "In progress", "done": "Done"},
    },
}  # fmt: skip


def format_day(value: date, lang: str) -> str:
    """15/09/2027 en français, 2027-09-15 (ISO 8601) en anglais."""
    return value.strftime("%d/%m/%Y") if lang == "fr" else value.isoformat()


# ─────────────────────────────────────────────────────────────
# 2. Blocs du rapport, indépendants du format
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Cell:
    text: str
    level: str | None = None  # identifiant de niveau : couleur de la case
    note: str = ""  # précision affichée avant le texte (ex. libellé du niveau dans une cartographie)
    href: str | None = None  # lien
    strong: bool = False  # mise en évidence (retard)


@dataclass(frozen=True)
class Heading:
    text: str
    level: int = 2


@dataclass(frozen=True)
class Paragraph:
    text: str


@dataclass(frozen=True)
class Bullets:
    items: tuple[str, ...]


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[Cell, ...], ...]
    heat: bool = False  # cartographie : première colonne = niveau de vraisemblance


@dataclass
class Report:
    title: str
    lang: str
    meta: list[str] = field(default_factory=list)
    blocks: list[Heading | Paragraph | Bullets | Table] = field(default_factory=list)
    footer: str = ""


# ─────────────────────────────────────────────────────────────
# 3. Calculs
# ─────────────────────────────────────────────────────────────
def _residual(register: Register, risk: Risk) -> str:
    return register.residual_level(risk)


def ordered(register: Register, risks: list[Risk]) -> list[Risk]:
    """Du plus grave au moins grave (résiduel, puis inhérent), puis par identifiant."""
    rank = register.method.rank
    return sorted(
        risks,
        key=lambda r: (-rank(register.residual_level(r)), -rank(register.inherent_level(r)), r.id),
    )


def heat_rows(register: Register, risks: list[Risk], residual: bool) -> tuple[tuple[Cell, ...], ...]:
    """Une ligne par niveau de vraisemblance, du plus élevé au plus faible ; une case par impact."""
    method, lang = register.method, register.lang
    rows = []
    for likelihood in range(method.likelihood.size, 0, -1):
        row = [Cell(method.likelihood.levels[likelihood - 1].label.get(lang))]
        for impact in range(1, method.impact.size + 1):
            cell = Score(likelihood, impact)
            ids = [r.id for r in risks if (r.residual if residual else r.inherent) == cell]
            level = method.level_of(likelihood, impact)
            row.append(Cell(", ".join(ids), level=level.id, note=level.label.get(lang), strong=bool(ids)))
        rows.append(tuple(row))
    return tuple(rows)


def level_cell(method: Method, level_id: str, lang: str) -> Cell:
    return Cell(method.level(level_id).label.get(lang), level=level_id)


# ─────────────────────────────────────────────────────────────
# 4. Construction du rapport
# ─────────────────────────────────────────────────────────────
def build_report(register: Register, warnings: list[str], today: date) -> Report:
    lang, method = register.lang, register.method
    t = LABELS[lang]
    day = lambda d: format_day(d, lang)  # noqa: E731 — raccourci local, lisible
    active = ordered(register, [r for r in register.risks if r.status == "active"])
    closed = [r for r in register.risks if r.status == "closed"]
    above = [r for r in active if method.needs_acceptance(_residual(register, r))]
    open_measures = sorted(
        ((r, m) for r in active for m in r.measures if m.status != "done"), key=lambda rm: (rm[1].due, rm[0].id)
    )
    late = [rm for rm in open_measures if rm[1].due < today]
    sep = " : " if lang == "fr" else ": "  # typographie française : espace avant les deux-points

    report = Report(
        title=t["title"].format(org=register.organisation),
        lang=lang,
        meta=[
            f"{t['method']}{sep}{method.name.get(lang)}",
            f"{t['assessed']}{sep}{day(register.assessed_on)}, {t['by']} {register.assessor}",
            f"{t['as_of']}{sep}{day(today)}",
        ],
        footer=t["footer"].format(version=__version__, today=day(today)),
    )
    add = report.blocks.append

    # ── Synthèse ────────────────────────────────────────────
    add(Heading(t["summary"]))
    add(Bullets((
        t["s_active"].format(n=len(active), c=len(closed)),
        t["s_above"].format(n=len(above), appetite=method.level(method.appetite).label.get(lang)),
        t["s_measures"].format(n=len(open_measures), late=len(late)),
        t["s_warnings"].format(n=len(warnings)),
    )))  # fmt: skip
    counts = [
        (level_cell(method, lv.id, lang), Cell(str(sum(_residual(register, r) == lv.id for r in active))))
        for lv in reversed(method.levels)
    ]
    add(Table((t["level"], t["risks"]), tuple(counts)))

    # ── Cartographies ───────────────────────────────────────
    corner = f"{method.likelihood.name.get(lang)} ↓ / {method.impact.name.get(lang)} →"
    impacts = tuple(level.label.get(lang) for level in method.impact.levels)
    for key, residual in (("map_inherent", False), ("map_residual", True)):
        add(Heading(t[key]))
        add(Table((corner, *impacts), heat_rows(register, active, residual), heat=True))
    add(Paragraph(t["map_note"]))

    # ── Risques par niveau résiduel ─────────────────────────
    add(Heading(t["by_level"]))
    add(Table(
        (t["c_id"], t["c_risk"], t["c_owner"], t["c_inherent"], t["c_residual"], t["c_treatment"], t["c_review"]),
        tuple(
            (Cell(r.id), Cell(r.title), Cell(r.owner), level_cell(method, register.inherent_level(r), lang),
             level_cell(method, _residual(register, r), lang), Cell(t["treatments"][r.treatment]),
             Cell(day(r.review.next), strong=r.review.next < today))
            for r in active
        ),
    ))  # fmt: skip

    # ── Au-dessus de l'appétence ────────────────────────────
    add(Heading(t["above"]))
    if not above:
        add(Paragraph(t["none_above"]))
    else:
        rows = []
        for r in above:
            a = r.acceptance
            if a is not None and a.until < today:
                situation = Cell(t["expired"].format(until=day(a.until)), strong=True)
            elif a is not None:
                situation = Cell(t["accepted"].format(by=a.by, role=a.role, until=day(a.until)))
            else:
                situation = Cell(t["reducing"].format(n=sum(m.status != "done" for m in r.measures)))
            rows.append((Cell(r.id), Cell(r.title), level_cell(method, _residual(register, r), lang), situation))
        add(Table((t["c_id"], t["c_risk"], t["c_residual"], t["c_situation"]), tuple(rows)))

    # ── Plan d'action ───────────────────────────────────────
    add(Heading(t["plan"]))
    if not open_measures:
        add(Paragraph(t["none_plan"]))
    else:
        add(Table(
            (t["c_due"], t["c_id"], t["c_measure"], t["c_owner"], t["c_status"]),
            tuple(
                (Cell(day(m.due), strong=m.due < today), Cell(r.id), Cell(m.title), Cell(m.owner),
                 Cell(t["late"] if m.due < today else t["statuses"][m.status], strong=m.due < today))
                for r, m in open_measures
            ),
        ))  # fmt: skip

    # ── Calendrier des revues ───────────────────────────────
    add(Heading(t["reviews"]))
    add(Table(
        (t["c_date"], t["c_id"], t["c_risk"], t["c_residual"]),
        tuple(
            (Cell(day(r.review.next) + (f" — {t['overdue']}" if r.review.next < today else ""),
                  strong=r.review.next < today),
             Cell(r.id), Cell(r.title), level_cell(method, _residual(register, r), lang))
            for r in sorted(active, key=lambda r: (r.review.next, r.id))
        ),
    ))  # fmt: skip

    # ── Références ──────────────────────────────────────────
    add(Heading(t["references"]))
    themes: dict[int, set[str]] = {theme: set() for theme in ANNEX_A}
    for r in active:
        for control in (*r.iso27001, *(c for m in r.measures for c in m.iso27001)):
            themes[annex_a_theme(control)].add(control)
    playbooks: dict[str, list[str]] = {}
    techniques: dict[str, list[str]] = {}
    for r in active:
        for p in r.playbooks:
            playbooks.setdefault(p, []).append(r.id)
        for tech in r.attack:
            techniques.setdefault(tech, []).append(r.id)
    if not any(themes.values()) and not playbooks and not techniques:
        add(Paragraph(t["none_refs"]))
    if any(themes.values()):
        add(Heading(t["annex_a"], 3))
        key = lambda c: tuple(int(part) for part in c.split("."))  # noqa: E731 — 8.7 avant 8.13
        add(Table(
            (t["c_theme"], t["c_controls"]),
            tuple((Cell(f"{theme} — {name.get(lang)}"), Cell(", ".join(sorted(themes[theme], key=key)) or "·"))
                  for theme, (_count, name) in ANNEX_A.items()),
        ))  # fmt: skip
    if playbooks:
        add(Heading(t["playbooks"], 3))
        add(Table(
            (t["c_playbook"], t["risks"]),
            tuple((Cell(f"{p} — {PLAYBOOKS[p][0].get(lang)}", href=playbook_url(p, lang)), Cell(", ".join(ids)))
                  for p, ids in sorted(playbooks.items())),
        ))  # fmt: skip
    if techniques:
        add(Heading(t["attack"], 3))
        add(Table(
            (t["c_technique"], t["risks"]),
            tuple((Cell(tech, href=attack_url(tech)), Cell(", ".join(ids)))
                  for tech, ids in sorted(techniques.items())),
        ))  # fmt: skip

    # ── Risques clos et avertissements ──────────────────────
    if closed:
        add(Heading(t["closed"]))
        add(Table((t["c_id"], t["c_risk"]), tuple((Cell(r.id), Cell(r.title)) for r in closed)))
    if warnings:
        add(Heading(t["warnings"]))
        add(Bullets(tuple(warnings)))
    return report


# ─────────────────────────────────────────────────────────────
# 5. Rendu Markdown
# ─────────────────────────────────────────────────────────────
_MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|#~])")


def md(text: str) -> str:
    """Texte du registre rendu inerte en Markdown : caractères spéciaux échappés, une seule ligne."""
    return _MD_SPECIAL.sub(r"\\\1", " ".join(text.split()))


def _md_cell(cell: Cell) -> str:
    text = md(cell.text)
    if cell.href:
        text = f"[{text}]({cell.href})"  # liens construits par le programme, jamais par le registre
    if cell.strong and text:
        text = f"**{text}**"
    if cell.note:  # cartographie : « Élevé · **R01** », ou « Élevé » seul pour une case vide
        return f"{md(cell.note)} · {text}" if text else md(cell.note)
    return text


def render_markdown(report: Report) -> str:
    lines = [f"# {md(report.title)}", ""]
    lines += [f"- {md(item)}" for item in report.meta] + [""]
    for block in report.blocks:
        if isinstance(block, Heading):
            lines += ["#" * block.level + " " + md(block.text), ""]
        elif isinstance(block, Paragraph):
            lines += [md(block.text), ""]
        elif isinstance(block, Bullets):
            lines += [f"- {md(item)}" for item in block.items] + [""]
        else:
            lines.append("| " + " | ".join(md(h) for h in block.headers) + " |")
            lines.append("|" + "---|" * len(block.headers))
            lines += ["| " + " | ".join(_md_cell(c) for c in row) + " |" for row in block.rows]
            lines.append("")
    lines += ["---", "", f"*{md(report.footer)}*", ""]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 6. Rendu HTML : un fichier autonome, imprimable
# ─────────────────────────────────────────────────────────────
_BASE_CSS = """
:root { color-scheme: light dark; --fg: #1b1b1f; --bg: #ffffff; --muted: #5d5f66; --line: #d9dadf; --late: #b3261e; }
@media (prefers-color-scheme: dark) {
  :root { --fg: #e6e6ea; --bg: #16171b; --muted: #a5a7ae; --line: #3a3c43; --late: #ff8a80; }
}
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 72rem; padding: 2rem 1rem; font: 15px/1.5 system-ui, -apple-system, "Segoe UI",
  Roboto, sans-serif; color: var(--fg); background: var(--bg); }
h1 { font-size: 1.6rem; margin: 0 0 .5rem; }
h2 { font-size: 1.2rem; margin: 2rem 0 .6rem; padding-bottom: .2rem; border-bottom: 2px solid var(--line); }
h3 { font-size: 1rem; margin: 1.2rem 0 .4rem; }
.meta { list-style: none; padding: 0; margin: 0; color: var(--muted); }
.table { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin: .4rem 0 1rem; }
th, td { border: 1px solid var(--line); padding: .35rem .5rem; text-align: left; vertical-align: top; }
th { font-weight: 600; }
.heat td { text-align: center; min-width: 6rem; }
.heat th[scope="row"] { white-space: nowrap; }
.note { display: block; font-size: .75rem; opacity: .9; }
.level { font-weight: 600; }
.late { color: var(--late); font-weight: 700; }
a { color: inherit; }
footer { margin-top: 2.5rem; color: var(--muted); font-size: .85rem; }
@media print {
  body { max-width: none; padding: 0; font-size: 11px; }
  h2 { break-after: avoid; }
  table, tr { break-inside: avoid; }
  a { text-decoration: none; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
@page { size: A4 landscape; margin: 12mm; }
""".strip()


def _luminance(color: str) -> float:
    """Luminance relative WCAG 2.x d'une couleur #RRVVBB."""
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def text_color(background: str) -> str:
    """Noir ou blanc, selon celui qui contraste le plus avec le fond (rapport de contraste WCAG)."""
    lum = _luminance(background)
    return "#000000" if (lum + 0.05) / 0.05 >= 1.05 / (lum + 0.05) else "#ffffff"


def stylesheet(method: Method) -> str:
    """Feuille de style complète : base + une classe par niveau (identifiants et couleurs déjà validés)."""
    rules = [f".lv-{lv.id} {{ background: {lv.color}; color: {text_color(lv.color)}; }}" for lv in method.levels]
    return _BASE_CSS + "\n" + "\n".join(rules)


def _html_cell(cell: Cell, tag: str = "td", scope: str = "") -> str:
    e = html.escape
    text = e(cell.text)
    if cell.href:
        text = f'<a href="{e(cell.href)}" rel="noopener noreferrer">{text}</a>'
    if cell.strong and cell.text:
        text = f'<span class="late">{text}</span>' if not cell.level else f"<strong>{text}</strong>"
    if cell.note:
        text = f'<span class="note">{e(cell.note)}</span>{text}'
    classes = [f"lv-{cell.level}", "level-cell"] if cell.level else []
    attrs = (f' class="{" ".join(classes)}"' if classes else "") + (f' scope="{scope}"' if scope else "")
    return f"<{tag}{attrs}>{text}</{tag}>"


def render_html(report: Report, method: Method) -> str:
    e = html.escape
    css = stylesheet(method)
    digest = base64.b64encode(hashlib.sha256(css.encode("utf-8")).digest()).decode("ascii")
    csp = f"default-src 'none'; style-src 'sha256-{digest}'; img-src 'none'; base-uri 'none'; form-action 'none'"
    out = [
        "<!doctype html>",
        f'<html lang="{report.lang}">',
        "<head>",
        '<meta charset="utf-8">',
        f'<meta http-equiv="Content-Security-Policy" content="{csp}">',
        '<meta name="referrer" content="no-referrer">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{e(report.title)}</title>",
        f"<style>{css}</style>",
        "</head>",
        "<body>",
        "<header>",
        f"<h1>{e(report.title)}</h1>",
        '<ul class="meta">' + "".join(f"<li>{e(item)}</li>" for item in report.meta) + "</ul>",
        "</header>",
        "<main>",
    ]
    for block in report.blocks:
        if isinstance(block, Heading):
            out.append(f"<h{block.level}>{e(block.text)}</h{block.level}>")
        elif isinstance(block, Paragraph):
            out.append(f"<p>{e(block.text)}</p>")
        elif isinstance(block, Bullets):
            out.append("<ul>" + "".join(f"<li>{e(item)}</li>" for item in block.items) + "</ul>")
        else:
            heat = ' class="heat"' if block.heat else ""
            out.append(f'<div class="table"><table{heat}>')
            out.append("<thead><tr>" + "".join(f'<th scope="col">{e(h)}</th>' for h in block.headers) + "</tr></thead>")
            out.append("<tbody>")
            for row in block.rows:
                first = _html_cell(row[0], "th", "row") if block.heat else _html_cell(row[0])
                out.append("<tr>" + first + "".join(_html_cell(c) for c in row[1:]) + "</tr>")
            out.append("</tbody></table></div>")
    out += ["</main>", f"<footer>{e(report.footer)}</footer>", "</body>", "</html>", ""]
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────
# 7. Ligne de commande
# ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    setup_streams()
    parser = argparse.ArgumentParser(
        prog="risk-report", description="Produit le rapport d'un registre de risques vérifié (Markdown ou HTML)."
    )
    parser.add_argument("register", type=Path, help="registre (fichier TOML)")
    parser.add_argument("--format", choices=("md", "html"), default="md", help="format du rapport (défaut : md)")
    parser.add_argument("-o", "--output", type=Path, help="fichier de sortie (défaut : sortie standard)")
    parser.add_argument("--force", action="store_true", help="remplace le fichier de sortie s'il existe")
    add_common_options(parser)
    args = parser.parse_args(argv)

    root = Path.cwd()
    if missing_paths([args.register, *(args.methods or [])]):
        return 2
    today = args.today or date.today()
    register, problems = load_register(args.register, methods_dirs(args, root), today)
    if register is None:
        for problem in problems:
            print(problem.render(root), file=sys.stderr)
        print("Rapport impossible : corriger d'abord le registre (risk-check).", file=sys.stderr)
        return 1
    report = build_report(register, [p.message for p in problems if p.warning], today)
    text = render_html(report, register.method) if args.format == "html" else render_markdown(report)
    return 0 if write_output(args.output, text, args.force) else 2
