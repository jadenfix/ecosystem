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
SDK_CONFIG_FIELDS = ["base_url", "token", "timeout_ms"]
CLI_FLAGS = [
    "--base-url",
    "--token",
    "--token-file",
    "--timeout-ms",
    "--output",
    "--json",
]
ERROR_FIELDS = ["status", "code", "message"]
OPTIONAL_ERROR_FIELDS = {"request_id", "details"}
LOWER_CAMEL = re.compile(r"^[a-z][a-zA-Z0-9]*$")
PROJECTS_OPERATION_ID = re.compile(r"^projects(?:\.[a-z][a-zA-Z0-9]*){2,}$")
SNAKE = re.compile(r"^[a-z][a-z0-9_]*$")
ENV_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]*_TOKEN$")
ENV_API_KEY = re.compile(r"^[A-Z][A-Z0-9_]*_API_KEY$")


@dataclass(frozen=True)
class AuditResult:
    service: str
    violations: list[str]


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def service_env_prefix(service: str) -> str:
    prefix = re.sub(r"[^A-Za-z0-9]+", "_", service).strip("_").upper()
    return prefix or "SERVICE"


def template_manifest(service: str) -> dict[str, Any]:
    prefix = service_env_prefix(service)
    return {
        "surface_version": SURFACE_VERSION,
        "service": service,
        "contract": {
            "type": "openapi",
            "path": "sdks/openapi.json",
            "drift_check": "replace with the repo-local contract drift check",
        },
        "auth": {
            "scheme": "bearer",
            "header": "Authorization",
            "value_format": "Bearer <token>",
            "token_field": "token",
            "env_token": f"{prefix}_TOKEN",
            "compat_headers": [],
            "compat_env": [],
            "precedence": AUTH_PRECEDENCE,
        },
        "sdk": {
            "config_fields": SDK_CONFIG_FIELDS,
            "error_type": "ApiError",
            "operation_names": "contract",
        },
        "cli": {
            "global_flags": CLI_FLAGS,
            "env": [f"{prefix}_BASE_URL", f"{prefix}_TOKEN", f"{prefix}_TIMEOUT_MS"],
            "output_modes": ["json", "text"],
            "operation_names": "contract",
        },
        "errors": {
            "fields": ["status", "code", "message", "request_id", "details"],
        },
    }


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
    env_prefix = service_env_prefix(str(service))

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
        elif env_token != f"{env_prefix}_TOKEN":
            violations.append(
                f"auth.env_token: expected service-prefixed {env_prefix}_TOKEN"
            )

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
    config_fields = require_list(sdk, "config_fields", violations)
    if config_fields[: len(SDK_CONFIG_FIELDS)] != SDK_CONFIG_FIELDS:
        violations.append(
            f"sdk.config_fields: must start with {SDK_CONFIG_FIELDS}"
        )
    if "api_key" in config_fields or "apiKey" in config_fields:
        violations.append("sdk.config_fields: api_key/apiKey may not be canonical")
    for field in config_fields:
        if not isinstance(field, str) or not SNAKE.match(field):
            violations.append(
                f"sdk.config_fields: {field!r} must be a snake_case client field"
            )
    if sdk.get("operation_names") != "contract":
        violations.append("sdk.operation_names: expected 'contract'")
    if not isinstance(sdk.get("error_type"), str) or not sdk.get("error_type", "").strip():
        violations.append("sdk.error_type: expected non-empty string")

    cli = require_object(manifest, "cli", violations)
    flags = require_list(cli, "global_flags", violations)
    if flags[: len(CLI_FLAGS)] != CLI_FLAGS:
        violations.append(f"cli.global_flags: must start with {CLI_FLAGS}")
    if "--api-key" in flags or "--api-key-file" in flags:
        violations.append("cli.global_flags: api-key flags may only be aliases")
    env = set(require_list(cli, "env", violations))
    if auth_scheme == "bearer" and auth.get("env_token") not in env:
        violations.append("cli.env: missing canonical token env var")
    expected_env = {
        f"{env_prefix}_BASE_URL",
        f"{env_prefix}_TOKEN",
        f"{env_prefix}_TIMEOUT_MS",
    }
    missing_env = sorted(expected_env - env)
    if missing_env:
        violations.append(f"cli.env: missing service-prefixed env vars {missing_env}")
    output_modes = set(require_list(cli, "output_modes", violations))
    if output_modes != {"json", "text"}:
        violations.append("cli.output_modes: expected exactly ['json', 'text']")
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
                if not isinstance(operation, str) or not (
                    LOWER_CAMEL.match(operation)
                    or PROJECTS_OPERATION_ID.match(operation)
                ):
                    violations.append(
                        f"operations: {operation!r} is not a contract operation name"
                    )

    mcp = manifest.get("mcp")
    if mcp is not None:
        if not isinstance(mcp, dict):
            violations.append("mcp: expected object when present")
        else:
            for key in ("path", "drift_check"):
                if not isinstance(mcp.get(key), str) or not mcp.get(key).strip():
                    violations.append(f"mcp.{key}: expected non-empty string")
            if mcp.get("tool_names") not in {
                "contract",
                "catalog",
                "documented_composites",
            }:
                violations.append(
                    "mcp.tool_names: expected 'contract', 'catalog', or "
                    "'documented_composites'"
                )
            if mcp.get("auth") != "shared":
                violations.append("mcp.auth: expected 'shared'")
            if mcp.get("errors") not in {"structured_content", "transport_native"}:
                violations.append(
                    "mcp.errors: expected 'structured_content' or 'transport_native'"
                )

    return AuditResult(service=str(service), violations=violations)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 2 and args[0] == "--print-template":
        print(json.dumps(template_manifest(args[1]), indent=2))
        return 0
    if len(args) != 1:
        print(
            "usage: audit-client-surface.py <client-surface.json>\n"
            "       audit-client-surface.py --print-template <service>",
            file=sys.stderr,
        )
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
