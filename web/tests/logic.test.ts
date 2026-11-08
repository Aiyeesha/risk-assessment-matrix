/**
 * Calculs de l'interface sur l'export réel d'Atelier Lumen (5×5), date de référence fixée.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { parseExport } from "../src/data.ts";
import {
  actionPlan, contrast, filterRisks, formatDay, heatMap, localToday, NO_FILTER, normalize, owners, reviews, situation,
  sortRisks, summary, textColor,
} from "../src/logic.ts";
import { fill, MESSAGES, pickLang } from "../src/i18n.ts";
import { example } from "./fixture.ts";

const doc = parseExport(example());
const TODAY = "2026-11-08";

test("synthèse : comme le rapport Python à la même date", () => {
  const s = summary(doc, TODAY);
  assert.deepEqual(
    [s.active, s.closed, s.above, s.openMeasures, s.overdueMeasures, s.overdueReviews, s.expiredAcceptances],
    [7, 1, 5, 4, 1, 0, 0],
  );
  assert.deepEqual(s.byLevel.map((l) => l.count), [0, 1, 4, 2]); // critique → faible
});

test("cartographie : lignes de la vraisemblance la plus forte à la plus faible", () => {
  const active = doc.risks.filter((r) => r.status === "active");
  const inherent = heatMap(doc.method, active, "inherent");
  assert.equal(inherent[0]?.likelihood, 5);
  assert.deepEqual(inherent[1]?.cells[4], { likelihood: 4, impact: 5, level: "critical", ids: ["R01"] });
  const residual = heatMap(doc.method, active, "residual");
  assert.deepEqual(residual[3]?.cells[3]?.ids, ["R02", "R03"]);
});

test("tri : du plus grave au moins grave", () => {
  assert.deepEqual(sortRisks(doc.method, doc.risks).slice(0, 3).map((r) => r.id), ["R01", "R02", "R03"]);
});

test("filtres : état, niveau, responsable, traitement, case, texte sans accents", () => {
  assert.equal(filterRisks(doc, NO_FILTER).length, 7);
  assert.equal(filterRisks(doc, { ...NO_FILTER, status: "all" }).length, 8);
  assert.deepEqual(filterRisks(doc, { ...NO_FILTER, status: "closed" }).map((r) => r.id), ["R08"]);
  assert.deepEqual(filterRisks(doc, { ...NO_FILTER, level: "high" }).map((r) => r.id), ["R01"]);
  assert.deepEqual(filterRisks(doc, { ...NO_FILTER, treatment: "transfer" }).map((r) => r.id), ["R05"]);
  assert.deepEqual(filterRisks(doc, { ...NO_FILTER, cell: { which: "residual", likelihood: 2, impact: 4 } }).map((r) => r.id), ["R02", "R03"]);
  assert.deepEqual(filterRisks(doc, { ...NO_FILTER, text: "RANCONGICIEL" }).map((r) => r.id), ["R01"]);
  assert.ok(owners(doc).includes("Julien Morel, DSI"));
  assert.equal(normalize("Sécurité Élevée"), "securite elevee");
});

test("situation de chaque risque au-dessus de l'appétence", () => {
  const byId = (id: string) => doc.risks.find((r) => r.id === id)!;
  assert.equal(situation(doc.method, byId("R01"), TODAY), "reducing");
  assert.equal(situation(doc.method, byId("R02"), TODAY), "accepted");
  assert.equal(situation(doc.method, byId("R02"), "2027-10-02"), "expired");
  assert.equal(situation(doc.method, byId("R06"), TODAY), "below");
});

test("plan d'action et revues : tri par date, retards repérés", () => {
  const plan = actionPlan(doc, TODAY);
  assert.deepEqual(plan.map((p) => [p.measure.due, p.overdue]), [
    ["2026-10-31", true], ["2026-12-15", false], ["2027-01-31", false], ["2027-03-31", false],
  ]);
  const next = reviews(doc, "2027-01-20");
  assert.equal(next[0]?.risk.id, "R01");
  assert.equal(next[0]?.overdue, true);
});

test("couleurs : texte blanc lisible (WCAG AA) sur chaque niveau des deux méthodes", () => {
  for (const name of ["atelier-lumen", "atelier-lumen-ebios"]) {
    for (const level of parseExport(example(name)).method.levels) {
      const fg = textColor(level.color);
      assert.equal(fg, "#ffffff", level.id);
      assert.ok(contrast(level.color, fg) >= 4.5, `${level.id} ${contrast(level.color, fg).toFixed(2)}`);
    }
  }
});

test("dates : affichage français et date du jour locale", () => {
  assert.equal(formatDay("2027-09-15", "fr"), "15/09/2027");
  assert.equal(formatDay("2027-09-15", "en"), "2027-09-15");
  assert.equal(localToday(new Date(2026, 0, 5)), "2026-01-05");
});

test("textes : mêmes clés en français et en anglais, langue choisie", () => {
  assert.deepEqual(Object.keys(MESSAGES.fr).sort(), Object.keys(MESSAGES.en).sort());
  assert.equal(fill("{n} risque(s)", { n: 3 }), "3 risque(s)");
  assert.equal(pickLang(null, ["en-GB", "fr"]), "en");
  assert.equal(pickLang("fr", ["en-US"]), "fr");
  assert.equal(pickLang(null, ["de-DE"]), "fr");
});
