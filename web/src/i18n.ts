/**
 * Textes de l'interface, en français et en anglais.
 * Le CONTENU du registre reste dans sa propre langue ; seule l'interface change.
 */

import type { Lang } from "./data.ts";
import type { Situation } from "./logic.ts";

export const LANGS: readonly Lang[] = ["fr", "en"];

export interface Messages {
  readonly htmlTitle: string; readonly skip: string; readonly intro: string;
  readonly loadTitle: string; readonly example5x5: string; readonly exampleEbios: string; readonly openFile: string;
  readonly privacy: string; readonly loading: string; readonly loadError: string; readonly loaded: string;
  readonly method: string; readonly assessed: string; readonly exported: string; readonly today: string;
  readonly summaryTitle: string; readonly cardActive: string; readonly cardAbove: string; readonly cardOpen: string;
  readonly cardOverdue: string; readonly cardReviews: string; readonly cardExpired: string;
  readonly mapTitle: string; readonly inherent: string; readonly residual: string; readonly mapHint: string;
  readonly cellLabel: string; readonly cellEmpty: string;
  readonly filtersTitle: string; readonly fStatus: string; readonly fLevel: string; readonly fOwner: string;
  readonly fTreatment: string; readonly fSearch: string; readonly all: string; readonly reset: string;
  readonly cellFilter: string; readonly statusActive: string; readonly statusClosed: string; readonly statusAll: string;
  readonly risksTitle: string; readonly count: string; readonly noRisk: string;
  readonly cId: string; readonly cRisk: string; readonly cOwner: string; readonly cSituation: string;
  readonly cTreatment: string; readonly cReview: string; readonly cDue: string; readonly cMeasure: string; readonly cStatus: string;
  readonly details: string; readonly description: string; readonly assets: string; readonly threat: string;
  readonly vulnerability: string; readonly controls: string; readonly measures: string; readonly acceptance: string;
  readonly acceptedBy: string; readonly history: string; readonly references: string; readonly iso27001: string;
  readonly attack: string; readonly playbooks: string; readonly flags: string; readonly gdpr: string; readonly nis2: string;
  readonly justification: string; readonly transferTo: string; readonly none: string;
  readonly planTitle: string; readonly noPlan: string; readonly overdue: string;
  readonly reviewsTitle: string;
  readonly remember: string; readonly rememberHelp: string; readonly storageBlocked: string;
  readonly footer: string; readonly guide: string; readonly repo: string;
  readonly situations: Readonly<Record<Situation, string>>;
  readonly treatments: Readonly<Record<string, string>>;
  readonly measureStatuses: Readonly<Record<string, string>>;
}

