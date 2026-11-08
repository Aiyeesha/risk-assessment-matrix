/**
 * Liaison entre la page (index.html) et les modules (data, logic, i18n, storage).
 *
 * Sécurité :
 *   - le texte est TOUJOURS inséré avec textContent, jamais innerHTML : un registre piégé ne peut
 *     pas injecter de code ;
 *   - un fichier ouvert est lu localement (File.text()) ; la seule requête réseau lit les exemples
 *     de CE site (CSP : connect-src 'self') ;
 *   - les couleurs des niveaux, déjà validées (#RRVVBB), passent par le CSSOM (element.style),
 *     que la CSP autorise, et non par des attributs style ;
 *   - seuls les liens ATT&CK et playbooks validés par data.ts deviennent des liens.
 */

import { DataError, parseText, type Lang, type Level, type Reference, type RegisterDoc, type Risk } from "./data.ts";
import {
  actionPlan, filterRisks, formatDay, heatMap, localToday, NO_FILTER, owners, reviews, situation, summary, textColor,
  type Filters, type Which,
} from "./logic.ts";
import { fill, MESSAGES, pickLang, type Messages } from "./i18n.ts";
import * as storage from "./storage.ts";

const GUIDE: Readonly<Record<Lang, string>> = {
  fr: "https://github.com/Aiyeesha/risk-assessment-matrix/blob/main/docs/fr/guide-evaluation.md",
  en: "https://github.com/Aiyeesha/risk-assessment-matrix/blob/main/docs/en/assessment-guide.md",
};

// ─────────────────────────────────────────────────────────────
// 1. Accès à la page
// ─────────────────────────────────────────────────────────────
function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Élément #${id} introuvable dans index.html`);
  return element as T;
}

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  options: { className?: string; text?: string; attrs?: Record<string, string> } = {},
  children: readonly (Node | string)[] = [],
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  for (const [name, value] of Object.entries(options.attrs ?? {})) node.setAttribute(name, value);
  node.append(...children);
  return node;
}

// ─────────────────────────────────────────────────────────────
// 2. État
// ─────────────────────────────────────────────────────────────
const today = localToday();
let lang: Lang = pickLang(storage.loadLang(), navigator.languages ?? [navigator.language]);
let t: Messages = MESSAGES[lang];
let doc: RegisterDoc | null = null;
let which: Which = "residual";
let filters: Filters = NO_FILTER;
let selected: string | null = null;

// ─────────────────────────────────────────────────────────────
// 3. Éléments d'affichage réutilisables
// ─────────────────────────────────────────────────────────────
function level(id: string): Level | undefined {
  return doc?.method.levels.find((l) => l.id === id);
}

/** Pastille colorée d'un niveau (couleur validée, contraste calculé). */
function badge(levelId: string): HTMLElement {
  const l = level(levelId);
  const span = el("span", { className: "badge", text: l?.label ?? levelId });
  if (l) {
    span.style.backgroundColor = l.color;
    span.style.color = textColor(l.color);
  }
  return span;
}

function day(iso: string, late = false): HTMLElement {
  return el("span", { className: late ? "date late" : "date", text: formatDay(iso, lang) + (late ? ` — ${t.overdue}` : "") });
}

/** Référence : lien si l'adresse a été validée, texte sinon. */
function reference(ref: Reference): HTMLElement {
  const text = ref.label ? `${ref.id} — ${ref.label}` : ref.id;
  return ref.url ? el("a", { text, attrs: { href: ref.url, rel: "noopener noreferrer", target: "_blank" } }) : el("span", { text });
}

function table(target: HTMLTableElement, headers: readonly string[], rows: readonly (readonly (Node | string)[])[]): void {
  const head = el("thead", {}, [el("tr", {}, headers.map((h) => el("th", { text: h, attrs: { scope: "col" } })))]);
  const body = el("tbody", {}, rows.map((cells) => el("tr", {}, cells.map((c) => el("td", {}, [c])))));
  target.replaceChildren(head, body);
}

// ─────────────────────────────────────────────────────────────
// 4. Rendu des sections
// ─────────────────────────────────────────────────────────────
function renderMeta(d: RegisterDoc): void {
  const meta = byId<HTMLDListElement>("meta");
  const entries: [string, string][] = [
    [t.method, d.method.name],
    [t.assessed, `${formatDay(d.register.assessedOn, lang)} — ${d.register.assessor}`],
    [t.exported, formatDay(d.asOf, lang)],
    [t.today, formatDay(today, lang)],
  ];
  meta.replaceChildren(...entries.flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })]));
  meta.hidden = false;
}

