"""
Import et export CSV du registre, pour travailler dans un tableur (Excel, LibreOffice Calc).

Deux fichiers, une ligne par élément :
  - risques  : une ligne par risque (identification, notes, traitement, acceptation, revue, références) ;
  - mesures  : une ligne par mesure, rattachée à son risque par « risk_id ».
L'historique n'a pas de colonne : il se tient dans le fichier TOML.

SÉCURITÉ — injection de formules (CSV injection, CWE-1236) : un tableur exécute une cellule qui
commence par « = », « + », « - » ou « @ » (ou par une tabulation ou un retour chariot, qui
précèdent parfois ces caractères). À l'EXPORT, une telle cellule est précédée d'une apostrophe,
que le tableur affiche comme du texte (recommandation de l'OWASP) ; à l'IMPORT, cette apostrophe
ajoutée est retirée, et la valeur reste du texte dans le fichier TOML, où elle ne peut rien exécuter.

Limites à l'import : 1 Mio par fichier, 5 000 lignes, UTF-8 (avec ou sans BOM).
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from risk_matrix.register import Register

# ─────────────────────────────────────────────────────────────
# 1. Réglages
# ─────────────────────────────────────────────────────────────
MAX_BYTES = 1_048_576
MAX_ROWS = 5_000
DANGEROUS = ("=", "+", "-", "@", "\t", "\r")  # premiers caractères interprétés par un tableur
LIST_SEPARATOR = " | "  # listes dans une cellule : « Messagerie | Virements »
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TRUE = {"true", "oui", "yes", "vrai", "1"}
_FALSE = {"false", "non", "no", "faux", "0"}

# Colonnes du fichier des risques, dans l'ordre. Les colonnes CALCULÉES (niveaux, mesures ouvertes)
# sont écrites à l'export pour la lecture et ignorées à l'import : elles viennent de la méthode.
RISK_COLUMNS = (
    "id", "title", "description", "category", "owner", "status",
    "assets", "threat", "vulnerability", "gdpr", "nis2",
    "inherent_likelihood", "inherent_impact", "inherent_level", "existing_controls",
    "residual_likelihood", "residual_impact", "residual_level", "residual_justification",
    "treatment", "transfer_to",
    "acceptance_by", "acceptance_role", "acceptance_on", "acceptance_until", "acceptance_rationale",
    "review_last", "review_next",
    "iso27001", "attack", "playbooks",
    "measures_open", "measures_total",
)  # fmt: skip
COMPUTED_COLUMNS = frozenset({"inherent_level", "residual_level", "measures_open", "measures_total"})
MEASURE_COLUMNS = ("risk_id", "title", "owner", "due", "status", "iso27001")
_LIST_COLUMNS = frozenset({"assets", "existing_controls", "iso27001", "attack", "playbooks"})
_INT_COLUMNS = frozenset({"inherent_likelihood", "inherent_impact", "residual_likelihood", "residual_impact"})
_DATE_COLUMNS = frozenset({"acceptance_on", "acceptance_until", "review_last", "review_next", "due"})
_BOOL_COLUMNS = frozenset({"gdpr", "nis2"})


# ─────────────────────────────────────────────────────────────
# 2. Protection des cellules
# ─────────────────────────────────────────────────────────────
def neutralize(value: str) -> str:
    """Cellule exportée : « =SOMME(A1) » devient « '=SOMME(A1) », affichée comme texte."""
    return "'" + value if value.startswith(DANGEROUS) else value


def restore(value: str) -> str:
    """Cellule importée : retire l'apostrophe ajoutée par neutralize(), et seulement celle-là."""
    return value[1:] if value.startswith("'") and value[1:].startswith(DANGEROUS) else value


# ─────────────────────────────────────────────────────────────
# 3. Export : registre → lignes de texte
# ─────────────────────────────────────────────────────────────
def _boolean(value: bool, lang: str) -> str:
    return {("fr", True): "oui", ("fr", False): "non", ("en", True): "yes", ("en", False): "no"}[(lang, value)]


def _day(value: date | None) -> str:
    return value.isoformat() if value else ""


