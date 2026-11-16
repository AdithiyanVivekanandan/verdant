#!/usr/bin/env python3
"""Add a key to a nested section of the locale files, safely.

The script finds the *top level* of a named section and inserts the key as
its direct child, so a key with the same name inside a nested block (for
example ``schedule.priority.uncertain``) is never confused with the
section-level key.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def section_bounds(text: str, name: str) -> tuple[int, int]:
    """Return the (open brace index, close brace index) of a section.

    The name may be a dotted path: ``readings.history`` addresses the
    nested ``history`` object inside the ``readings`` section. The
    indentation of each part is derived from the path, so a nested section
    is found at its own level.
    """
    parts = name.split(".")
    current_start, current_end = 0, len(text)
    for depth, part in enumerate(parts):
        indent = "  " * depth
        found = None
        for marker in (
            f"\n{indent}{part}: {{",
            f'\n{indent}"{part}": {{',
            f"\n{indent}  {part}: {{",
            f'\n{indent}  "{part}": {{',
        ):
            index = text.find(marker, current_start, current_end)
            if index != -1:
                found = index
                break
        if found is None:
            raise ValueError(f"section {part!r} not found in {name!r}")
        brace = text.index("{", found)
        close = -1
        level = 0
        for position in range(brace, current_end):
            if text[position] == "{":
                level += 1
            elif text[position] == "}":
                level -= 1
                if level == 0:
                    close = position
                    break
        if close == -1:
            raise ValueError(f"section {part!r} is not closed in {name!r}")
        current_start, current_end = brace, close
    return current_start, current_end


def top_level_keys(body: str) -> set[str]:
    """Collect the keys declared directly inside an object body."""
    keys: set[str] = set()
    depth = 0
    for line in body.splitlines():
        stripped = line.strip()
        if depth == 0:
            match = re.match(r'^"?([A-Za-z0-9_]+)"?\s*:', stripped)
            if match:
                keys.add(match.group(1))
        depth += line.count("{") - line.count("}")
    return keys


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: add_section_key.py <section> <key> <locale=value> [...]")
        return 2

    section, key = sys.argv[1], sys.argv[2]
    values: dict[str, str] = {}
    for item in sys.argv[3:]:
        locale, _, value = item.partition("=")
        values[locale] = value

    translations = Path(__file__).resolve().parents[1] / "lib" / "translations"
    for locale, value in values.items():
        path = translations / f"{locale}.ts"
        text = path.read_text(encoding="utf-8")
        start, end = section_bounds(text, section)
        body = text[start + 1 : end]
        if key in top_level_keys(body):
            print(f"{locale}: {section}.{key} already present")
            continue
        quote = '"' if f'"{key}"' in body or f'"{section}"' in text else ""
        insertion = f'\n    {quote}{key}{quote}: "{value}",'
        text = text[: start + 1] + insertion + text[start + 1 :]
        path.write_text(text, encoding="utf-8")
        print(f"{locale}: inserted {section}.{key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