function renderSummary(d: RegisterDoc): void {
  const s = summary(d, today);
  const cards: [number, string, boolean][] = [
    [s.active, t.cardActive, false], [s.above, t.cardAbove, s.above > 0],
    [s.openMeasures, t.cardOpen, false], [s.overdueMeasures, t.cardOverdue, s.overdueMeasures > 0],
    [s.overdueReviews, t.cardReviews, s.overdueReviews > 0], [s.expiredAcceptances, t.cardExpired, s.expiredAcceptances > 0],
  ];
  byId("cards").replaceChildren(...cards.map(([n, label, alert]) =>
    el("li", { className: alert ? "card alert" : "card" }, [el("strong", { text: String(n) }), el("span", { text: label })])));
}

function renderHeat(d: RegisterDoc): void {
  const active = d.risks.filter((r) => r.status === "active");
  const rows = heatMap(d.method, active, which);
  const corner = `${d.method.likelihood.name} ↓ / ${d.method.impact.name} →`;
  const head = el("thead", {}, [el("tr", {}, [
    el("th", { text: corner, attrs: { scope: "col" } }),
    ...d.method.impact.levels.map((l) => el("th", { text: l.label, attrs: { scope: "col" } })),
  ])]);
  const body = el("tbody", {}, rows.map((row) => el("tr", {}, [
    el("th", { text: row.label, attrs: { scope: "row" } }),
    ...row.cells.map((cell) => {
      const l = level(cell.level);
      const isSelected = filters.cell?.which === which && filters.cell.likelihood === cell.likelihood && filters.cell.impact === cell.impact;
      const button = el("button", {
        className: isSelected ? "cell selected" : "cell",
        attrs: {
          type: "button", "aria-pressed": String(isSelected),
          "aria-label": fill(t.cellLabel, { level: l?.label ?? cell.level, l: cell.likelihood, i: cell.impact, n: cell.ids.length }),
        },
      }, [el("span", { className: "cell-level", text: l?.label ?? "" }), el("span", { className: "cell-ids", text: cell.ids.join(", ") })]);
      if (l) {
        button.style.backgroundColor = l.color;
        button.style.color = textColor(l.color);
      }
      button.addEventListener("click", () => {
        filters = { ...filters, cell: isSelected ? null : { which, likelihood: cell.likelihood, impact: cell.impact } };
        renderAll();
      });
      return el("td", {}, [button]);
    }),
  ])));
  byId<HTMLTableElement>("heat").replaceChildren(head, body);
  byId("show-inherent").setAttribute("aria-pressed", String(which === "inherent"));
  byId("show-residual").setAttribute("aria-pressed", String(which === "residual"));
}

function option(value: string, label: string, current: string): HTMLOptionElement {
  const o = el("option", { text: label, attrs: { value } });
  o.selected = value === current;
  return o;
}

function renderFilters(d: RegisterDoc): void {
  byId<HTMLSelectElement>("f-status").replaceChildren(
    option("active", t.statusActive, filters.status), option("closed", t.statusClosed, filters.status), option("all", t.statusAll, filters.status));
  byId<HTMLSelectElement>("f-level").replaceChildren(option("", t.all, filters.level),
    ...[...d.method.levels].reverse().map((l) => option(l.id, l.label, filters.level)));
  byId<HTMLSelectElement>("f-owner").replaceChildren(option("", t.all, filters.owner), ...owners(d).map((o) => option(o, o, filters.owner)));
  byId<HTMLSelectElement>("f-treatment").replaceChildren(option("", t.all, filters.treatment),
    ...Object.entries(t.treatments).map(([k, v]) => option(k, v, filters.treatment)));
  byId<HTMLInputElement>("f-search").value = filters.text;
  const chip = byId("cell-filter");
  chip.hidden = filters.cell === null;
  if (filters.cell) {
    chip.textContent = fill(t.cellFilter, {
      l: filters.cell.likelihood, i: filters.cell.impact, which: filters.cell.which === "inherent" ? t.inherent : t.residual,
    });
  }
}