def risk_rows(register: Register) -> list[dict[str, str]]:
    rows = []
    for risk in register.risks:
        acceptance = risk.acceptance
        rows.append({
            "id": risk.id,
            "title": risk.title,
            "description": risk.description,
            "category": risk.category,
            "owner": risk.owner,
            "status": risk.status,
            "assets": LIST_SEPARATOR.join(risk.assets),
            "threat": risk.threat,
            "vulnerability": risk.vulnerability,
            "gdpr": _boolean(risk.gdpr, register.lang),
            "nis2": _boolean(risk.nis2, register.lang),
            "inherent_likelihood": str(risk.inherent.likelihood),
            "inherent_impact": str(risk.inherent.impact),
            "inherent_level": register.method.level(register.inherent_level(risk)).label.get(register.lang),
            "existing_controls": LIST_SEPARATOR.join(risk.existing_controls),
            "residual_likelihood": str(risk.residual.likelihood),
            "residual_impact": str(risk.residual.impact),
            "residual_level": register.method.level(register.residual_level(risk)).label.get(register.lang),
            "residual_justification": risk.residual_justification,
            "treatment": risk.treatment,
            "transfer_to": risk.transfer_to,
            "acceptance_by": acceptance.by if acceptance else "",
            "acceptance_role": acceptance.role if acceptance else "",
            "acceptance_on": _day(acceptance.on if acceptance else None),
            "acceptance_until": _day(acceptance.until if acceptance else None),
            "acceptance_rationale": acceptance.rationale if acceptance else "",
            "review_last": _day(risk.review.last),
            "review_next": _day(risk.review.next),
            "iso27001": LIST_SEPARATOR.join(risk.iso27001),
            "attack": LIST_SEPARATOR.join(risk.attack),
            "playbooks": LIST_SEPARATOR.join(risk.playbooks),
            "measures_open": str(sum(m.status != "done" for m in risk.measures)),
            "measures_total": str(len(risk.measures)),
        })  # fmt: skip
    return rows


def measure_rows(register: Register) -> list[dict[str, str]]:
    return [
        {
            "risk_id": risk.id,
            "title": m.title,
            "owner": m.owner,
            "due": _day(m.due),
            "status": m.status,
            "iso27001": LIST_SEPARATOR.join(m.iso27001),
        }
        for risk in register.risks
        for m in risk.measures
    ]


