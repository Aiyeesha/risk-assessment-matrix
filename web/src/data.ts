/**
 * Lecture et validation d'un export JSON de « risk-export » (schema_version 1).
 *
 * Un fichier ouvert par l'utilisateur n'est PAS digne de confiance : tout est vérifié avant
 * affichage (types, dates, couleurs, cohérence de la grille), et seuls les liens vers MITRE ATT&CK
 * et vers le dépôt des playbooks sont gardés comme liens. Toute anomalie lève une DataError
 * au message lisible : rien n'est affiché à moitié.
 */

export const SCHEMA_VERSION = 1;
export const MAX_BYTES = 2 * 1024 * 1024; // 2 Mio : bien au-delà d'un registre réel
export type Lang = "fr" | "en";

// Liens autorisés (préfixes) : tout autre lien est affiché comme du texte
export const LINK_PREFIXES = [
  "https://attack.mitre.org/techniques/",
  "https://github.com/Aiyeesha/incident-response-playbook/",
] as const;

// ─────────────────────────────────────────────────────────────
// 1. Types (miroir de risk_matrix/export.py)
// ─────────────────────────────────────────────────────────────
export interface AxisLevel { readonly value: number; readonly label: string; readonly description: string }
export interface Axis { readonly name: string; readonly levels: readonly AxisLevel[] }
export interface Level {
  readonly id: string; readonly label: string; readonly color: string;
  readonly reviewMonths: number; readonly guidance: string;
}
export interface Authority { readonly level: string; readonly by: string; readonly maxMonths: number }
export interface Method {
  readonly id: string; readonly name: string; readonly references: readonly string[];
  readonly likelihood: Axis; readonly impact: Axis; readonly levels: readonly Level[];
  readonly grid: readonly (readonly string[])[]; readonly appetite: string;
  readonly authorities: readonly Authority[];
}
export interface Score { readonly likelihood: number; readonly impact: number; readonly level: string }
export interface Reference { readonly id: string; readonly label: string; readonly url: string | null }
export interface Measure {
  readonly title: string; readonly owner: string; readonly due: string;
  readonly status: "planned" | "in-progress" | "done"; readonly iso27001: readonly Reference[];
}
export interface Acceptance {
  readonly by: string; readonly role: string; readonly on: string; readonly until: string; readonly rationale: string;
}
export interface Risk {
  readonly id: string; readonly title: string; readonly description: string; readonly category: string;
  readonly owner: string; readonly status: "active" | "closed"; readonly assets: readonly string[];
  readonly threat: string; readonly vulnerability: string; readonly gdpr: boolean; readonly nis2: boolean;
  readonly inherent: Score; readonly existingControls: readonly string[]; readonly measures: readonly Measure[];
  readonly residual: Score; readonly justification: string;
  readonly treatment: "reduce" | "accept" | "transfer" | "avoid"; readonly transferTo: string;
  readonly acceptance: Acceptance | null; readonly review: { readonly last: string; readonly next: string };
  readonly history: readonly { readonly on: string; readonly by: string; readonly change: string }[];
  readonly iso27001: readonly Reference[]; readonly attack: readonly Reference[]; readonly playbooks: readonly Reference[];
}
export interface RegisterDoc {
  readonly asOf: string;
  readonly generator: string;
  readonly register: { readonly organisation: string; readonly lang: Lang; readonly assessedOn: string; readonly assessor: string };
  readonly method: Method;
  readonly risks: readonly Risk[];
}

export class DataError extends Error {}

// ─────────────────────────────────────────────────────────────
// 2. Lecteur : chaque accès vérifie le type et indique le chemin fautif
// ─────────────────────────────────────────────────────────────
type Obj = Record<string, unknown>;
const DAY = /^\d{4}-\d{2}-\d{2}$/;
const COLOR = /^#[0-9a-fA-F]{6}$/;

function fail(path: string, message: string): never {
  throw new DataError(`${path} : ${message}`);
}
function obj(v: unknown, path: string): Obj {
  if (typeof v !== "object" || v === null || Array.isArray(v)) fail(path, "objet attendu");
  return v as Obj;
}
function arr(v: unknown, path: string): unknown[] {
  if (!Array.isArray(v)) fail(path, "liste attendue");
  return v;
}
function str(v: unknown, path: string, allowEmpty = true): string {
  if (typeof v !== "string" || (!allowEmpty && v.trim() === "")) fail(path, "texte attendu");
  return v;
}
function int(v: unknown, path: string, min = 1): number {
  if (typeof v !== "number" || !Number.isInteger(v) || v < min) fail(path, `entier ≥ ${min} attendu`);
  return v;
}
function bool(v: unknown, path: string): boolean {
  if (typeof v !== "boolean") fail(path, "true ou false attendu");
  return v;
}
function day(v: unknown, path: string): string {
  const s = str(v, path);
  // Le motif ET une date réelle : « 2026-02-30 » est refusé
  if (!DAY.test(s) || new Date(`${s}T00:00:00Z`).toISOString().slice(0, 10) !== s) fail(path, "date AAAA-MM-JJ attendue");
  return s;
}
function oneOf<T extends string>(v: unknown, path: string, allowed: readonly T[]): T {
  if (typeof v !== "string" || !allowed.includes(v as T)) fail(path, `« ${allowed.join(" », « ")} » attendu`);
  return v as T;
}
function strings(v: unknown, path: string): string[] {
  return arr(v, path).map((item, i) => str(item, `${path}[${i}]`));
}

