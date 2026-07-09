#!/usr/bin/env python3
"""Check cross-repo API style and endpoint/tool conflicts.

The shared style target is data-engine's AIP-like API profile:
project-scoped /v1 resources, dotted projects.* operationIds, shared HTTP error
envelopes, cursor pagination, Operation for async work, Idempotency-Key for
mutations, and If-Match/update_mask for patches.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ecosystem.toml"
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}
PROJECTS_OPERATION_ID = re.compile(r"^projects(?:\.[a-z][a-zA-Z0-9]*){2,}$")
PUBLIC_OPERATION_IDS = {"health", "getHealth", "openapi", "getOpenapi", "postMcp"}
TRANSPORT_NATIVE_PATHS = {"/mcp", "/openapi.json", "/health", "/healthz", "/readyz"}
ERROR_ENVELOPE_SCHEMAS = {"Error", "ErrorResponse", "ApiError", "ApiErrorBody"}
ERROR_BODY_SCHEMAS = {"ErrorBody", "ApiErrorBody"}
ASYNC_VERBS = {
    "ingest",
    "run",
    "sync",
    "emit",
    "emitRlvr",
    "emitEval",
    "emitPreference",
    "emitSft",
}
MUTATING_METHODS = {"post", "put", "patch", "delete"}


@dataclass(frozen=True)
class Contract:
    service: str
    repo_key: str | None = None
    repo_path: str | None = None
    openapi: str | None = None
    mcp_catalog: str | None = None
    style: str = "aip-target"
    required: bool = False
    gateway_mount: str = ""
    mcp_namespace: str = ""
    mcp_tools_from_openapi: bool = False


@dataclass(frozen=True)
class Operation:
    service: str
    method: str
    path: str
    operation_id: str
    op: dict[str, Any]
    path_item: dict[str, Any]
    spec: dict[str, Any]

    @property
    def where(self) -> str:
        return f"{self.service}: {self.method.upper()} {self.path}"


@dataclass
class AuditState:
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
    mcp_tools: list[tuple[str, str, str]] = field(default_factory=list)


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            f"{path}: PyYAML is required to read YAML OpenAPI specs"
        ) from exc
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_data(path: Path) -> Any:
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml(path)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1] if ref else ""


def resolve_ref(spec: dict[str, Any], value: Any) -> Any:
    if not isinstance(value, dict) or "$ref" not in value:
        return value
    ref = value["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return value
    current: Any = spec
    for part in ref.removeprefix("#/").split("/"):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return value
    return current if current is not None else value


def response_schema(spec: dict[str, Any], response: Any) -> dict[str, Any]:
    response = resolve_ref(spec, response)
    if not isinstance(response, dict):
        return {}
    content = response.get("content", {})
    if not isinstance(content, dict):
        return {}
    media = content.get("application/json") or content.get("application/problem+json")
    if not isinstance(media, dict):
        return {}
    schema = media.get("schema", {})
    return schema if isinstance(schema, dict) else {}


def request_schema(spec: dict[str, Any], op: dict[str, Any]) -> dict[str, Any]:
    body = resolve_ref(spec, op.get("requestBody", {}))
    if not isinstance(body, dict):
        return {}
    content = body.get("content", {})
    if not isinstance(content, dict):
        return {}
    media = content.get("application/json")
    if not isinstance(media, dict):
        return {}
    schema = media.get("schema", {})
    return schema if isinstance(schema, dict) else {}


def schema_has_property(
    spec: dict[str, Any],
    schema: dict[str, Any],
    names: set[str],
    seen: set[str] | None = None,
) -> bool:
    seen = seen or set()
    if "$ref" in schema:
        ref = str(schema["$ref"])
        if ref in seen:
            return False
        seen.add(ref)
        resolved = resolve_ref(spec, schema)
        return isinstance(resolved, dict) and schema_has_property(spec, resolved, names, seen)

    props = schema.get("properties", {})
    if isinstance(props, dict) and names.intersection(props):
        return True

    for key in ("allOf", "oneOf", "anyOf"):
        branches = schema.get(key, [])
        if isinstance(branches, list):
            for branch in branches:
                if isinstance(branch, dict) and schema_has_property(spec, branch, names, seen):
                    return True
    return False


def schema_ref_schema_name(spec: dict[str, Any], schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return ref_name(str(schema["$ref"]))
    return ""


def schema_is_ref_or_named(spec: dict[str, Any], schema: dict[str, Any], names: set[str]) -> bool:
    direct = schema_ref_schema_name(spec, schema)
    if direct in names:
        return True
    resolved = resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        return False
    for name in names:
        component = spec.get("components", {}).get("schemas", {}).get(name)
        if component is resolved:
            return True
    return False


def schema_is_operation(spec: dict[str, Any], schema: dict[str, Any]) -> bool:
    if schema_is_ref_or_named(spec, schema, {"Operation"}):
        return True
    resolved = resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        return False
    required = set(resolved.get("required", []))
    props = resolved.get("properties", {})
    return isinstance(props, dict) and {"name", "done"}.issubset(required | set(props))


def schema_is_error_envelope(spec: dict[str, Any], schema: dict[str, Any]) -> bool:
    if schema_is_ref_or_named(spec, schema, ERROR_ENVELOPE_SCHEMAS):
        return True
    resolved = resolve_ref(spec, schema)
    if not isinstance(resolved, dict):
        return False
    props = resolved.get("properties", {})
    return isinstance(props, dict) and "error" in props


def operation_params(operation: Operation) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    for source in (operation.path_item.get("parameters", []), operation.op.get("parameters", [])):
        if not isinstance(source, list):
            continue
        for raw in source:
            param = resolve_ref(operation.spec, raw)
            if isinstance(param, dict):
                params.append(param)
    return params


def params_by_location(operation: Operation, location: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for param in operation_params(operation):
        if param.get("in") == location and isinstance(param.get("name"), str):
            out[param["name"]] = param
    return out


def normalized_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path.rstrip("/") or "/")


def operation_id_verb(operation_id: str) -> str:
    return operation_id.rsplit(".", 1)[-1] if operation_id else ""


def is_transport_native_path(path: str) -> bool:
    normalized = path.rstrip("/") or "/"
    return normalized in TRANSPORT_NATIVE_PATHS


def is_list_operation(operation: Operation) -> bool:
    oid = operation.operation_id
    return oid.endswith(".list") or oid.startswith("list")


def is_async_operation(operation: Operation) -> bool:
    verb = operation_id_verb(operation.operation_id)
    if verb in ASYNC_VERBS:
        return True
    if any(code == "202" for code in operation.op.get("responses", {})):
        return True
    text = " ".join(
        str(operation.op.get(key, "")) for key in ("summary", "description")
    ).lower()
    return "long-running" in text or "async" in text


def is_mutating_operation(operation: Operation) -> bool:
    if operation.method not in MUTATING_METHODS:
        return False
    if is_transport_native_path(operation.path):
        return False
    if operation.operation_id in PUBLIC_OPERATION_IDS:
        return False
    return True


def list_response_schema(operation: Operation) -> dict[str, Any]:
    responses = operation.op.get("responses", {})
    if not isinstance(responses, dict):
        return {}
    for code in ("200", "201"):
        if code in responses:
            return response_schema(operation.spec, responses[code])
    return {}


def response_schemas(operation: Operation) -> list[tuple[str, dict[str, Any]]]:
    responses = operation.op.get("responses", {})
    if not isinstance(responses, dict):
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for code, response in responses.items():
        if isinstance(code, str):
            out.append((code, response_schema(operation.spec, response)))
    return out


def audit_openapi(contract: Contract, path: Path, state: AuditState) -> None:
    spec = load_data(path)
    if not isinstance(spec, dict):
        state.violations.append(f"{contract.service}: {path} did not parse to an object")
        return

    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        state.violations.append(f"{contract.service}: OpenAPI spec has no paths object")
        return

    seen_routes: dict[str, list[str]] = {}
    seen_operation_ids: dict[str, list[str]] = {}
    operations: list[Operation] = []

    for raw_path, path_item in paths.items():
        if not isinstance(raw_path, str) or not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            operation_id = op.get("operationId", "")
            if not isinstance(operation_id, str):
                operation_id = ""
            operation = Operation(
                service=contract.service,
                method=method,
                path=raw_path,
                operation_id=operation_id,
                op=op,
                path_item=path_item,
                spec=spec,
            )
            operations.append(operation)
            state.operations.append(operation)
            route_key = f"{method.upper()} {normalized_path(raw_path)}"
            seen_routes.setdefault(route_key, []).append(f"{method.upper()} {raw_path}")
            if operation_id:
                seen_operation_ids.setdefault(operation_id, []).append(
                    f"{method.upper()} {raw_path}"
                )
            elif not is_transport_native_path(raw_path):
                state.violations.append(f"{operation.where}: missing operationId")

    for route_key, wheres in seen_routes.items():
        if len(wheres) > 1:
            state.violations.append(
                f"{contract.service}: duplicate or shadowed route {route_key}: {wheres}"
            )

    for operation_id, wheres in seen_operation_ids.items():
        if len(wheres) > 1:
            state.violations.append(
                f"{contract.service}: duplicate operationId {operation_id!r}: {wheres}"
            )

    enforce_aip = contract.style in {"aip", "aip-target"}
    for operation in operations:
        if enforce_aip:
            audit_aip_operation(operation, state)

    if enforce_aip:
        audit_operation_schema(contract, spec, state)

    if contract.mcp_tools_from_openapi:
        for operation in operations:
            if operation.operation_id and not is_transport_native_path(operation.path):
                state.mcp_tools.append((contract.service, operation.operation_id, str(path)))

    print(
        f"audited {contract.service} OpenAPI: {len(operations)} operations "
        f"from {path}"
    )


def audit_aip_operation(operation: Operation, state: AuditState) -> None:
    if is_transport_native_path(operation.path):
        return

    if not operation.path.startswith("/v1/") and operation.path != "/v1":
        state.violations.append(f"{operation.where}: path is outside /v1")

    oid = operation.operation_id
    if not PROJECTS_OPERATION_ID.match(oid):
        state.violations.append(
            f"{operation.where}: operationId {oid!r} is not projects.<collection>[.<subcollection>].<verb>"
        )

    if is_list_operation(operation):
        query_params = params_by_location(operation, "query")
        for name in ("page_size", "page_token"):
            if name not in query_params:
                state.violations.append(f"{operation.where}: list endpoint missing query {name}")
        schema = list_response_schema(operation)
        for name in ("next_page_token", "total_size"):
            if not schema_has_property(operation.spec, schema, {name}):
                state.violations.append(
                    f"{operation.where}: list response missing {name}"
                )
        if "{parent" not in operation.path and "projects/" not in operation.path:
            state.violations.append(
                f"{operation.where}: list endpoint is not scoped under projects/*"
            )

    if is_mutating_operation(operation):
        headers = {name.lower(): param for name, param in params_by_location(operation, "header").items()}
        idem = headers.get("idempotency-key")
        if idem is None:
            state.violations.append(f"{operation.where}: mutating endpoint missing Idempotency-Key")
        elif idem.get("required") is not True:
            state.violations.append(f"{operation.where}: Idempotency-Key is not required")

    if operation.method == "patch":
        headers = {name.lower(): param for name, param in params_by_location(operation, "header").items()}
        if_match = headers.get("if-match")
        if if_match is None:
            state.violations.append(f"{operation.where}: PATCH missing If-Match")
        elif if_match.get("required") is not True:
            state.violations.append(f"{operation.where}: If-Match is not required")
        schema = request_schema(operation.spec, operation.op)
        if not schema_has_property(operation.spec, schema, {"update_mask", "updateMask"}):
            state.violations.append(f"{operation.where}: PATCH body missing update_mask")

    if is_async_operation(operation):
        success_schemas = [
            schema
            for code, schema in response_schemas(operation)
            if code.startswith("2")
        ]
        if not any(schema_is_operation(operation.spec, schema) for schema in success_schemas):
            state.violations.append(f"{operation.where}: async endpoint does not return Operation")

    if not is_transport_native_path(operation.path):
        error_codes = [
            code for code, _schema in response_schemas(operation) if code.startswith(("4", "5"))
        ]
        if not error_codes:
            state.violations.append(f"{operation.where}: no documented 4xx/5xx response")
        for code, schema in response_schemas(operation):
            if not code.startswith(("4", "5")):
                continue
            if not schema_is_error_envelope(operation.spec, schema):
                state.violations.append(
                    f"{operation.where}: error {code} does not use shared error envelope"
                )


def audit_operation_schema(contract: Contract, spec: dict[str, Any], state: AuditState) -> None:
    schemas = spec.get("components", {}).get("schemas", {})
    if not isinstance(schemas, dict):
        state.violations.append(f"{contract.service}: components.schemas is missing")
        return
    operation = schemas.get("Operation")
    if not isinstance(operation, dict):
        state.violations.append(f"{contract.service}: missing Operation schema")
        return
    props = operation.get("properties", {})
    if not isinstance(props, dict):
        state.violations.append(f"{contract.service}: Operation.properties is missing")
        return
    error = props.get("error")
    if not isinstance(error, dict):
        state.violations.append(f"{contract.service}: Operation.error is missing")
    elif not schema_is_ref_or_named(spec, error, ERROR_BODY_SCHEMAS):
        state.violations.append(
            f"{contract.service}: Operation.error must reference inner error body, not HTTP envelope"
        )


def load_mcp_catalog(contract: Contract, path: Path, state: AuditState) -> None:
    catalog = load_data(path)
    if isinstance(catalog, list):
        tools = catalog
    elif isinstance(catalog, dict) and isinstance(catalog.get("tools"), list):
        tools = catalog["tools"]
    else:
        state.violations.append(f"{contract.service}: {path} is not a tools list/catalog")
        return
    local: dict[str, int] = {}
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            state.violations.append(f"{contract.service}: {path} contains tool without name")
            continue
        name = tool["name"]
        local[name] = local.get(name, 0) + 1
        state.mcp_tools.append((contract.service, name, str(path)))
    for name, count in local.items():
        if count > 1:
            state.violations.append(
                f"{contract.service}: MCP catalog has duplicate tool {name!r}"
            )
    print(f"audited {contract.service} MCP catalog: {len(tools)} tools from {path}")


def audit_global_conflicts(
    contracts: dict[str, Contract],
    state: AuditState,
    *,
    shared_gateway: bool,
) -> None:
    gateway_routes: dict[str, list[str]] = {}
    for op in state.operations:
        contract = contracts[op.service]
        mount = "" if shared_gateway else contract.gateway_mount.strip("/")
        path = op.path if not mount else f"/{mount}{op.path}"
        key = f"{op.method.upper()} {normalized_path(path)}"
        gateway_routes.setdefault(key, []).append(f"{op.service} {op.method.upper()} {op.path}")
    for route, owners in gateway_routes.items():
        if len(owners) > 1:
            state.violations.append(
                f"gateway: duplicate route {route} across services: {owners}"
            )

    global_tools: dict[str, list[str]] = {}
    for service, name, source in state.mcp_tools:
        namespace = contracts.get(service, Contract(service)).mcp_namespace
        global_name = f"{namespace}.{name}" if namespace else name
        global_tools.setdefault(global_name, []).append(f"{service} ({source})")
    for name, owners in global_tools.items():
        if len(owners) > 1:
            state.violations.append(
                f"mcp: duplicate combined tool name {name!r}: {owners}"
            )


def configured_contracts(manifest: dict[str, Any]) -> dict[str, Contract]:
    raw = manifest.get("api_contracts", {})
    if not isinstance(raw, dict):
        return {}
    contracts: dict[str, Contract] = {}
    for service, spec in raw.items():
        if not isinstance(spec, dict):
            continue
        contracts[service] = Contract(
            service=service,
            repo_key=spec.get("repo_key"),
            repo_path=spec.get("repo_path"),
            openapi=spec.get("openapi"),
            mcp_catalog=spec.get("mcp_catalog"),
            style=spec.get("style", "aip-target"),
            required=bool(spec.get("required", False)),
            gateway_mount=spec.get("gateway_mount", ""),
            mcp_namespace=spec.get("mcp_namespace", ""),
            mcp_tools_from_openapi=bool(spec.get("mcp_tools_from_openapi", False)),
        )
    return contracts


def checkout_roots(args: argparse.Namespace) -> list[Path]:
    roots: list[Path] = []
    for value in args.checkout_root or []:
        roots.append(value.resolve())
    env_root = os.environ.get("TEMPERA_CHECKOUT_ROOT")
    if env_root:
        roots.append(Path(env_root).resolve())
    roots.extend(
        [
            ROOT.parent.resolve(),
            Path.home().resolve(),
            (Path.home() / "Desktop" / "ecosystem").resolve(),
        ]
    )
    deduped: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root not in seen:
            deduped.append(root)
            seen.add(root)
    return deduped


def resolve_repo_root(contract: Contract, manifest: dict[str, Any], roots: list[Path]) -> Path | None:
    names: list[str] = []
    if contract.repo_path:
        names.append(contract.repo_path)
    if contract.repo_key:
        repo_spec = manifest.get("repos", {}).get(contract.repo_key, {})
        if isinstance(repo_spec, dict) and isinstance(repo_spec.get("path"), str):
            names.append(repo_spec["path"])
        aliases = manifest.get("checkout_aliases", {}).get(contract.repo_key, [])
        if isinstance(aliases, list):
            names.extend(str(alias) for alias in aliases)
    for root in roots:
        for name in names:
            candidate = Path(name)
            if candidate.is_absolute() and candidate.is_dir():
                return candidate.resolve()
            path = root / name
            if path.is_dir():
                return path.resolve()
    return None


def resolve_contract_path(
    contract: Contract,
    manifest: dict[str, Any],
    roots: list[Path],
    rel_path: str | None,
) -> Path | None:
    if not rel_path:
        return None
    path = Path(rel_path)
    if path.is_absolute():
        return path if path.exists() else None
    repo_root = resolve_repo_root(contract, manifest, roots)
    if repo_root:
        candidate = repo_root / rel_path
        if candidate.exists():
            return candidate
    for root in roots:
        candidate = root / rel_path
        if candidate.exists():
            return candidate
    return None


def parse_named_path(value: str) -> tuple[str, str]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("expected service:path")
    service, path = value.split(":", 1)
    if not service or not path:
        raise argparse.ArgumentTypeError("expected service:path")
    return service, path


def add_overrides(contracts: dict[str, Contract], args: argparse.Namespace) -> None:
    for service, path in args.openapi or []:
        base = contracts.get(service, Contract(service=service, style="aip"))
        contracts[service] = Contract(
            service=base.service,
            repo_key=base.repo_key,
            repo_path=base.repo_path,
            openapi=path,
            mcp_catalog=base.mcp_catalog,
            style=base.style,
            required=True,
            gateway_mount=base.gateway_mount,
            mcp_namespace=base.mcp_namespace,
            mcp_tools_from_openapi=base.mcp_tools_from_openapi,
        )
    for service, path in args.mcp_catalog or []:
        base = contracts.get(service, Contract(service=service, style="mcp-native"))
        contracts[service] = Contract(
            service=base.service,
            repo_key=base.repo_key,
            repo_path=base.repo_path,
            openapi=base.openapi,
            mcp_catalog=path,
            style=base.style,
            required=True,
            gateway_mount=base.gateway_mount,
            mcp_namespace=base.mcp_namespace,
            mcp_tools_from_openapi=base.mcp_tools_from_openapi,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout-root", action="append", type=Path)
    parser.add_argument("--service", action="append", help="Configured service to audit")
    parser.add_argument("--openapi", action="append", type=parse_named_path, help="Override/add service:path")
    parser.add_argument("--mcp-catalog", action="append", type=parse_named_path, help="Override/add service:path")
    parser.add_argument("--strict-missing", action="store_true", help="Missing configured files are failures")
    parser.add_argument("--shared-gateway", action="store_true", help="Check raw paths as if all services share one /v1 host")
    parser.add_argument("--list", action="store_true", help="List configured contracts and resolved files")
    args = parser.parse_args(argv)

    manifest = load_toml(MANIFEST)
    contracts = configured_contracts(manifest)
    add_overrides(contracts, args)

    if args.service:
        selected = set(args.service)
        unknown = selected - set(contracts)
        if unknown:
            print(f"unknown API contract service(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        contracts = {name: contract for name, contract in contracts.items() if name in selected}

    if not contracts:
        print("no API contracts configured", file=sys.stderr)
        return 2

    roots = checkout_roots(args)
    state = AuditState()

    if args.list:
        for contract in contracts.values():
            openapi = resolve_contract_path(contract, manifest, roots, contract.openapi)
            catalog = resolve_contract_path(contract, manifest, roots, contract.mcp_catalog)
            print(
                f"{contract.service}: openapi={openapi or 'missing'} "
                f"mcp_catalog={catalog or 'missing'} style={contract.style}"
            )
        return 0

    for contract in contracts.values():
        openapi = resolve_contract_path(contract, manifest, roots, contract.openapi)
        catalog = resolve_contract_path(contract, manifest, roots, contract.mcp_catalog)

        if contract.openapi and openapi is None:
            message = f"{contract.service}: missing OpenAPI file {contract.openapi!r}"
            if args.strict_missing or contract.required:
                state.violations.append(message)
            else:
                state.warnings.append(message)
        elif openapi is not None:
            audit_openapi(contract, openapi, state)

        if contract.mcp_catalog and catalog is None:
            message = f"{contract.service}: missing MCP catalog {contract.mcp_catalog!r}"
            if args.strict_missing or contract.required:
                state.violations.append(message)
            else:
                state.warnings.append(message)
        elif catalog is not None:
            load_mcp_catalog(contract, catalog, state)

    audit_global_conflicts(contracts, state, shared_gateway=args.shared_gateway)

    if state.warnings:
        print(f"\n{len(state.warnings)} API CONTRACT WARNINGS:")
        for warning in state.warnings:
            print(f"  - {warning}")

    if state.violations:
        print(f"\n{len(state.violations)} API CONTRACT VIOLATIONS:")
        for violation in state.violations:
            print(f"  - {violation}")
        return 1

    print("API contract style/conflict check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
