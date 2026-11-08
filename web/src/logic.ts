/**
 * Calculs de l'interface, sans accès à la page (testables avec node --test) :
 * cartographies, filtres, tri, synthèse, plan d'action, revues, couleurs lisibles.
 *
 * Les échéances sont comparées à la date du jour de l'utilisateur (« today »), au format
 * AAAA-MM-JJ : la comparaison de deux chaînes de ce format suit l'ordre chronologique.
 */

import type { Measure, Method, RegisterDoc, Risk } from "./data.ts";

export type Which = "inherent" | "residual";
export type Situation = "below" | "accepted" | "expired" | "reducing" | "pending";

/** Date du jour, locale, au format AAAA-MM-JJ. */
export function localToday(now: Date = new Date()): string {
  const pad = (n: number): string => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

// ─────────────────────────────────────────────────────────────
// 1. Niveaux
// ─────────────────────────────────────────────────────────────
export function rank(method: Method, levelId: string): number {
  return method.levels.findIndex((l) => l.id === levelId);
}

export function aboveAppetite(method: Method, levelId: string): boolean {
  return rank(method, levelId) > rank(method, method.appetite);
}

/** Du plus grave au moins grave (résiduel, puis inhérent), puis par identifiant. */
export function sortRisks(method: Method, risks: readonly Risk[]): Risk[] {
  return [...risks].sort((a, b) =>
    rank(method, b.residual.level) - rank(method, a.residual.level)
    || rank(method, b.inherent.level) - rank(method, a.inherent.level)
    || a.id.localeCompare(b.id));
}

// ─────────────────────────────────────────────────────────────
// 2. Cartographie
// ─────────────────────────────────────────────────────────────
export interface HeatCell { readonly likelihood: number; readonly impact: number; readonly level: string; readonly ids: readonly string[] }
export interface HeatRow { readonly likelihood: number; readonly label: string; readonly cells: readonly HeatCell[] }

/** Lignes de la vraisemblance la plus forte à la plus faible ; une case par niveau d'impact. */
export function heatMap(method: Method, risks: readonly Risk[], which: Which): HeatRow[] {
  const rows: HeatRow[] = [];
  for (let l = method.likelihood.levels.length; l >= 1; l--) {
    const cells = method.impact.levels.map((_, index) => {
      const impact = index + 1;
      const ids = risks.filter((r) => r[which].likelihood === l && r[which].impact === impact).map((r) => r.id);
      return { likelihood: l, impact, level: method.grid[l - 1]?.[index] ?? "", ids };
    });
    rows.push({ likelihood: l, label: method.likelihood.levels[l - 1]?.label ?? String(l), cells });
  }
  return rows;
}

// ─────────────────────────────────────────────────────────────
// 3. Filtres
// ─────────────────────────────────────────────────────────────
export interface Filters {
  readonly status: "active" | "closed" | "all";
  readonly level: string; // niveau résiduel, "" = tous
  readonly owner: string; // "" = tous
  readonly treatment: string; // "" = tous
  readonly text: string;
  readonly cell: { readonly which: Which; readonly likelihood: number; readonly impact: number } | null;
}

export const NO_FILTER: Filters = { status: "active", level: "", owner: "", treatment: "", text: "", cell: null };

/** Recherche insensible à la casse et aux accents : « securite » trouve « Sécurité ». */
export function normalize(text: string): string {
  return text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
}

export function filterRisks(doc: RegisterDoc, f: Filters): Risk[] {
  const needle = normalize(f.text.trim());
  const kept = doc.risks.filter((r) =>
    (f.status === "all" || r.status === f.status)
    && (!f.level || r.residual.level === f.level)
    && (!f.owner || r.owner === f.owner)
    && (!f.treatment || r.treatment === f.treatment)
    && (!f.cell || (r[f.cell.which].likelihood === f.cell.likelihood && r[f.cell.which].impact === f.cell.impact))
    && (!needle || normalize([r.id, r.title, r.description, r.category, r.owner, r.threat, r.vulnerability, ...r.assets].join(" ")).includes(needle)));
  return sortRisks(doc.method, kept);
}

export function owners(doc: RegisterDoc): string[] {
  return [...new Set(doc.risks.map((r) => r.owner))].sort((a, b) => a.localeCompare(b));
}

// ─────────────────────────────────────────────────────────────
// 4. Situation, synthèse, plan d'action, revues
// ─────────────────────────────────────────────────────────────
export function situation(method: Method, risk: Risk, today: string): Situation {
  if (!aboveAppetite(method, risk.residual.level)) return "below";
  if (risk.acceptance) return risk.acceptance.until < today ? "expired" : "accepted";
  return risk.measures.some((m) => m.status !== "done") ? "reducing" : "pending";
}

export interface Summary {
  readonly active: number; readonly closed: number; readonly above: number;
  readonly openMeasures: number; readonly overdueMeasures: number;
  readonly overdueReviews: number; readonly expiredAcceptances: number;
  readonly byLevel: readonly { readonly level: string; readonly count: number }[];
}

export function summary(doc: RegisterDoc, today: string): Summary {
  const active = doc.risks.filter((r) => r.status === "active");
  const open = active.flatMap((r) => r.measures.filter((m) => m.status !== "done"));
  return {
    active: active.length,
    closed: doc.risks.length - active.length,
    above: active.filter((r) => aboveAppetite(doc.method, r.residual.level)).length,
    openMeasures: open.length,
    overdueMeasures: open.filter((m) => m.due < today).length,
    overdueReviews: active.filter((r) => r.review.next < today).length,
    expiredAcceptances: active.filter((r) => r.acceptance !== null && r.acceptance.until < today).length,
    byLevel: [...doc.method.levels].reverse().map((l) => ({ level: l.id, count: active.filter((r) => r.residual.level === l.id).length })),
  };
}

export interface PlanItem { readonly risk: Risk; readonly measure: Measure; readonly overdue: boolean }

/** Mesures ouvertes des risques actifs, par échéance. */
export function actionPlan(doc: RegisterDoc, today: string): PlanItem[] {
  return doc.risks
    .filter((r) => r.status === "active")
    .flatMap((risk) => risk.measures.filter((m) => m.status !== "done").map((measure) => ({ risk, measure, overdue: measure.due < today })))
    .sort((a, b) => a.measure.due.localeCompare(b.measure.due) || a.risk.id.localeCompare(b.risk.id));
}

export interface ReviewItem { readonly risk: Risk; readonly overdue: boolean }

export function reviews(doc: RegisterDoc, today: string): ReviewItem[] {
  return doc.risks
    .filter((r) => r.status === "active")
    .map((risk) => ({ risk, overdue: risk.review.next < today }))
    .sort((a, b) => a.risk.review.next.localeCompare(b.risk.review.next) || a.risk.id.localeCompare(b.risk.id));
}

// ─────────────────────────────────────────────────────────────
// 5. Couleurs : texte noir ou blanc, le plus lisible sur le fond (WCAG 2.x)
// ─────────────────────────────────────────────────────────────
export function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = Number.parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
}

export function textColor(background: string): "#000000" | "#ffffff" {
  return contrast(background, "#000000") >= contrast(background, "#ffffff") ? "#000000" : "#ffffff";
}

/** Format d'affichage d'une date AAAA-MM-JJ : 15/09/2027 en français, inchangée en anglais. */
export function formatDay(iso: string, lang: "fr" | "en"): string {
  return lang === "fr" ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : iso;
}
