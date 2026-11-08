"""
Écriture d'un registre au format TOML (la bibliothèque standard sait lire le TOML, pas l'écrire).

Volontairement limité aux types d'un registre : texte, entier, booléen, date, liste et table.
Mise en page : en-tête, puis un bloc [[risks]] par risque, suivi de ses [[risks.measures]] et
[[risks.history]] — la même forme que les registres écrits à la main.
"""

from __future__ import annotations

from datetime import date

# Échappements des chaînes TOML « basiques » (entre guillemets doubles)
_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}
_BLOCKS = ("measures", "history")  # listes de tables écrites en blocs [[risks.…]]


def _string(value: str) -> str:
    out = []
    for char in value:
        if char in _ESCAPES:
            out.append(_ESCAPES[char])
        elif ord(char) < 0x20 or ord(char) == 0x7F:  # autres caractères de contrôle : interdits tels quels
            out.append(f"\\u{ord(char):04x}")
        else:
            out.append(char)
    return '"' + "".join(out) + '"'


def value(item: object) -> str:
    """Valeur TOML d'un objet Python (types d'un registre seulement)."""
    if isinstance(item, bool):  # avant int : bool est un sous-type d'int
        return "true" if item else "false"
    if isinstance(item, int):
        return str(item)
    if isinstance(item, date):
        return item.isoformat()
    if isinstance(item, str):
        return _string(item)
    if isinstance(item, list | tuple):
        return "[" + ", ".join(value(v) for v in item) + "]"
    if isinstance(item, dict):  # table en ligne : { clé = valeur, … }
        return "{ " + ", ".join(f"{k} = {value(v)}" for k, v in item.items()) + " }"
    raise TypeError(f"type non pris en charge : {type(item).__name__}")


def _pairs(table: dict, skip: tuple[str, ...] = ()) -> list[str]:
    return [f"{key} = {value(item)}" for key, item in table.items() if key not in skip]


def dump_register(data: dict, comment: str = "") -> str:
    """Texte TOML d'un registre (dictionnaire de la même forme que celui lu par tomllib)."""
    lines = [f"# {line}" if line else "#" for line in comment.splitlines()]
    lines += _pairs(data, skip=("risks",))
    for risk in data.get("risks", []):
        lines += ["", "[[risks]]", *_pairs(risk, skip=_BLOCKS)]
        for block in _BLOCKS:
            for entry in risk.get(block, []):
                lines += ["", f"[[risks.{block}]]", *_pairs(entry)]
    return "\n".join(lines) + "\n"