function renderRisks(d: RegisterDoc): void {
  const list = filterRisks(d, filters);
  byId("count").textContent = list.length ? fill(t.count, { n: list.length }) : t.noRisk;
  const head = el("thead", {}, [el("tr", {}, [t.cId, t.cRisk, t.cOwner, t.inherent, t.residual, t.cSituation, t.cReview]
    .map((h) => el("th", { text: h, attrs: { scope: "col" } })))]);
  const body = el("tbody", {}, list.map((r) => {
    const open = el("button", { className: "link", text: r.title, attrs: { type: "button", "aria-expanded": String(selected === r.id) } });
    open.addEventListener("click", () => {
      selected = selected === r.id ? null : r.id;
      renderAll();
      if (selected) byId("detail").focus();
    });
    const late = r.status === "active" && r.review.next < today;
    return el("tr", { className: selected === r.id ? "selected" : "" }, [
      el("td", { text: r.id }), el("td", {}, [open]), el("td", { text: r.owner }),
      el("td", {}, [badge(r.inherent.level)]), el("td", {}, [badge(r.residual.level)]),
      el("td", { text: t.situations[situation(d.method, r, today)] }), el("td", {}, [day(r.review.next, late)]),
    ]);
  }));
  byId<HTMLTableElement>("risks").replaceChildren(head, body);
  renderDetail(d.risks.find((r) => r.id === selected) ?? null);
}

function field(label: string, content: Node | string): HTMLElement[] {
  return [el("dt", { text: label }), el("dd", {}, [content])];
}

function list(items: readonly (Node | string)[]): Node {
  return items.length ? el("ul", {}, items.map((i) => el("li", {}, [i]))) : document.createTextNode(t.none);
}

function renderDetail(r: Risk | null): void {
  const box = byId("detail");
  box.hidden = r === null;
  if (!r || !doc) {
    box.replaceChildren();
    return;
  }
  const fields: HTMLElement[] = [
    ...field(t.description, r.description || t.none),
    ...field(t.assets, list(r.assets)),
    ...field(t.threat, r.threat || t.none),
    ...field(t.vulnerability, r.vulnerability || t.none),
    ...field(t.controls, list(r.existingControls)),
    ...field(t.cTreatment, t.treatments[r.treatment] ?? r.treatment),
  ];
  if (r.transferTo) fields.push(...field(t.transferTo, r.transferTo));
  if (r.justification) fields.push(...field(t.justification, r.justification));
  fields.push(...field(t.measures, list(r.measures.map((m) => el("span", {}, [
    `${m.title} — ${m.owner} — `, day(m.due, m.status !== "done" && m.due < today), ` — ${t.measureStatuses[m.status] ?? m.status}`,
  ])))));
  if (r.acceptance) {
    const a = r.acceptance;
    fields.push(...field(t.acceptance, el("span", {}, [
      el("span", { text: fill(t.acceptedBy, { by: a.by, role: a.role, on: formatDay(a.on, lang), until: formatDay(a.until, lang) }) }),
      el("br"), el("em", { text: a.rationale }),
    ])));
  }
  const flags = [r.gdpr ? t.gdpr : "", r.nis2 ? t.nis2 : ""].filter(Boolean);
  fields.push(...field(t.flags, flags.length ? flags.join(" · ") : t.none));
  fields.push(...field(t.iso27001, list(r.iso27001.map(reference))));
  fields.push(...field(t.attack, list(r.attack.map(reference))));
  fields.push(...field(t.playbooks, list(r.playbooks.map(reference))));
  fields.push(...field(t.history, list(r.history.map((h) => `${formatDay(h.on, lang)} — ${h.by} : ${h.change}`))));
  box.replaceChildren(
    el("h3", {}, [`${r.id} — ${r.title} `, badge(r.residual.level)]),
    el("dl", { className: "fields" }, fields),
  );
}

function renderPlan(d: RegisterDoc): void {
  const items = actionPlan(d, today);
  const target = byId<HTMLTableElement>("plan");
  if (!items.length) {
    target.replaceChildren(el("caption", { text: t.noPlan }));
    return;
  }
  table(target, [t.cDue, t.cId, t.cMeasure, t.cOwner, t.cStatus], items.map(({ risk, measure, overdue }) => [
    day(measure.due, overdue), risk.id, measure.title, measure.owner, t.measureStatuses[measure.status] ?? measure.status,
  ]));
}

function renderReviews(d: RegisterDoc): void {
  table(byId<HTMLTableElement>("reviews"), [t.cReview, t.cId, t.cRisk, t.residual], reviews(d, today).map(({ risk, overdue }) => [
    day(risk.review.next, overdue), risk.id, risk.title, badge(risk.residual.level),
  ]));
}

