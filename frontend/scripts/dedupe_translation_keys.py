#!/usr/bin/env python3
"""Remove duplicate keys inside a single object literal.

The translation files are edited by scripts, and a re-run can insert the same
key twice. This pass removes the later duplicates while keeping the first
occurrence, so the file stays valid and the values stay unchanged.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KEY_LINE = re.compile(r'^(?P<indent>\s*)(?P<key>"?[A-Za-z0-9_]+"?)\s*:\s*(?P<value>.*)$')


def dedupe_file(path: Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    # Track the brace depth of every line and the object each line belongs to.
    stack: list[dict] = []
    seen: dict[int, set[str]] = {}
    removed = 0
    output: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            output.append(line)
            continue

        opens = line.count("{")
        closes = line.count("}")

        if opens and not stripped.startswith("}"):
            # This line opens a new object.
            stack.append({"seen": set(), "depth": len(stack)})
            seen[len(stack)] = stack[-1]["seen"]

        key_match = KEY_LINE.match(line)
        duplicate = False
        if key_match and stack:
            key = key_match.group("key").strip('"')
            current = stack[-1]["seen"]
            if key in current:
                duplicate = True
            else:
                current.add(key)

        if not duplicate:
            output.append(line)
        else:
            removed += 1

        for _ in range(closes):
            if stack:
                stack.pop()

    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return removed


def main() -> int:
    translations = Path(__file__).resolve().parents[1] / "lib" / "translations"
    total = 0
    for locale in ("en", "hi", "kn", "ta"):
        path = translations / f"{locale}.ts"
        removed = dedupe_file(path)
        total += removed
        print(f"{path.name}: removed {removed} duplicate key(s)")
    print(f"total removed: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
