"""
Registre de risques : lecture et vérification d'un fichier TOML « kind = "register" ».

Le registre s'appuie sur une MÉTHODE (référencée par son identifiant) : les échelles, la grille,
l'appétence et les autorités d'acceptation viennent d'elle. Deux sortes de messages :
  - ERREURS : donnée invalide ou incohérente (le registre ne peut pas être utilisé tel quel) ;
  - AVERTISSEMENTS : ce qui est échu à la date du jour (revue, mesure ou acceptation dépassée).
    Le fichier est valide, mais demande une action.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import date

from risk_matrix.method import Method, _Reader
from risk_matrix.references import PLAYBOOKS, annex_a_theme, is_attack_id

# ─────────────────────────────────────────────────────────────
# 1. Réglages
# ─────────────────────────────────────────────────────────────
FORMAT_VERSION = 1
TREATMENTS = ("reduce", "accept", "transfer", "avoid")  # réduire, accepter, transférer, éviter
RISK_STATUSES = ("active", "closed")  # « closed » : risque disparu (actif retiré, activité arrêtée…)
MEASURE_STATUSES = ("planned", "in-progress", "done")
_RISK_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")  # « R01 », « RH-03 », « CYB-12 »

_REGISTER_KEYS = {"kind", "format", "method", "lang", "organisation", "assessed_on", "assessor", "risks"}
_RISK_KEYS = {
    "id",
    "title",
    "description",
    "category",
    "owner",
    "status",
    "assets",
    "threat",
    "vulnerability",
    "gdpr",
    "nis2",
    "inherent",
    "existing_controls",
    "measures",
    "residual",
    "treatment",
    "transfer",
    "acceptance",
    "review",
    "history",
    "iso27001",
    "attack",
    "playbooks",
}
_MEASURE_KEYS = {"title", "owner", "due", "status", "iso27001"}


def add_months(start: date, months: int) -> date:
    """Même jour, « months » mois plus tard (ramené au dernier jour du mois si besoin : 31 janv. + 1 → 28/29 févr.)."""
    month_index = start.month - 1 + months
    year, month = start.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


# ─────────────────────────────────────────────────────────────
# 2. Modèle
# ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Score:
    likelihood: int
    impact: int

    def exceeds(self, other: Score) -> bool:
        """Vrai si l'un des deux axes est plus élevé que dans « other »."""
        return self.likelihood > other.likelihood or self.impact > other.impact


@dataclass(frozen=True)
class Measure:
    title: str
    owner: str
    due: date
    status: str
    iso27001: tuple[str, ...] = ()  # mesures de l'annexe A mises en œuvre par cette action


@dataclass(frozen=True)
class Acceptance:
    by: str
    role: str
    on: date
    until: date
    rationale: str


@dataclass(frozen=True)
class Review:
    last: date
    next: date


@dataclass(frozen=True)
class HistoryEntry:
    on: date
    by: str
    change: str


@dataclass(frozen=True)
class Risk:
    id: str
    title: str
    description: str
    category: str
    owner: str
    status: str
    assets: tuple[str, ...]
    threat: str
    vulnerability: str
    gdpr: bool
    nis2: bool
    inherent: Score
    existing_controls: tuple[str, ...]
    measures: tuple[Measure, ...]
    residual: Score
    residual_justification: str
    treatment: str
    transfer_to: str
    acceptance: Acceptance | None
    review: Review
    history: tuple[HistoryEntry, ...]
    iso27001: tuple[str, ...] = ()  # mesures de l'annexe A d'ISO/IEC 27001:2022 qui traitent le risque
    attack: tuple[str, ...] = ()  # techniques MITRE ATT&CK du scénario
    playbooks: tuple[str, ...] = ()  # playbooks à appliquer si le risque se réalise


@dataclass(frozen=True)
class Register:
    method: Method
    lang: str
    organisation: str
    assessed_on: date
    assessor: str
    risks: tuple[Risk, ...]

    def inherent_level(self, risk: Risk) -> str:
        return self.method.level_of(risk.inherent.likelihood, risk.inherent.impact).id

    def residual_level(self, risk: Risk) -> str:
        return self.method.level_of(risk.residual.likelihood, risk.residual.impact).id