def write_csv(rows: Iterable[dict[str, str]], columns: tuple[str, ...], delimiter: str) -> str:
    """Texte CSV, chaque cellule protégée contre l'injection de formules."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=delimiter, lineterminator="\r\n")  # fin de ligne attendue par Excel
    writer.writerow(columns)
    for row in rows:
        writer.writerow(neutralize(row[c]) for c in columns)
    return out.getvalue()


# ─────────────────────────────────────────────────────────────
# 4. Import : fichier CSV → lignes de texte vérifiées
# ─────────────────────────────────────────────────────────────
class CsvError(Exception):
    """Fichier CSV inutilisable : message et numéro de ligne (si connu)."""

    def __init__(self, message: str, line: int | None = None) -> None:
        super().__init__(message)
        self.message, self.line = message, line


def read_csv(path: Path, columns: tuple[str, ...], delimiter: str | None = None) -> list[tuple[int, dict[str, str]]]:
    """
    Lit un CSV dont l'en-tête n'utilise que des colonnes connues ; renvoie [(n° de ligne, cellules)].
    Lève CsvError pour un fichier inutilisable (taille, encodage, en-tête, structure).
    """
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise CsvError(f"fichier trop volumineux ({size} octets, maximum {MAX_BYTES})")
    try:
        text = path.read_bytes().decode("utf-8-sig")  # « -sig » : retire le BOM ajouté par Excel
    except UnicodeDecodeError as exc:
        raise CsvError(
            f"encodage invalide (octet {exc.start}) : enregistrer le fichier au format « CSV UTF-8 »"
        ) from None
    first_line = text.split("\n", 1)[0]
    if delimiter is None:  # point-virgule pour un Excel français, virgule sinon
        delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    try:
        header = next(reader, None)
        if not header or not any(cell.strip() for cell in header):
            raise CsvError("fichier vide : une ligne d'en-tête est attendue", 1)
        header = [cell.strip() for cell in header]
        unknown = [c for c in header if c not in columns]
        if unknown:
            raise CsvError(f"colonne(s) inconnue(s) : {', '.join(unknown)} (attendues : {', '.join(columns)})", 1)
        duplicated = sorted({c for c in header if header.count(c) > 1})
        if duplicated:
            raise CsvError(f"colonne(s) en double : {', '.join(duplicated)}", 1)
        if columns[0] not in header:
            raise CsvError(f"colonne « {columns[0]} » obligatoire", 1)

        rows = []
        for cells in reader:
            if not any(cell.strip() for cell in cells):
                continue  # ligne vide, fréquente en fin de fichier
            if len(rows) >= MAX_ROWS:
                raise CsvError(f"plus de {MAX_ROWS} lignes", reader.line_num)
            if len(cells) != len(header):
                raise CsvError(f"{len(cells)} cellules pour {len(header)} colonnes", reader.line_num)
            rows.append((reader.line_num, {c: restore(v.strip()) for c, v in zip(header, cells, strict=True)}))
        return rows
    except csv.Error as exc:  # guillemet non fermé, cellule démesurée…
        raise CsvError(f"structure CSV invalide : {exc}", reader.line_num) from None


# ─────────────────────────────────────────────────────────────
# 5. Import : lignes → données de registre (même forme que le TOML lu)
# ─────────────────────────────────────────────────────────────
class _Converter:
    """Convertit les cellules en valeurs typées et collecte les erreurs (ligne, message)."""

    def __init__(self) -> None:
        self.errors: list[tuple[int, str]] = []

    def value(self, line: int, column: str, raw: str) -> object:
        if raw == "":
            return None  # cellule vide : clé absente du TOML
        if column in _LIST_COLUMNS:
            return [item.strip() for item in raw.split("|") if item.strip()]
        if column in _INT_COLUMNS:
            if not raw.isdigit():
                self.errors.append((line, f"colonne « {column} » : entier attendu (« {raw} »)"))
                return None
            return int(raw)
        if column in _DATE_COLUMNS:
            try:
                if not _DAY.match(raw):
                    raise ValueError
                return date.fromisoformat(raw)
            except ValueError:
                self.errors.append((line, f"colonne « {column} » : date AAAA-MM-JJ attendue (« {raw} »)"))
                return None
        if column in _BOOL_COLUMNS:
            if raw.lower() in _TRUE:
                return True
            if raw.lower() in _FALSE:
                return False
            self.errors.append((line, f"colonne « {column} » : oui ou non attendu (« {raw} »)"))
            return None
        return raw


def _group(cells: dict[str, object], mapping: dict[str, str]) -> dict[str, object] | None:
    """Regroupe des colonnes en table TOML : {"review_last": d} → {"last": d} ; None si tout est vide."""
    table = {key: cells[column] for column, key in mapping.items() if cells.get(column) is not None}
    return table or None


def rows_to_register(
    header: dict[str, object],
    risks: list[tuple[int, dict[str, str]]],
    measures: list[tuple[int, dict[str, str]]] = (),
) -> tuple[dict, list[tuple[str, int, str]]]:
    """
    Données de registre (dictionnaire prêt pour parse_register et l'écriture TOML) et erreurs de
    conversion sous la forme (fichier « risks » ou « measures », ligne, message).
    """
    conv = _Converter()
    errors: list[tuple[str, int, str]] = []
    data: dict[str, object] = {"kind": "register", "format": 1, **header, "risks": []}
    by_id: dict[str, dict] = {}

    for line, row in risks:
        cells = {c: conv.value(line, c, v) for c, v in row.items() if c not in COMPUTED_COLUMNS}
        risk: dict[str, object] = {}
        for key in ("id", "title", "description", "category", "owner", "status", "assets", "threat",
                    "vulnerability", "gdpr", "nis2"):  # fmt: skip
            if cells.get(key) is not None:
                risk[key] = cells[key]
        if inherent := _group(cells, {"inherent_likelihood": "likelihood", "inherent_impact": "impact"}):
            risk["inherent"] = inherent
        if cells.get("existing_controls") is not None:
            risk["existing_controls"] = cells["existing_controls"]
        residual = _group(cells, {"residual_likelihood": "likelihood", "residual_impact": "impact",
                                  "residual_justification": "justification"})  # fmt: skip
        if residual:
            risk["residual"] = residual
        if cells.get("treatment") is not None:
            risk["treatment"] = cells["treatment"]
        if cells.get("transfer_to") is not None:
            risk["transfer"] = {"to": cells["transfer_to"]}
        acceptance = _group(cells, {f"acceptance_{k}": k for k in ("by", "role", "on", "until", "rationale")})
        if acceptance:
            risk["acceptance"] = acceptance
        if review := _group(cells, {"review_last": "last", "review_next": "next"}):
            risk["review"] = review
        for key in ("iso27001", "attack", "playbooks"):
            if cells.get(key) is not None:
                risk[key] = cells[key]
        risk_id = str(risk.get("id", ""))
        if risk_id in by_id:
            errors.append(("risks", line, f"identifiant « {risk_id} » en double"))
        elif risk_id:
            by_id[risk_id] = risk
        data["risks"].append(risk)
    errors += [("risks", line, message) for line, message in conv.errors]

    conv = _Converter()
    for line, row in measures:
        cells = {c: conv.value(line, c, v) for c, v in row.items()}
        target = by_id.get(str(cells.get("risk_id") or ""))
        if target is None:
            errors.append(("measures", line, f"risque « {cells.get('risk_id') or ''} » absent du fichier des risques"))
            continue
        measure = {k: cells[k] for k in ("title", "owner", "due", "status", "iso27001") if cells.get(k) is not None}
        target.setdefault("measures", []).append(measure)
    errors += [("measures", line, message) for line, message in conv.errors]
    return data, errors