export const MESSAGES: Readonly<Record<Lang, Messages>> = {
  fr: {
    htmlTitle: "Matrice des risques — cartographie, plan d'action et revues",
    skip: "Aller au contenu",
    intro: "Explorez un registre de risques exporté par risk-export : cartographies du risque inhérent et résiduel, risques au-dessus de l'appétence, plan d'action et revues.",
    loadTitle: "Registre",
    example5x5: "Exemple — méthode 5×5",
    exampleEbios: "Exemple — EBIOS RM 4×4",
    openFile: "Ouvrir un export JSON…",
    privacy: "Le fichier est lu dans votre navigateur : rien n'est envoyé, rien n'est conservé.",
    loading: "Chargement…",
    loadError: "Registre refusé",
    loaded: "Registre chargé : {org}",
    method: "Méthode", assessed: "Évaluation", exported: "Situation de l'export", today: "Échéances comparées au",
    summaryTitle: "Synthèse",
    cardActive: "risques actifs", cardAbove: "au-dessus de l'appétence", cardOpen: "mesures ouvertes",
    cardOverdue: "mesures en retard", cardReviews: "revues en retard", cardExpired: "acceptations expirées",
    mapTitle: "Cartographie", inherent: "Risque inhérent", residual: "Risque résiduel",
    mapHint: "Choisissez une case pour n'afficher que ses risques.",
    cellLabel: "{level} — vraisemblance {l}, impact {i} : {n} risque(s)", cellEmpty: "aucun",
    filtersTitle: "Filtres", fStatus: "État", fLevel: "Niveau résiduel", fOwner: "Responsable", fTreatment: "Traitement",
    fSearch: "Rechercher", all: "Tous", reset: "Réinitialiser", cellFilter: "Case : vraisemblance {l} × impact {i} ({which})",
    statusActive: "Actifs", statusClosed: "Clos", statusAll: "Tous",
    risksTitle: "Risques", count: "{n} risque(s)", noRisk: "Aucun risque ne correspond aux filtres.",
    cId: "ID", cRisk: "Risque", cOwner: "Responsable", cSituation: "Situation", cTreatment: "Traitement",
    cReview: "Prochaine revue", cDue: "Échéance", cMeasure: "Mesure", cStatus: "État",
    details: "Détail", description: "Description", assets: "Actifs", threat: "Menace", vulnerability: "Vulnérabilité",
    controls: "Mesures existantes", measures: "Mesures prévues", acceptance: "Acceptation formelle",
    acceptedBy: "{by} ({role}), du {on} au {until}", history: "Historique", references: "Références",
    iso27001: "ISO/IEC 27001:2022, annexe A", attack: "MITRE ATT&CK", playbooks: "Playbooks", flags: "Obligations",
    gdpr: "Données personnelles (RGPD)", nis2: "NIS 2", justification: "Justification du résiduel", transferTo: "Transféré à",
    none: "—",
    planTitle: "Plan d'action", noPlan: "Aucune mesure ouverte.", overdue: "En retard",
    reviewsTitle: "Calendrier des revues",
    remember: "Mémoriser la langue sur cet appareil",
    rememberHelp: "Seule la langue est conservée ; le registre ne l'est jamais.",
    storageBlocked: "Le stockage local est bloqué par ce navigateur.",
    footer: "Outil libre (licence MIT). Aucune donnée ne quitte votre navigateur.",
    guide: "Guide d'évaluation", repo: "Code source",
    situations: {
      below: "Sous l'appétence", accepted: "Accepté", expired: "Acceptation expirée",
      reducing: "Réduction en cours", pending: "À accepter",
    },
    treatments: { reduce: "Réduire", accept: "Accepter", transfer: "Transférer", avoid: "Éviter" },
    measureStatuses: { planned: "Prévue", "in-progress": "En cours", done: "Terminée" },
  },
  en: {
    htmlTitle: "Risk matrix — heat maps, action plan and reviews",
    skip: "Skip to content",
    intro: "Explore a risk register exported by risk-export: inherent and residual heat maps, risks above the appetite, action plan and reviews.",
    loadTitle: "Register",
    example5x5: "Example — 5×5 method",
    exampleEbios: "Example — EBIOS RM 4×4",
    openFile: "Open a JSON export…",
    privacy: "The file is read in your browser: nothing is sent, nothing is kept.",
    loading: "Loading…",
    loadError: "Register rejected",
    loaded: "Register loaded: {org}",
    method: "Method", assessed: "Assessment", exported: "Export status as of", today: "Deadlines compared with",
    summaryTitle: "Summary",
    cardActive: "active risks", cardAbove: "above the appetite", cardOpen: "open measures",
    cardOverdue: "overdue measures", cardReviews: "overdue reviews", cardExpired: "expired acceptances",
    mapTitle: "Heat map", inherent: "Inherent risk", residual: "Residual risk",
    mapHint: "Pick a cell to show only its risks.",
    cellLabel: "{level} — likelihood {l}, impact {i}: {n} risk(s)", cellEmpty: "none",
    filtersTitle: "Filters", fStatus: "Status", fLevel: "Residual level", fOwner: "Owner", fTreatment: "Treatment",
    fSearch: "Search", all: "All", reset: "Reset", cellFilter: "Cell: likelihood {l} × impact {i} ({which})",
    statusActive: "Active", statusClosed: "Closed", statusAll: "All",
    risksTitle: "Risks", count: "{n} risk(s)", noRisk: "No risk matches the filters.",
    cId: "ID", cRisk: "Risk", cOwner: "Owner", cSituation: "Status", cTreatment: "Treatment",
    cReview: "Next review", cDue: "Due", cMeasure: "Measure", cStatus: "Status",
    details: "Details", description: "Description", assets: "Assets", threat: "Threat", vulnerability: "Vulnerability",
    controls: "Existing controls", measures: "Planned measures", acceptance: "Formal acceptance",
    acceptedBy: "{by} ({role}), from {on} to {until}", history: "History", references: "References",
    iso27001: "ISO/IEC 27001:2022, Annex A", attack: "MITRE ATT&CK", playbooks: "Playbooks", flags: "Obligations",
    gdpr: "Personal data (GDPR)", nis2: "NIS 2", justification: "Residual justification", transferTo: "Transferred to",
    none: "—",
    planTitle: "Action plan", noPlan: "No open measure.", overdue: "Overdue",
    reviewsTitle: "Review schedule",
    remember: "Remember the language on this device",
    rememberHelp: "Only the language is kept; the register never is.",
    storageBlocked: "Local storage is blocked by this browser.",
    footer: "Free tool (MIT licence). No data leaves your browser.",
    guide: "Assessment guide", repo: "Source code",
    situations: {
      below: "Below the appetite", accepted: "Accepted", expired: "Acceptance expired",
      reducing: "Reduction under way", pending: "To be accepted",
    },
    treatments: { reduce: "Reduce", accept: "Accept", transfer: "Transfer", avoid: "Avoid" },
    measureStatuses: { planned: "Planned", "in-progress": "In progress", done: "Done" },
  },
};

/** Remplace les {clés} d'un message ; les valeurs restent du texte (insérées avec textContent). */
export function fill(template: string, values: Readonly<Record<string, string | number>>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) => (key in values ? String(values[key]) : match));
}

/** Langue initiale : préférence mémorisée, sinon celle du navigateur, sinon le français. */
export function pickLang(saved: string | null, navigatorLangs: readonly string[]): Lang {
  if (saved === "fr" || saved === "en") return saved;
  for (const tag of navigatorLangs) {
    const base = tag.slice(0, 2).toLowerCase();
    if (base === "fr" || base === "en") return base;
  }
  return "fr";
}