/** Lien gardé seulement s'il pointe vers un site autorisé (https, préfixe connu). */
export function safeUrl(v: unknown): string | null {
  return typeof v === "string" && LINK_PREFIXES.some((prefix) => v.startsWith(prefix)) ? v : null;
}

// ─────────────────────────────────────────────────────────────
// 3. Méthode
// ─────────────────────────────────────────────────────────────
function axis(v: unknown, path: string): Axis {
  const o = obj(v, path);
  const levels = arr(o["levels"], `${path}.levels`).map((item, i) => {
    const l = obj(item, `${path}.levels[${i}]`);
    const value = int(l["value"], `${path}.levels[${i}].value`);
    if (value !== i + 1) fail(`${path}.levels[${i}].value`, `${i + 1} attendu`);
    return { value, label: str(l["label"], `${path}.levels[${i}].label`, false), description: str(l["description"], `${path}.levels[${i}].description`) };
  });
  if (levels.length < 2 || levels.length > 7) fail(`${path}.levels`, "de 2 à 7 niveaux attendus");
  return { name: str(o["name"], `${path}.name`, false), levels };
}

function method(v: unknown): Method {
  const o = obj(v, "method");
  const likelihood = axis(o["likelihood"], "method.likelihood");
  const impact = axis(o["impact"], "method.impact");
  const levels = arr(o["levels"], "method.levels").map((item, i) => {
    const l = obj(item, `method.levels[${i}]`);
    const color = str(l["color"], `method.levels[${i}].color`);
    if (!COLOR.test(color)) fail(`method.levels[${i}].color`, "couleur #RRVVBB attendue");
    return {
      id: str(l["id"], `method.levels[${i}].id`, false), label: str(l["label"], `method.levels[${i}].label`, false),
      color, reviewMonths: int(l["review_months"], `method.levels[${i}].review_months`),
      guidance: str(l["guidance"], `method.levels[${i}].guidance`),
    };
  });
  const ids = levels.map((l) => l.id);
  if (ids.length < 2 || new Set(ids).size !== ids.length) fail("method.levels", "au moins deux niveaux, identifiants uniques");
  // Grille : une ligne par vraisemblance, une case par impact, chaque case = niveau connu
  const grid = arr(o["grid"], "method.grid").map((row, r) =>
    arr(row, `method.grid[${r}]`).map((cell, c) => oneOf(cell, `method.grid[${r}][${c}]`, ids)));
  if (grid.length !== likelihood.levels.length || grid.some((row) => row.length !== impact.levels.length)) {
    fail("method.grid", `${likelihood.levels.length} × ${impact.levels.length} cases attendues`);
  }
  const authorities = arr(o["authorities"], "method.authorities").map((item, i) => {
    const a = obj(item, `method.authorities[${i}]`);
    return {
      level: oneOf(a["level"], `method.authorities[${i}].level`, ids), by: str(a["by"], `method.authorities[${i}].by`, false),
      maxMonths: int(a["max_months"], `method.authorities[${i}].max_months`),
    };
  });
  return {
    id: str(o["id"], "method.id", false), name: str(o["name"], "method.name", false),
    references: strings(o["references"], "method.references"), likelihood, impact, levels, grid,
    appetite: oneOf(o["appetite"], "method.appetite", ids), authorities,
  };
}

// ─────────────────────────────────────────────────────────────
// 4. Risques
// ─────────────────────────────────────────────────────────────
function score(v: unknown, path: string, m: Method): Score {
  const o = obj(v, path);
  const likelihood = int(o["likelihood"], `${path}.likelihood`);
  const impact = int(o["impact"], `${path}.impact`);
  if (likelihood > m.likelihood.levels.length || impact > m.impact.levels.length) fail(path, "note hors des échelles de la méthode");
  const level = m.grid[likelihood - 1]?.[impact - 1] ?? "";
  // Le niveau doit être celui de la grille : un export retouché à la main est détecté
  if (o["level"] !== level) fail(`${path}.level`, `« ${level} » attendu d'après la grille`);
  return { likelihood, impact, level };
}

function refs(v: unknown, path: string, label: (o: Obj) => string): Reference[] {
  return arr(v, path).map((item, i) => {
    const o = obj(item, `${path}[${i}]`);
    return { id: str(o["id"], `${path}[${i}].id`, false), label: label(o), url: safeUrl(o["url"]) };
  });
}
const themeLabel = (o: Obj): string => (typeof o["theme"] === "string" ? o["theme"] : "");
const titleLabel = (o: Obj): string => (typeof o["title"] === "string" ? o["title"] : "");