@dataclass
class Findings:
    """Erreurs et avertissements d'un registre, dans l'ordre du fichier."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# 3. Lecteur enrichi : dates, booléens, listes de textes
# ─────────────────────────────────────────────────────────────
class _RegisterReader(_Reader):
    def day(self, data: object, path: str) -> date:
        # tomllib renvoie un « date » pour 2026-11-08, un « datetime » si l'heure est donnée : on veut le jour seul
        if type(data) is not date:
            self.error(path, "date attendue au format AAAA-MM-JJ, sans guillemets")
            return date.min
        return data

    def boolean(self, data: object, path: str, default: bool = False) -> bool:
        if data is None:
            return default
        if not isinstance(data, bool):
            self.error(path, "true ou false attendu")
            return default
        return data

    def strings(self, data: object, path: str) -> tuple[str, ...]:
        return tuple(self.string(item, f"{path}[{i}]") for i, item in enumerate(self.array(data, path)))

    def optional(self, data: object, path: str) -> str:
        """Texte facultatif : absent → "", présent → non vide."""
        return "" if data is None else self.string(data, path)

    def references(self, data: object, path: str, kind: str) -> tuple[str, ...]:
        """Liste d'identifiants d'un référentiel (« iso27001 », « attack » ou « playbooks »), sans doublon."""
        if data is None:
            return ()
        values = self.strings(data, path)
        for i, value in enumerate(values):
            if not value:
                continue  # déjà signalé (texte vide)
            if kind == "iso27001" and annex_a_theme(value) is None:
                self.error(
                    f"{path}[{i}]",
                    f"« {value} » n'est pas une mesure de l'annexe A d'ISO/IEC 27001:2022 "
                    "(5.1 à 5.37, 6.1 à 6.8, 7.1 à 7.14, 8.1 à 8.34)",
                )
            elif kind == "attack" and not is_attack_id(value):
                self.error(f"{path}[{i}]", f"« {value} » n'est pas un identifiant ATT&CK (T1234 ou T1234.001)")
            elif kind == "playbooks" and value not in PLAYBOOKS:
                self.error(f"{path}[{i}]", f"playbook « {value} » inconnu ({', '.join(PLAYBOOKS)})")
            if value in values[:i]:
                self.error(f"{path}[{i}]", f"« {value} » en double")
        return values

    def choice(self, data: object, path: str, allowed: tuple[str, ...]) -> str:
        if data not in allowed:
            self.error(path, f"« {' », « '.join(allowed)} » attendu")
            return allowed[0]
        return str(data)

    def score(self, data: object, path: str, method: Method, extra: frozenset[str] = frozenset()) -> Score:
        """Note { likelihood = …, impact = … }, bornée par les échelles de la méthode."""
        table = self.table(data, path)
        self.unknown_keys(table, {"likelihood", "impact"} | extra, path)
        values = []
        for axis_key, axis in (("likelihood", method.likelihood), ("impact", method.impact)):
            value = self.integer(table.get(axis_key), f"{path}.{axis_key}")
            if value > axis.size:
                self.error(
                    f"{path}.{axis_key}", f"{value} hors échelle (1 à {axis.size} dans la méthode « {method.id} »)"
                )
                value = axis.size
            values.append(value)
        return Score(*values)


# ─────────────────────────────────────────────────────────────
# 4. Vérification d'un risque
# ─────────────────────────────────────────────────────────────
def _risk(
    r: _RegisterReader, item: object, where: str, method: Method, lang: str, today: date, warn: list[str]
) -> Risk:
    data = r.table(item, where)
    risk_id = r.string(data.get("id"), f"{where}.id")
    if risk_id and not _RISK_ID.match(risk_id):
        r.error(f"{where}.id", f"identifiant « {risk_id} » invalide (majuscules, chiffres et tirets, ex. R01)")
    at = risk_id or where  # les messages suivants désignent le risque par son identifiant : « R03.residual »
    r.unknown_keys(data, _RISK_KEYS, at)

    status = r.choice(data.get("status", "active"), f"{at}.status", RISK_STATUSES)
    inherent = r.score(data.get("inherent"), f"{at}.inherent", method)
    residual_data = data.get("residual")
    residual = r.score(residual_data, f"{at}.residual", method, frozenset({"justification"}))
    justification = ""
    if isinstance(residual_data, dict) and "justification" in residual_data:
        justification = r.string(residual_data["justification"], f"{at}.residual.justification")

    # ── Risque résiduel : jamais au-dessus de l'inhérent sans explication ──
    if residual.exceeds(inherent) and not justification:
        r.error(f"{at}.residual", "supérieur au risque inhérent sur un axe : ajouter « justification »")

    # ── Mesures prévues ─────────────────────────────────────
    measures = []
    for j, measure_item in enumerate(r.array(data.get("measures", []), f"{at}.measures")):
        mwhere = f"{at}.measures[{j}]"
        m = r.table(measure_item, mwhere)
        r.unknown_keys(m, _MEASURE_KEYS, mwhere)
        measure = Measure(
            r.string(m.get("title"), f"{mwhere}.title"),
            r.string(m.get("owner"), f"{mwhere}.owner"),
            r.day(m.get("due"), f"{mwhere}.due"),
            r.choice(m.get("status"), f"{mwhere}.status", MEASURE_STATUSES),
            r.references(m.get("iso27001"), f"{mwhere}.iso27001", "iso27001"),
        )
        if status == "active" and measure.status != "done" and date.min < measure.due < today:
            warn.append(f"{mwhere} : mesure en retard (échéance {measure.due.isoformat()}) — « {measure.title} »")
        measures.append(measure)

    # ── Traitement ──────────────────────────────────────────
    treatment = r.choice(data.get("treatment"), f"{at}.treatment", TREATMENTS)
    transfer = r.table(data.get("transfer", {}), f"{at}.transfer")
    r.unknown_keys(transfer, {"to"}, f"{at}.transfer")
    transfer_to = r.string(transfer["to"], f"{at}.transfer.to") if "to" in transfer else ""
    if treatment == "reduce" and not measures:
        r.error(f"{at}.measures", "traitement « reduce » sans aucune mesure de réduction")
    if treatment == "transfer" and not transfer_to:
        r.error(
            f"{at}.transfer.to",
            "traitement « transfer » : préciser à qui le risque est transféré (assureur, prestataire…)",
        )
    if treatment != "transfer" and transfer_to:
        r.error(f"{at}.transfer", "renseigné alors que le traitement n'est pas « transfer »")

    # ── Acceptation formelle ────────────────────────────────
    acceptance = None
    if "acceptance" in data:
        awhere = f"{at}.acceptance"
        a = r.table(data["acceptance"], awhere)
        r.unknown_keys(a, {"by", "role", "on", "until", "rationale"}, awhere)
        acceptance = Acceptance(
            r.string(a.get("by"), f"{awhere}.by"),
            r.string(a.get("role"), f"{awhere}.role"),
            r.day(a.get("on"), f"{awhere}.on"),
            r.day(a.get("until"), f"{awhere}.until"),
            r.string(a.get("rationale"), f"{awhere}.rationale"),
        )
    residual_level = method.level_of(residual.likelihood, residual.impact).id
    above = method.needs_acceptance(residual_level)
    # Le risque résiduel reste au-dessus de l'appétence et rien n'est plus en cours pour le réduire :
    # il est, de fait, accepté — cela doit être une décision formelle (ISO/IEC 27001, 6.1.3 f)
    treatment_over = treatment == "accept" or not any(m.status != "done" for m in measures)
    if status == "active" and above and treatment_over and acceptance is None:
        r.error(
            f"{at}.acceptance",
            f"risque résiduel « {residual_level} » au-dessus de l'appétence : acceptation formelle requise",
        )
    if acceptance is not None and date.min not in (acceptance.on, acceptance.until):
        authority = method.authority(residual_level)
        if acceptance.until <= acceptance.on:
            r.error(f"{at}.acceptance.until", "doit être postérieure à la date d'acceptation (« on »)")
        if authority is not None:
            expected_role = authority.by.get(lang)
            if acceptance.role != expected_role:
                r.error(
                    f"{at}.acceptance.role",
                    f"« {expected_role} » attendu pour un risque « {residual_level} » (méthode « {method.id} »)",
                )
            limit = add_months(acceptance.on, authority.max_months)
            if acceptance.until > limit:
                r.error(
                    f"{at}.acceptance.until",
                    f"au-delà de {authority.max_months} mois pour un risque « {residual_level} » "
                    f"(au plus tard {limit.isoformat()})",
                )
        if status == "active" and acceptance.until < today:
            warn.append(
                f"{at}.acceptance : acceptation expirée le {acceptance.until.isoformat()} — à renouveler ou à traiter"
            )

    # ── Revue ───────────────────────────────────────────────
    rwhere = f"{at}.review"
    rv = r.table(data.get("review"), rwhere)
    r.unknown_keys(rv, {"last", "next"}, rwhere)
    review = Review(r.day(rv.get("last"), f"{rwhere}.last"), r.day(rv.get("next"), f"{rwhere}.next"))
    if date.min not in (review.last, review.next):
        months = method.level(residual_level).review_months
        if review.next <= review.last:
            r.error(f"{rwhere}.next", "doit être postérieure à la dernière revue (« last »)")
        elif review.next > add_months(review.last, months):
            r.error(
                f"{rwhere}.next",
                f"trop éloignée : un risque « {residual_level} » se revoit tous les {months} mois au plus",
            )
        if status == "active" and review.next < today:
            warn.append(f"{rwhere} : revue en retard (prévue le {review.next.isoformat()})")

    # ── Historique : dates croissantes ──────────────────────
    history = []
    for j, entry_item in enumerate(r.array(data.get("history", []), f"{at}.history")):
        hwhere = f"{at}.history[{j}]"
        h = r.table(entry_item, hwhere)
        r.unknown_keys(h, {"on", "by", "change"}, hwhere)
        entry = HistoryEntry(
            r.day(h.get("on"), f"{hwhere}.on"),
            r.string(h.get("by"), f"{hwhere}.by"),
            r.string(h.get("change"), f"{hwhere}.change"),
        )
        if history and entry.on < history[-1].on:
            r.error(f"{hwhere}.on", "historique à tenir dans l'ordre chronologique")
        if entry.on > today:
            r.error(f"{hwhere}.on", f"date future ({entry.on.isoformat()})")
        history.append(entry)

    return Risk(
        id=risk_id,
        title=r.string(data.get("title"), f"{at}.title"),
        description=r.optional(data.get("description"), f"{at}.description"),
        category=r.optional(data.get("category"), f"{at}.category"),
        owner=r.string(data.get("owner"), f"{at}.owner"),
        status=status,
        assets=r.strings(data.get("assets"), f"{at}.assets"),
        threat=r.string(data.get("threat"), f"{at}.threat"),
        vulnerability=r.string(data.get("vulnerability"), f"{at}.vulnerability"),
        gdpr=r.boolean(data.get("gdpr"), f"{at}.gdpr"),
        nis2=r.boolean(data.get("nis2"), f"{at}.nis2"),
        inherent=inherent,
        existing_controls=r.strings(data.get("existing_controls", []), f"{at}.existing_controls"),
        measures=tuple(measures),
        residual=residual,
        residual_justification=justification,
        treatment=treatment,
        transfer_to=transfer_to,
        acceptance=acceptance,
        review=review,
        history=tuple(history),
        iso27001=r.references(data.get("iso27001"), f"{at}.iso27001", "iso27001"),
        attack=r.references(data.get("attack"), f"{at}.attack", "attack"),
        playbooks=r.references(data.get("playbooks"), f"{at}.playbooks", "playbooks"),
    )


# ─────────────────────────────────────────────────────────────
# 5. Vérification du registre complet
# ─────────────────────────────────────────────────────────────
def parse_register(data: dict, methods: dict[str, Method], today: date) -> tuple[Register | None, Findings]:
    """Vérifie un registre déjà lu depuis TOML ; « methods » : méthodes disponibles, par identifiant."""
    r = _RegisterReader()
    findings = Findings()
    r.unknown_keys(data, _REGISTER_KEYS, "")
    if data.get("format") != FORMAT_VERSION:
        r.error("format", f"{FORMAT_VERSION} attendu (version du format de fichier)")
    lang = r.choice(data.get("lang"), "lang", ("fr", "en"))
    organisation = r.string(data.get("organisation"), "organisation")
    assessed_on = r.day(data.get("assessed_on"), "assessed_on")
    assessor = r.string(data.get("assessor"), "assessor")
    if assessed_on > today:
        r.error("assessed_on", f"date future ({assessed_on.isoformat()})")

    method_id = r.string(data.get("method"), "method")
    method = methods.get(method_id)
    if method is None:
        known = ", ".join(sorted(methods)) or "aucune"
        r.error("method", f"méthode « {method_id} » introuvable (disponibles : {known})")
        findings.errors = r.errors
        return None, findings  # sans méthode, impossible de vérifier les scores

    risks = [
        _risk(r, item, f"risks[{i}]", method, lang, today, findings.warnings)
        for i, item in enumerate(r.array(data.get("risks"), "risks"))
    ]
    if not risks:
        r.error("risks", "au moins un risque attendu")
    ids = [risk.id for risk in risks if risk.id]
    for duplicate in sorted({i for i in ids if ids.count(i) > 1}):
        r.error("risks", f"identifiant « {duplicate} » en double")

    findings.errors = r.errors
    if findings.errors:
        return None, findings
    return Register(method, lang, organisation, assessed_on, assessor, tuple(risks)), findings
