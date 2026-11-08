/**
 * Mémorisation FACULTATIVE de la langue (localStorage), désactivée par défaut.
 *
 * Le registre lui-même n'est JAMAIS conservé : il décrit les faiblesses d'une organisation.
 * Chaque accès est protégé : un navigateur qui bloque le stockage ne casse pas la page.
 */

import type { Lang } from "./data.ts";

const KEY = "risk-assessment-matrix:lang";

function store(): Storage | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

/** Langue mémorisée, ou null (rien de mémorisé, valeur inattendue ou stockage bloqué). */
export function loadLang(): Lang | null {
  try {
    const value = store()?.getItem(KEY) ?? null;
    return value === "fr" || value === "en" ? value : null;
  } catch {
    return null;
  }
}

/** Mémorise la langue ; renvoie false si le stockage est indisponible. */
export function saveLang(lang: Lang): boolean {
  try {
    const s = store();
    if (!s) return false;
    s.setItem(KEY, lang);
    return true;
  } catch {
    return false;
  }
}

export function forget(): void {
  try {
    store()?.removeItem(KEY);
  } catch {
    // stockage bloqué : rien à effacer
  }
}
