"""
Méthode d'évaluation des risques : lecture et vérification d'un fichier TOML « kind = "method" ».

Une méthode décrit, en français ET en anglais :
  - deux axes : la vraisemblance et l'impact (appelé « gravité » dans EBIOS RM), chacun avec
    ses niveaux numérotés de 1 à n ;
  - les niveaux de risque, du moins grave au plus grave (couleur, fréquence de revue) ;
  - la GRILLE : le niveau de risque de chaque case vraisemblance × impact. Elle est explicite,
    case par case, pour couvrir aussi bien une matrice 5×5 que les zones d'EBIOS RM ;
  - l'appétence au risque et les règles d'acceptation : qui peut accepter un risque
    au-dessus de l'appétence, et pour combien de temps au plus.

Toutes les erreurs sont collectées (pas d'arrêt à la première) et désignent le champ fautif
par son chemin, par exemple « likelihood.levels[2].label.en ».
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────
# 1. Réglages
# ─────────────────────────────────────────────────────────────
LANGS = ("fr", "en")
FORMAT_VERSION = 1  # version du format de fichier « méthode »
AXIS_SIZES = range(3, 8)  # de 3 à 7 niveaux par axe : en dessous, trop grossier ; au-delà, illisible
_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")  # identifiant : « ebios-rm-4x4 », « high »
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")  # couleur hexadécimale : « #b3261e »


# ─────────────────────────────────────────────────────────────
# 2. Modèle
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Text:
    """Un texte dans les deux langues."""

    fr: str
    en: str

    def get(self, lang: str) -> str:
        return self.fr if lang == "fr" else self.en


@dataclass(frozen=True)
class AxisLevel:
    value: int  # 1 = le plus faible
    label: Text
    description: Text


@dataclass(frozen=True)
class Axis:
    name: Text
    levels: tuple[AxisLevel, ...]

    @property
    def size(self) -> int:
        return len(self.levels)


@dataclass(frozen=True)
class RiskLevel:
    id: str
    label: Text
    color: str
    review_months: int  # fréquence de revue des risques de ce niveau
    guidance: Text  # ce que l'organisation fait d'un risque de ce niveau


@dataclass(frozen=True)
class Authority:
    """Qui peut accepter un risque d'un niveau donné, et pour combien de temps au plus."""

    level: str
    by: Text
    max_months: int


@dataclass(frozen=True)
class Method:
    id: str
    name: Text
    references: tuple[str, ...]
    likelihood: Axis
    impact: Axis
    levels: tuple[RiskLevel, ...]  # du moins grave au plus grave
    grid: tuple[
        tuple[str, ...], ...
    ]  # grid[vraisemblance - 1][impact - 1] = identifiant de niveau (table [grid] du fichier)
    appetite: str  # niveau le plus élevé acceptable sans acceptation formelle
    authorities: tuple[Authority, ...]

    def level_of(self, likelihood: int, impact: int) -> RiskLevel:
        """Niveau de risque d'une case (valeurs à partir de 1)."""
        return self.level(self.grid[likelihood - 1][impact - 1])

    def level(self, level_id: str) -> RiskLevel:
        return next(level for level in self.levels if level.id == level_id)

    def rank(self, level_id: str) -> int:
        """0 pour le niveau le moins grave, puis 1, 2…"""
        return [level.id for level in self.levels].index(level_id)

    def needs_acceptance(self, level_id: str) -> bool:
        """Un risque au-dessus de l'appétence exige une acceptation formelle s'il est accepté."""
        return self.rank(level_id) > self.rank(self.appetite)

    def authority(self, level_id: str) -> Authority | None:
        return next((a for a in self.authorities if a.level == level_id), None)


