"""Tiny TOML loader wrapper for ecosystem scripts.

Use stdlib `tomllib` when available. Fall back to a narrow parser that supports
the TOML shape used by `ecosystem.toml`: tables, strings, booleans, and arrays
of strings.
"""

from __future__ import annotations

from pathlib import Path


try:  # Python 3.11+
    import tomllib as _tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on older Python
    _tomllib = None


def load(path: Path) -> dict:
    if _tomllib is not None:
        with path.open("rb") as f:
            return _tomllib.load(f)
    return _load_simple(path.read_text())


def _strip_comment(line: str) -> str:
    in_string = False
    escaped = False
    out = []
    for ch in line:
        if escaped:
            out.append(ch)
            escaped = False
            continue
        if ch == "\\" and in_string:
            out.append(ch)
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if ch == "#" and not in_string:
            break
        out.append(ch)
    return "".join(out).strip()


def _parse_value(value: str):
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        items = []
        current = []
        in_string = False
        escaped = False
        for ch in inner:
            if escaped:
                current.append(ch)
                escaped = False
                continue
            if ch == "\\" and in_string:
                current.append(ch)
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
                current.append(ch)
                continue
            if ch == "," and not in_string:
                items.append(_parse_value("".join(current).strip()))
                current = []
                continue
            current.append(ch)
        if current:
            items.append(_parse_value("".join(current).strip()))
        return items
    raise ValueError(f"unsupported TOML value: {value}")


def _load_simple(text: str) -> dict:
    root: dict = {}
    current = root
    pending_key = None
    pending_value = []

    for raw_line in text.splitlines():
        line = _strip_comment(raw_line)
        if not line:
            continue

        if pending_key is not None:
            pending_value.append(line)
            if line.endswith("]"):
                current[pending_key] = _parse_value(" ".join(pending_value))
                pending_key = None
                pending_value = []
            continue

        if line.startswith("[") and line.endswith("]"):
            current = root
            for part in line.strip("[]").split("."):
                current = current.setdefault(part, {})
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and not value.endswith("]"):
            pending_key = key
            pending_value = [value]
            continue
        current[key] = _parse_value(value)

    if pending_key is not None:
        raise ValueError(f"unterminated array for {pending_key}")

    return root
