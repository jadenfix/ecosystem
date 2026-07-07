#!/usr/bin/env python3
"""Audit an OpenAPI spec for the ecosystem service shape profile.

The check is intentionally small and portable so every repo can vendor or call
it without adopting a shared crate:
  - every operation has a unique lower-camel operationId
  - every operation has exactly one tag
  - every documented 4xx/5xx response uses a shared error schema
  - success object responses reference named schemas instead of inline objects
  - list operations expose pagination parameters
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sys
from pathlib import Path
from typing import Any


CAMEL = re.compile(r"^[a-z][a-zA-Z0-9]*$")
DEFAULT_ERROR_SCHEMA_SUFFIXES = ("/ErrorResponse", "/ApiErrorBody")


@dataclass(frozen=True)
class AuditResult:
    operation_count: int
    unique_operation_id_count: int
    schema_count: int
    violations: list[str]


def load_spec(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def operations(spec: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    ops: list[tuple[str, str, dict[str, Any]]] = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if method == "parameters":
                continue
            ops.append((method.upper(), path, op))
    return ops


def schema_ref(response: dict[str, Any]) -> str:
    return (
        response.get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
    )


def audit_spec(
    spec: dict[str, Any],
    *,
    error_schema_suffixes: tuple[str, ...] = DEFAULT_ERROR_SCHEMA_SUFFIXES,
    list_pagination_exemptions: set[str] | None = None,
) -> AuditResult:
    violations: list[str] = []
    op_ids: dict[str, list[str]] = {}
    ops = operations(spec)
    list_pagination_exemptions = list_pagination_exemptions or set()

    for method, path, op in ops:
        where = f"{method} {path}"
        oid = op.get("operationId")
        tags = op.get("tags", [])

        if not oid:
            violations.append(f"{where}: missing operationId")
        else:
            if not CAMEL.match(oid):
                violations.append(f"{where}: operationId {oid!r} is not lower-camel")
            op_ids.setdefault(oid, []).append(where)

        if len(tags) != 1:
            violations.append(f"{where}: expected exactly 1 tag, got {tags}")

        responses = op.get("responses", {})
        is_health = oid in {"health", "getHealth"} or path.rstrip("/").endswith("/health")
        if not is_health:
            err_codes = [code for code in responses if code.startswith(("4", "5"))]
            if not err_codes:
                violations.append(f"{where}: no documented 4xx/5xx error response")
            for code in err_codes:
                ref = schema_ref(responses[code])
                if not ref.endswith(error_schema_suffixes):
                    violations.append(
                        f"{where}: error {code} body is not shared error schema "
                        f"(got {ref or 'none'})"
                    )

        for code, body in responses.items():
            if not code.startswith("2"):
                continue
            schema = body.get("content", {}).get("application/json", {}).get("schema", {})
            if (
                "$ref" not in schema
                and schema.get("type") == "object"
                and "properties" in schema
            ):
                violations.append(
                    f"{where}: success {code} uses inline anonymous object"
                )

    for oid, wheres in op_ids.items():
        if len(wheres) > 1:
            violations.append(f"operationId {oid!r} is duplicated: {wheres}")

    for method, path, op in ops:
        oid = op.get("operationId", "")
        if oid.startswith("list") and oid not in list_pagination_exemptions:
            params = {p.get("name") for p in op.get("parameters", [])}
            if "cursor" not in params and "limit" not in params:
                violations.append(f"{method} {path}: list op {oid!r} lacks pagination")

    return AuditResult(
        operation_count=len(ops),
        unique_operation_id_count=len(op_ids),
        schema_count=len(spec.get("components", {}).get("schemas", {})),
        violations=violations,
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args:
        print("usage: audit-openapi-shape.py <openapi.json>", file=sys.stderr)
        return 2

    result = audit_spec(load_spec(args[0]))
    print(
        f"audited {result.operation_count} operations, "
        f"{result.unique_operation_id_count} unique operationIds, "
        f"{result.schema_count} schemas"
    )
    if result.violations:
        print(f"\n{len(result.violations)} SHAPE VIOLATIONS:")
        for violation in result.violations:
            print(f"  - {violation}")
        return 1
    print("PASS: OpenAPI shape matches ecosystem profile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