function risk(v: unknown, i: number, m: Method): Risk {
  const p = `risks[${i}]`;
  const o = obj(v, p);
  const id = str(o["id"], `${p}.id`, false);
  const at = id; // messages suivants : « R03.residual… »
  const residual = obj(o["residual"], `${at}.residual`);
  const review = obj(o["review"], `${at}.review`);
  const acceptance = o["acceptance"] === null || o["acceptance"] === undefined ? null : obj(o["acceptance"], `${at}.acceptance`);
  return {
    id, title: str(o["title"], `${at}.title`, false), description: str(o["description"], `${at}.description`),
    category: str(o["category"], `${at}.category`), owner: str(o["owner"], `${at}.owner`, false),
    status: oneOf(o["status"], `${at}.status`, ["active", "closed"] as const),
    assets: strings(o["assets"], `${at}.assets`), threat: str(o["threat"], `${at}.threat`),
    vulnerability: str(o["vulnerability"], `${at}.vulnerability`), gdpr: bool(o["gdpr"], `${at}.gdpr`),
    nis2: bool(o["nis2"], `${at}.nis2`), inherent: score(o["inherent"], `${at}.inherent`, m),
    existingControls: strings(o["existing_controls"], `${at}.existing_controls`),
    measures: arr(o["measures"], `${at}.measures`).map((item, j) => {
      const mo = obj(item, `${at}.measures[${j}]`);
      return {
        title: str(mo["title"], `${at}.measures[${j}].title`, false), owner: str(mo["owner"], `${at}.measures[${j}].owner`),
        due: day(mo["due"], `${at}.measures[${j}].due`),
        status: oneOf(mo["status"], `${at}.measures[${j}].status`, ["planned", "in-progress", "done"] as const),
        iso27001: refs(mo["iso27001"], `${at}.measures[${j}].iso27001`, themeLabel),
      };
    }),
    residual: score(residual, `${at}.residual`, m), justification: str(residual["justification"] ?? "", `${at}.residual.justification`),
    treatment: oneOf(o["treatment"], `${at}.treatment`, ["reduce", "accept", "transfer", "avoid"] as const),
    transferTo: str(o["transfer_to"] ?? "", `${at}.transfer_to`),
    acceptance: acceptance && {
      by: str(acceptance["by"], `${at}.acceptance.by`), role: str(acceptance["role"], `${at}.acceptance.role`),
      on: day(acceptance["on"], `${at}.acceptance.on`), until: day(acceptance["until"], `${at}.acceptance.until`),
      rationale: str(acceptance["rationale"], `${at}.acceptance.rationale`),
    },
    review: { last: day(review["last"], `${at}.review.last`), next: day(review["next"], `${at}.review.next`) },
    history: arr(o["history"], `${at}.history`).map((item, j) => {
      const h = obj(item, `${at}.history[${j}]`);
      return { on: day(h["on"], `${at}.history[${j}].on`), by: str(h["by"], `${at}.history[${j}].by`), change: str(h["change"], `${at}.history[${j}].change`) };
    }),
    iso27001: refs(o["iso27001"], `${at}.iso27001`, themeLabel),
    attack: refs(o["attack"], `${at}.attack`, () => ""),
    playbooks: refs(o["playbooks"], `${at}.playbooks`, titleLabel),
  };
}

// ─────────────────────────────────────────────────────────────
// 5. Export complet
// ─────────────────────────────────────────────────────────────
export function parseExport(raw: unknown): RegisterDoc {
  const o = obj(raw, "export");
  if (o["schema_version"] !== SCHEMA_VERSION) {
    fail("schema_version", `format ${String(o["schema_version"])} non pris en charge (attendu : ${SCHEMA_VERSION}) — exporter le registre avec risk-export`);
  }
  const reg = obj(o["register"], "register");
  const m = method(o["method"]);
  const risks = arr(o["risks"], "risks").map((item, i) => risk(item, i, m));
  const ids = risks.map((r) => r.id);
  if (new Set(ids).size !== ids.length) fail("risks", "identifiants en double");
  return {
    asOf: day(o["as_of"], "as_of"),
    generator: str(o["generator"], "generator"),
    register: {
      organisation: str(reg["organisation"], "register.organisation", false),
      lang: oneOf(reg["lang"], "register.lang", ["fr", "en"] as const),
      assessedOn: day(reg["assessed_on"], "register.assessed_on"),
      assessor: str(reg["assessor"], "register.assessor"),
    },
    method: m,
    risks,
  };
}

/** Texte d'un fichier → registre validé (taille et syntaxe JSON vérifiées d'abord). */
export function parseText(text: string): RegisterDoc {
  if (text.length > MAX_BYTES) throw new DataError(`fichier trop volumineux (maximum ${MAX_BYTES / 1024 / 1024} Mio)`);
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    throw new DataError("ce fichier n'est pas du JSON valide — exporter le registre avec « risk-export registre.toml -o registre.json »");
  }
  return parseExport(raw);
}
