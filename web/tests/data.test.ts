/**
 * Validation de l'export JSON : les exports réels sont acceptés, les fichiers altérés refusés.
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { DataError, MAX_BYTES, parseExport, parseText, safeUrl } from "../src/data.ts";
import { example } from "./fixture.ts";

for (const lang of ["fr", "en"]) {
  for (const name of ["atelier-lumen", "atelier-lumen-ebios"]) {
    test(`export réel accepté : ${name} (${lang})`, () => {
      const doc = parseExport(example(name, lang));
      assert.equal(doc.register.lang, lang);
      assert.ok(doc.risks.length >= 4);
      assert.equal(doc.method.grid.length, doc.method.likelihood.levels.length);
    });
  }
}

test("les champs sont typés et renommés", () => {
  const doc = parseExport(example());
  const r01 = doc.risks[0]!;
  assert.equal(r01.id, "R01");
  assert.deepEqual(r01.inherent, { likelihood: 4, impact: 5, level: "critical" });
  assert.equal(r01.measures[2]?.status, "in-progress");
  assert.equal(r01.attack[0]?.url, "https://attack.mitre.org/techniques/T1133/");
  assert.match(r01.playbooks[0]?.url ?? "", /^https:\/\/github\.com\/Aiyeesha\/incident-response-playbook\//);
  assert.equal(doc.risks[1]?.acceptance?.until, "2027-10-01");
});

test("un autre format est refusé avec un message clair", () => {
  const data = { ...example(), schema_version: 2 };
  assert.throws(() => parseExport(data), /format 2 non pris en charge \(attendu : 1\)/);
});

test("un niveau incohérent avec la grille est détecté", () => {
  const data = example();
  data.risks[0].residual.level = "low"; // 3 × 4 = « high » d'après la grille
  assert.throws(() => parseExport(data), /R01\.residual\.level : « high » attendu d'après la grille/);
});

test("une couleur qui n'est pas #RRVVBB est refusée (elle serait injectée dans le style)", () => {
  const data = example();
  data.method.levels[0].color = "red; background-image: url(https://exemple.invalid)";
  assert.throws(() => parseExport(data), /method\.levels\[0\]\.color : couleur #RRVVBB attendue/);
});

test("une date impossible est refusée", () => {
  const data = example();
  data.risks[0].review.next = "2027-02-30";
  assert.throws(() => parseExport(data), /R01\.review\.next : date AAAA-MM-JJ attendue/);
});

test("une note hors échelle est refusée", () => {
  const data = example();
  data.risks[0].inherent.impact = 9;
  assert.throws(() => parseExport(data), /R01\.inherent : note hors des échelles/);
});

test("des identifiants en double sont refusés", () => {
  const data = example();
  data.risks[1].id = "R01";
  assert.throws(() => parseExport(data), /risks : identifiants en double/);
});

test("une grille mal dimensionnée est refusée", () => {
  const data = example();
  data.method.grid.pop();
  assert.throws(() => parseExport(data), /method\.grid : 5 × 5 cases attendues/);
});

test("un lien hors des sites autorisés devient du texte", () => {
  const data = example();
  data.risks[0].attack[0].url = "javascript:alert(1)";
  data.risks[0].playbooks[0].url = "https://exemple.invalid/piege";
  const r01 = parseExport(data).risks[0]!;
  assert.equal(r01.attack[0]?.url, null);
  assert.equal(r01.playbooks[0]?.url, null);
  assert.equal(safeUrl("https://attack.mitre.org/techniques/T1486/"), "https://attack.mitre.org/techniques/T1486/");
  assert.equal(safeUrl("https://attack.mitre.org.exemple.invalid/"), null);
});

test("le texte d'un registre reste du texte (aucune interprétation à la lecture)", () => {
  const data = example();
  data.risks[0].title = "<img src=x onerror=alert(1)>";
  assert.equal(parseExport(data).risks[0]?.title, "<img src=x onerror=alert(1)>");
});

test("fichier non JSON, trop gros ou vide : erreurs lisibles", () => {
  assert.throws(() => parseText("pas du json"), DataError);
  assert.throws(() => parseText("pas du json"), /n'est pas du JSON valide/);
  assert.throws(() => parseText(" ".repeat(MAX_BYTES + 1)), /trop volumineux/);
  assert.throws(() => parseText("[]"), /export : objet attendu/);
});