# ─────────────────────────────────────────────────────────────
# 3. Lecture vérifiée
# ─────────────────────────────────────────────────────────────
class _Reader:
    """Lit les champs un à un et COLLECTE les erreurs, avec le chemin de chaque champ."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path} : {message}")

    def table(self, data: object, path: str) -> dict:
        if not isinstance(data, dict):
            self.error(path, "table attendue")
            return {}
        return data

    def array(self, data: object, path: str) -> list:
        if not isinstance(data, list):
            self.error(path, "liste attendue")
            return []
        return data

    def string(self, data: object, path: str) -> str:
        if not isinstance(data, str) or not data.strip():
            self.error(path, "texte non vide attendu")
            return ""
        return data.strip()

    def integer(self, data: object, path: str, minimum: int = 1) -> int:
        # bool est un sous-type d'int en Python : « true » ne doit pas passer pour 1
        if not isinstance(data, int) or isinstance(data, bool) or data < minimum:
            self.error(path, f"entier supérieur ou égal à {minimum} attendu")
            return minimum
        return data

    def identifier(self, data: object, path: str) -> str:
        value = self.string(data, path)
        if value and not _ID.match(value):
            self.error(path, f"identifiant invalide « {value} » (minuscules, chiffres et tirets)")
        return value

    def text(self, data: object, path: str) -> Text:
        """Texte bilingue : { fr = "…", en = "…" }, et rien d'autre."""
        table = self.table(data, path)
        for extra in sorted(set(table) - set(LANGS)):
            self.error(f"{path}.{extra}", "langue inconnue (fr et en seulement)")
        return Text(*(self.string(table.get(lang), f"{path}.{lang}") for lang in LANGS))

    def unknown_keys(self, table: dict, allowed: set[str], path: str) -> None:
        """Une clé inconnue est presque toujours une faute de frappe : on la signale."""
        for key in sorted(set(table) - allowed):
            self.error(f"{path}.{key}" if path else key, "clé inconnue")


def _axis(r: _Reader, data: object, path: str) -> Axis:
    table = r.table(data, path)
    r.unknown_keys(table, {"name", "levels"}, path)
    levels = []
    for i, item in enumerate(r.array(table.get("levels"), f"{path}.levels")):
        where = f"{path}.levels[{i}]"
        level = r.table(item, where)
        r.unknown_keys(level, {"value", "label", "description"}, where)
        value = r.integer(level.get("value"), f"{where}.value")
        if value != i + 1:
            r.error(f"{where}.value", f"{i + 1} attendu (niveaux numérotés 1, 2, 3… dans l'ordre)")
        levels.append(
            AxisLevel(
                value,
                r.text(level.get("label"), f"{where}.label"),
                r.text(level.get("description"), f"{where}.description"),
            )
        )
    if len(levels) not in AXIS_SIZES:
        r.error(f"{path}.levels", f"de {AXIS_SIZES.start} à {AXIS_SIZES.stop - 1} niveaux attendus ({len(levels)})")
    return Axis(r.text(table.get("name"), f"{path}.name"), tuple(levels))


