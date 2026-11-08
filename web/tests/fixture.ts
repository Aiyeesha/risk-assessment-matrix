/** Exports réels du dépôt (examples/), relus à chaque appel : chaque test peut modifier sa copie. */

import { readFileSync } from "node:fs";

export type Json = Record<string, any>;

export function example(name = "atelier-lumen", lang = "fr"): Json {
  const url = new URL(`../../examples/${lang}/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(url, "utf8")) as Json;
}