function renderTexts(): void {
  document.documentElement.lang = lang;
  document.title = t.htmlTitle;
  const texts: [string, string][] = [
    ["skip-link", t.skip], ["intro", t.intro], ["load-title", t.loadTitle], ["example-5x5", t.example5x5],
    ["example-ebios", t.exampleEbios], ["open-file-label", t.openFile], ["privacy", t.privacy],
    ["summary-title", t.summaryTitle], ["map-title", t.mapTitle], ["show-inherent", t.inherent], ["show-residual", t.residual],
    ["map-hint", t.mapHint], ["risks-title", t.risksTitle], ["f-status-label", t.fStatus], ["f-level-label", t.fLevel],
    ["f-owner-label", t.fOwner], ["f-treatment-label", t.fTreatment], ["f-search-label", t.fSearch], ["f-reset", t.reset],
    ["plan-title", t.planTitle], ["reviews-title", t.reviewsTitle], ["remember-label", t.remember],
    ["remember-help", t.rememberHelp], ["footer-text", t.footer], ["guide-link", t.guide], ["repo-link", t.repo],
  ];
  for (const [id, text] of texts) byId(id).textContent = text;
  byId<HTMLAnchorElement>("guide-link").href = GUIDE[lang];
  byId("filters").setAttribute("aria-label", t.filtersTitle);
  for (const l of ["fr", "en"] as const) byId(`lang-${l}`).setAttribute("aria-pressed", String(l === lang));
}

function renderAll(): void {
  renderTexts();
  byId("app").hidden = doc === null;
  if (!doc) return;
  renderMeta(doc);
  renderSummary(doc);
  renderHeat(doc);
  renderFilters(doc);
  renderRisks(doc);
  renderPlan(doc);
  renderReviews(doc);
}

// ─────────────────────────────────────────────────────────────
// 5. Chargement d'un registre
// ─────────────────────────────────────────────────────────────
function show(text: string, error = false): void {
  const status = byId("status");
  status.textContent = text;
  status.className = error ? "error" : "";
}

function accept(text: string): void {
  try {
    doc = parseText(text);
    filters = NO_FILTER;
    selected = null;
    show(fill(t.loaded, { org: doc.register.organisation }));
  } catch (error) {
    doc = null;
    show(`${t.loadError} — ${error instanceof DataError ? error.message : String(error)}`, true);
  }
  renderAll();
}

async function loadExample(name: string): Promise<void> {
  show(t.loading);
  try {
    const response = await fetch(`./data/${name}.${lang}.json`, { credentials: "omit", cache: "no-cache" });
    if (!response.ok) throw new DataError(`HTTP ${response.status}`);
    accept(await response.text());
  } catch (error) {
    show(`${t.loadError} — ${error instanceof Error ? error.message : String(error)}`, true);
  }
}

// ─────────────────────────────────────────────────────────────
// 6. Événements
// ─────────────────────────────────────────────────────────────
byId("example-5x5").addEventListener("click", () => void loadExample("atelier-lumen"));
byId("example-ebios").addEventListener("click", () => void loadExample("atelier-lumen-ebios"));
byId<HTMLInputElement>("file").addEventListener("change", (event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  show(t.loading);
  void file.text().then(accept, () => show(t.loadError, true));
});

for (const l of ["fr", "en"] as const) {
  byId(`lang-${l}`).addEventListener("click", () => {
    lang = l;
    t = MESSAGES[lang];
    if (byId<HTMLInputElement>("remember").checked) storage.saveLang(lang);
    renderAll();
  });
}

byId("show-inherent").addEventListener("click", () => { which = "inherent"; renderAll(); });
byId("show-residual").addEventListener("click", () => { which = "residual"; renderAll(); });

function readFilters(): void {
  const status = byId<HTMLSelectElement>("f-status").value;
  filters = {
    ...filters,
    status: status === "closed" || status === "all" ? status : "active",
    level: byId<HTMLSelectElement>("f-level").value,
    owner: byId<HTMLSelectElement>("f-owner").value,
    treatment: byId<HTMLSelectElement>("f-treatment").value,
    text: byId<HTMLInputElement>("f-search").value,
  };
  if (doc) renderRisks(doc);
}
for (const id of ["f-status", "f-level", "f-owner", "f-treatment"]) byId(id).addEventListener("change", readFilters);
byId("f-search").addEventListener("input", readFilters);
byId("filters").addEventListener("submit", (event) => event.preventDefault());
byId("f-reset").addEventListener("click", () => { filters = NO_FILTER; renderAll(); });

const remember = byId<HTMLInputElement>("remember");
remember.checked = storage.loadLang() !== null;
remember.addEventListener("change", () => {
  if (!remember.checked) storage.forget();
  else if (!storage.saveLang(lang)) {
    remember.checked = false;
    show(t.storageBlocked, true);
  }
});

renderAll();