def parse_method(data: dict) -> tuple[Method | None, list[str]]:
    """Vérifie une méthode déjà lue depuis TOML ; renvoie (méthode, []) ou (None, erreurs)."""
    r = _Reader()
    r.unknown_keys(
        data, {"kind", "format", "id", "name", "references", "likelihood", "impact", "levels", "grid", "acceptance"}, ""
    )
    if data.get("format") != FORMAT_VERSION:
        r.error("format", f"{FORMAT_VERSION} attendu (version du format de fichier)")
    method_id = r.identifier(data.get("id"), "id")
    name = r.text(data.get("name"), "name")
    references = tuple(
        r.string(ref, f"references[{i}]") for i, ref in enumerate(r.array(data.get("references", []), "references"))
    )
    likelihood = _axis(r, data.get("likelihood"), "likelihood")
    impact = _axis(r, data.get("impact"), "impact")

    # ── Niveaux de risque, du moins grave au plus grave ─────
    levels: list[RiskLevel] = []
    for i, item in enumerate(r.array(data.get("levels"), "levels")):
        where = f"levels[{i}]"
        level = r.table(item, where)
        r.unknown_keys(level, {"id", "label", "color", "review_months", "guidance"}, where)
        color = r.string(level.get("color"), f"{where}.color")
        if color and not _COLOR.match(color):
            r.error(f"{where}.color", f"couleur « {color} » invalide (format #RRVVBB)")
        levels.append(
            RiskLevel(
                r.identifier(level.get("id"), f"{where}.id"),
                r.text(level.get("label"), f"{where}.label"),
                color,
                r.integer(level.get("review_months"), f"{where}.review_months"),
                r.text(level.get("guidance"), f"{where}.guidance"),
            )
        )
    ids = [level.id for level in levels]
    if len(levels) < 2:
        r.error("levels", "au moins deux niveaux de risque attendus")
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
        r.error("levels", f"identifiant « {duplicate} » en double")
    # Un risque plus grave ne se revoit jamais MOINS souvent qu'un risque moins grave
    for lower, higher in zip(levels, levels[1:], strict=False):
        if higher.review_months > lower.review_months:
            r.error("levels", f"« {higher.id} » revu moins souvent ({higher.review_months} mois) que « {lower.id} »")

    # ── Grille : table [grid], une ligne par vraisemblance (1 en premier), une colonne par impact ──
    # (une table dédiée : une clé « grid » écrite après un bloc [[levels]] lui appartiendrait en TOML)
    grid_table = r.table(data.get("grid"), "grid")
    r.unknown_keys(grid_table, {"rows"}, "grid")
    rows = r.array(grid_table.get("rows"), "grid.rows")
    if len(rows) != likelihood.size:
        r.error("grid.rows", f"{likelihood.size} lignes attendues, une par niveau de vraisemblance ({len(rows)})")
    grid: list[tuple[str, ...]] = []
    for i, row in enumerate(rows):
        cells = r.array(row, f"grid.rows[{i}]")
        if len(cells) != impact.size:
            r.error(f"grid.rows[{i}]", f"{impact.size} cases attendues, une par niveau d'impact ({len(cells)})")
        for j, cell in enumerate(cells):
            if cell not in ids:
                r.error(f"grid.rows[{i}][{j}]", f"niveau inconnu « {cell} »")
        grid.append(tuple(str(c) for c in cells))
    shape_ok = len(grid) == likelihood.size and all(len(row) == impact.size for row in grid)
    cells_ok = shape_ok and all(cell in ids for row in grid for cell in row)
    if cells_ok:
        rank = {level_id: n for n, level_id in enumerate(ids)}
        # Monotonie : plus de vraisemblance ou plus d'impact ne rend JAMAIS un risque moins grave
        for i in range(likelihood.size):
            for j in range(impact.size):
                if j + 1 < impact.size and rank[grid[i][j + 1]] < rank[grid[i][j]]:
                    r.error(
                        f"grid.rows[{i}][{j + 1}]",
                        f"« {grid[i][j + 1]} » moins grave que la case à sa gauche (« {grid[i][j]} »)",
                    )
                if i + 1 < likelihood.size and rank[grid[i + 1][j]] < rank[grid[i][j]]:
                    r.error(
                        f"grid.rows[{i + 1}][{j}]",
                        f"« {grid[i + 1][j]} » moins grave que la case de la ligne précédente (« {grid[i][j]} »)",
                    )
        for unused in [level_id for level_id in ids if not any(level_id in row for row in grid)]:
            r.error("grid.rows", f"niveau « {unused} » jamais utilisé dans la grille")

    # ── Appétence et autorités d'acceptation ────────────────
    acceptance = r.table(data.get("acceptance"), "acceptance")
    r.unknown_keys(acceptance, {"appetite", "authorities"}, "acceptance")
    appetite = r.identifier(acceptance.get("appetite"), "acceptance.appetite")
    if appetite and appetite not in ids:
        r.error("acceptance.appetite", f"niveau inconnu « {appetite} »")
    authorities: list[Authority] = []
    for i, item in enumerate(r.array(acceptance.get("authorities"), "acceptance.authorities")):
        where = f"acceptance.authorities[{i}]"
        entry = r.table(item, where)
        r.unknown_keys(entry, {"level", "by", "max_months"}, where)
        authorities.append(
            Authority(
                r.identifier(entry.get("level"), f"{where}.level"),
                r.text(entry.get("by"), f"{where}.by"),
                r.integer(entry.get("max_months"), f"{where}.max_months"),
            )
        )
    if appetite in ids and len(set(ids)) == len(ids):
        above = ids[ids.index(appetite) + 1 :]
        declared = [a.level for a in authorities]
        for level_id in above:
            if declared.count(level_id) != 1:
                r.error(
                    "acceptance.authorities",
                    f"une autorité attendue pour le niveau « {level_id} » (au-dessus de l'appétence)",
                )
        for level_id in sorted(set(declared) - set(above)):
            r.error(
                "acceptance.authorities",
                f"« {level_id} » n'est pas au-dessus de l'appétence : aucune autorité à déclarer",
            )
        # Plus le risque est grave, plus l'acceptation doit être revue tôt
        by_rank = sorted((a for a in authorities if a.level in above), key=lambda a: ids.index(a.level))
        for lower, higher in zip(by_rank, by_rank[1:], strict=False):
            if higher.max_months > lower.max_months:
                r.error(
                    "acceptance.authorities",
                    f"acceptation de « {higher.level} » plus longue que celle de « {lower.level} »",
                )

    if r.errors:
        return None, r.errors
    return Method(
        method_id, name, references, likelihood, impact, tuple(levels), tuple(grid), appetite, tuple(authorities)
    ), []
