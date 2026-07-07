#!/usr/bin/env python3
"""Audit a client-surface manifest for SDK, CLI, auth, and error consistency."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import sys
from pathlib import Path
from typing import Any


SURFACE_VERSION = "2026-07-07"
CONTRACT_TYPES = {
    "openapi",
    "json_rpc_manifest",
    "mcp_catalog",
    "json_schema",
    "http_route_manifest",
}
AUTH_PRECEDENCE = ["flag", "token_file", "env"]
SDK_CONFIG_FIELDS = {"base_url", "token", "timeout_ms"}
CLI_FLAGS = {"--base-url", "--token", "--token-file", "--timeout-ms", "--output"}
ERROR_FIELDS = ["status", "code", "message"]
OPTIONAL_ERROR_FIELDS = {"request_id", "details"}
LOWER_CAMEL = re.compile(r"^[a-z][a-zA-Z0-9]*$")
ENV_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]*_TOKEN$")
ENV_API_KEY = re.compile(r"^[A-Z][A-Z0-9_]*_API_KEY$")


@dataclass(frozen=True)
class AuditResult:
    service: str
    violations: list[str]


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def require_object(parent: dict[str, Any], key: str, violations: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        violations.append(f"{key}: expected object")
        return {}
    return value


def require_list(parent: dict[str, Any], key: str, violations: list[str]) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        violations.append(f"{key}: expected array")
        return []
    return value


def audit_manifest(manifest: dict[str, Any]) -> AuditResult:
    violations: list[str] = []
    service = manifest.get("service", "<unknown>")

    if manifest.get("surface_version") != SURFACE_VERSION:
        violations.append(
            f"surface_version: expected {SURFACE_VERSION!r}, got "
            f"{manifest.get('surface_version')!r}"
        )
    if not isinstance(service, str) or not service.strip():
        violations.append("service: expected non-empty string")

    contract = require_object(manifest, "contract", violations)
    contract_type = contract.get("type")
    if contract_type not in CONTRACT_TYPES:
        violations.append(f"contract.type: expected one of {sorted(CONTRACT_TYPES)}")
    for key in ("path", "drift_check"):
        if not isinstance(contract.get(key), str) or not contract.get(key).strip():
            violations.append(f"contract.{key}: expected non-empty string")

    auth = require_object(manifest, "auth", violations)
    auth_scheme = auth.get("scheme")
    if auth_scheme not in {"bearer", "none"}:
        violations.append("auth.scheme: expected 'bearer' or 'none'")
    if auth.get("token_field") != "token":
        violations.append("auth.token_field: canonical client field must be 'token'")
    if auth_scheme == "bearer":
        if auth.get("header") != "Authorization":
            violations.append("auth.header: bearer auth must use Authorization")
        if auth.get("value_format") != "Bearer <token>":
            violations.append("auth.value_format: expected 'Bearer <token>'")
        env_token = auth.get("env_token")
        if not isinstance(env_token, str) or not ENV_TOKEN.match(env_token):
            violations.append("auth.env_token: expected <SERVICE>_TOKEN")

    precedence = require_list(auth, "precedence", violations)
    if precedence and precedence != AUTH_PRECEDENCE:
        violations.append("auth.precedence: expected ['flag', 'token_file', 'env']")

    for header in auth.get("compat_headers", []):
        if not isinstance(header, str) or not header.lower().endswith("-api-key"):
            violations.append(
                "auth.compat_headers: compatibility headers must be API-key aliases"
            )
    for env_name in auth.get("compat_env", []):
        if not isinstance(env_name, str) or not ENV_API_KEY.match(env_name):
            violations.append("auth.compat_env: expected <SERVICE>_API_KEY aliases")

    sdk = require_object(manifest, "sdk", violations)
    config_fields = set(require_list(sdk, "config_fields", violations))
    missing_sdk_fields = sorted(SDK_CONFIG_FIELDS - config_fields)
    if missing_sdk_fields:
        violations.append(f"sdk.config_fields: missing {missing_sdk_fields}")
    if "api_key" in config_fields or "apiKey" in config_fields:
        violations.append("sdk.config_fields: api_key/apiKey may not be canonical")
    if sdk.get("operation_names") != "contract":
        violations.append("sdk.operation_names: expected 'contract'")
    if not isinstance(sdk.get("error_type"), str) or not sdk.get("error_type", "").strip():
        violations.append("sdk.error_type: expected non-empty string")

    cli = require_object(manifest, "cli", violations)
    flags = set(require_list(cli, "global_flags", violations))
    missing_flags = sorted(CLI_FLAGS - flags)
    if missing_flags:
        violations.append(f"cli.global_flags: missing {missing_flags}")
    if "--api-key" in flags or "--api-key-file" in flags:
        violations.append("cli.global_flags: api-key flags may only be aliases")
    env = set(require_list(cli, "env", violations))
    if auth_scheme == "bearer" and auth.get("env_token") not in env:
        violations.append("cli.env: missing canonical token env var")
    output_modes = set(require_list(cli, "output_modes", violations))
    if "json" not in output_modes:
        violations.append("cli.output_modes: missing stable json output")
    if cli.get("operation_names") not in {"contract", "documented_aliases"}:
        violations.append(
            "cli.operation_names: expected 'contract' or 'documented_aliases'"
        )

    errors = require_object(manifest, "errors", violations)
    error_fields = require_list(errors, "fields", violations)
    if error_fields[: len(ERROR_FIELDS)] != ERROR_FIELDS:
        violations.append(
            "errors.fields: must start with ['status', 'code', 'message']"
        )
    for field in error_fields[len(ERROR_FIELDS) :]:
        if field not in OPTIONAL_ERROR_FIELDS:
            violations.append(f"errors.fields: unknown optional field {field!r}")

    operations = manifest.get("operations")
    if operations is not None:
        if not isinstance(operations, list):
            violations.append("operations: expected array when present")
        else:
            for operation in operations:
                if not isinstance(operation, str) or not LOWER_CAMEL.match(operation):
                    violations.append(
                        f"operations: {operation!r} is not a lower-camel operation name"
                    )

    return AuditResult(service=str(service), violations=violations)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: audit-client-surface.py <client-surface.json>", file=sys.stderr)
        return 2

    result = audit_manifest(load_manifest(args[0]))
    print(f"audited client surface for {result.service}")
    if result.violations:
        print(f"\n{len(result.violations)} CLIENT SURFACE VIOLATIONS:")
        for violation in result.violations:
            print(f"  - {violation}")
        return 1
    print("PASS: client surface matches ecosystem profile")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
