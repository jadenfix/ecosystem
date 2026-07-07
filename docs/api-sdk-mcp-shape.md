# Shared API, SDK, and MCP Shape

Goal: every service in the ecosystem should feel like one product family from
the outside, even while each repo stays standalone. A caller should be able to
learn one SDK shape, one error model, and one MCP pattern, then move between
`Palette`, `cradle`, `tempo`, `temp.js`, `tempOS`, `remi`, and `Arrha` with
minimal new ceremony. Legacy binary, crate, or route names such as `beatbox`,
`beater-memory`, or `aetherctl` may remain inside their owning repos until their
repo-local rename tasks land, but new public docs and manifests should use the
canonical product names from `ecosystem.toml`.

This is a convergence profile, not a mandate to force every repo onto the same
transport. REST services should expose OpenAPI. JSON-RPC services should publish
a method manifest. Schema-first libraries should publish JSON Schema plus
conformance fixtures. The common rule is that each public boundary has one
machine-readable source of truth and every SDK/MCP/CLI surface derives from it
or is drift-checked against it.

## Client-Facing Shape

Every repo should describe the same client-facing facts in the same place and
use the same names across docs, SDKs, CLIs, MCP tools, examples, and fixtures:

- Contract path: OpenAPI, JSON-RPC manifest, MCP catalog, or JSON Schema.
- Base URL field: `base_url` on snake_case surfaces and `baseUrl` on camelCase
  surfaces.
- Auth field: `token` for Bearer auth. `api_key`/`apiKey` may remain only for
  legacy aliases and should be documented as such.
- Timeout field: `timeout_ms`/`timeoutMs`, measured in milliseconds.
- Output mode: `json` for stable machine-readable output; `text` only as a
  human convenience.
- Error fields: `status`, `code`, `message`, optional `request_id`, optional
  `details`.
- Idempotency field/header: use `Idempotency-Key` for HTTP unless the transport
  has a clearly documented equivalent.

If the CLI, SDK, MCP tool, and README cannot all be updated in the same PR, the
PR must add or update a drift fixture that makes the missing surface obvious.

Client-facing repos should also carry a small client-surface manifest using the
schema in `docs/client-surface-manifest.schema.json`. The manifest is the compact
SDK/CLI/auth/error contract that a future shared SDK core can consume without
learning every repo's internal layout. Run `scripts/audit-client-surface.py`
against that manifest when any SDK config, CLI flag, env var, auth rule, output
mode, operation name, or normalized error field changes.

Create a starting point with:

```sh
python3 scripts/audit-client-surface.py --print-template cradle \
  > docs/client-surface.json
```

The standard profile is intentionally narrow:

- SDK config starts with `base_url`, `token`, `timeout_ms`.
- CLI globals start with `--base-url`, `--token`, `--token-file`,
  `--timeout-ms`, `--output`, `--json`.
- Auth secret lookup is always `--token`, then `--token-file`, then the
  service-prefixed token env var.
- Service env vars use the canonical product name, uppercased with punctuation
  converted to underscores: `CRADLE_TOKEN`, `TEMP_JS_TOKEN`, `ARRHA_TOKEN`.
- Stable CLI output supports both `json` and `text`; JSON is the contract-shaped
  output used by tests and automation.
- Normalized SDK/CLI errors start with `status`, `code`, and `message`.
- MCP projections, when present, record their catalog path, drift check, shared
  auth behavior, and error mode in the same manifest.

Minimal Bearer-auth example:

```json
{
  "surface_version": "2026-07-07",
  "service": "cradle",
  "contract": {
    "type": "openapi",
    "path": "sdks/openapi.json",
    "drift_check": "cargo test -p beatbox-server --test openapi_drift"
  },
  "auth": {
    "scheme": "bearer",
    "header": "Authorization",
    "value_format": "Bearer <token>",
    "token_field": "token",
    "env_token": "CRADLE_TOKEN",
    "compat_headers": ["x-beatbox-api-key"],
    "compat_env": ["CRADLE_API_KEY"],
    "precedence": ["flag", "token_file", "env"]
  },
  "sdk": {
    "config_fields": ["base_url", "token", "timeout_ms"],
    "error_type": "ApiError",
    "operation_names": "contract"
  },
  "cli": {
    "global_flags": [
      "--base-url",
      "--token",
      "--token-file",
      "--timeout-ms",
      "--output",
      "--json"
    ],
    "env": ["CRADLE_BASE_URL", "CRADLE_TOKEN", "CRADLE_TIMEOUT_MS"],
    "output_modes": ["json", "text"],
    "operation_names": "contract"
  },
  "errors": {
    "fields": ["status", "code", "message", "request_id", "details"]
  },
  "mcp": {
    "path": "crates/beatbox-server/fixtures/mcp-tools.catalog.json",
    "drift_check": "cargo test -p beatbox-server --test mcp_catalog_drift",
    "tool_names": "catalog",
    "auth": "shared",
    "errors": "transport_native"
  }
}
```

## Service Profile

Services with HTTP control planes should use this shape:

- OpenAPI 3.1 as the committed machine contract.
- `/v1` for stable REST routes; health/readiness routes may sit outside `/v1`.
- Unique lower-camel `operationId` values, e.g. `createJob`, `getTrace`,
  `validateBrowserAdapter`.
- Exactly one resource tag per operation.
- Named request and response schemas; no anonymous success objects.
- A shared error envelope for every documented 4xx/5xx response.
- Transport-native endpoints such as MCP JSON-RPC may document transport errors
  in that protocol's shape instead of the REST error envelope; do not force a
  REST `ErrorResponse` onto `/mcp` if runtime returns a JSON-RPC envelope or an
  empty origin/CORS denial.
- Cursor pagination for list operations: `limit`, optional `cursor`, and
  response `next_cursor`/`nextCursor` according to that repo's wire casing.
- One drift gate that proves the served/generated contract equals the committed
  contract.
- REST repos should run the shared OpenAPI audit with `--enforce-auth` once
  their public spec declares Bearer security and public endpoint exemptions.

## SDK Profile

SDKs may be idiomatic per language, but they should share the same conceptual
surface:

- One client config shape: `base_url`/`baseUrl`, `token`, `timeout_ms`/
  `timeoutMs`, and optional service-scoped fields such as
  tenant, project, profile, or environment.
- `api_key`/`apiKey` is allowed only when a repo still exposes a documented
  compatibility API-key alias. New docs should call the value a Bearer token.
- Operation methods map from the canonical operation name.
- Transport errors and API errors are separate typed errors.
- API errors carry HTTP status, stable error code, message, optional request id,
  and optional structured details.
- Auth never goes in URLs or exception strings.
- Unknown response fields do not crash deserialization.
- SDK version follows the contract version.

The preferred auth shape for new clients is `Authorization: Bearer <token>`.
Existing service-specific API-key headers, such as `x-beatbox-api-key`, may stay
as compatibility aliases, but new SDK, CLI, MCP, and doc work should prefer
Bearer and test any alias against the same verifier.

For a future shared SDK core, this means every service can be described as:

```json
{
  "service": "cradle",
  "base_url": "http://127.0.0.1:7300",
  "auth": {"scheme": "bearer", "compat_headers": ["x-beatbox-api-key"]},
  "contract": "sdks/openapi.json",
  "operations": ["getHealth", "execute", "createJob"]
}
```

The generated or shared client can then reuse the same transport, retry,
timeout, auth, error, pagination, and MCP-tool projection code.

## CLI Profile

CLIs should mirror the SDK shape so docs, tests, and future shared client code
can describe one public surface:

- Use operation names from the contract for subcommands unless the CLI has a
  better domain noun that is documented as an alias.
- Every networked CLI accepts the same global flags where applicable:
  `--base-url`, `--token`, `--token-file`, `--timeout-ms`, `--output json|text`,
  and `--json` as a shortcut for JSON output.
- `--api-key` and `--api-key-file` may remain as deprecated aliases only when
  the service has a documented compatibility API-key header.
- Environment variables use the uppercase service prefix:
  `<SERVICE>_BASE_URL`, `<SERVICE>_TOKEN`, and `<SERVICE>_TIMEOUT_MS`.
- Compatibility aliases may also read `<SERVICE>_API_KEY`, but the canonical
  env var is `<SERVICE>_TOKEN`.
- `--token-file` reads secret material without printing it and wins over
  `<SERVICE>_TOKEN`; explicit `--token` wins over both for local debugging.
- SDKs, CLIs, and MCP clients must all use that same precedence:
  `--token`/config token, then token file, then env. Do not add repo-local
  precedence rules unless the manifest records and the audit allows the
  exception.
- JSON output is stable and contract-shaped. Text output may be friendly, but it
  must not be the only way to access a field.
- Authenticated commands must not follow redirects with auth headers attached.

## Auth And Errors

Auth and error handling are part of the public contract, not implementation
details:

- New HTTP clients use `Authorization: Bearer <token>`.
- A legacy `x-<service>-api-key` header is allowed only as a documented
  compatibility alias with a test proving it reaches the same verifier.
- MCP, CLI, and SDK callers use the same auth material and the same auth failure
  semantics as REST callers.
- Secrets never appear in URLs, logs, traces, panic messages, telemetry payloads,
  or exception strings.
- JSON requests send `content-type: application/json` and `accept:
  application/json`.
- API failures use one shared envelope per service. The SDK-facing normalized
  error shape is `status`, `code`, `message`, optional `request_id`, and optional
  `details`, regardless of language.
- Mutating operations that can be retried should accept an `Idempotency-Key`
  header or a clearly documented request idempotency field.

## MCP Profile

MCP should be a projection of the same operation contract whenever the service
has a stable REST control plane:

- `POST /mcp` for Streamable HTTP / JSON-RPC.
- `tools/list` returns one tool per operation plus explicitly documented
  composite tools.
- `tools/call` dispatches through the same auth and handler path as the REST
  operation.
- Tool names should use the canonical operation name unless a composite tool has
  a better domain name.
- Tool input schemas should be generated from or checked against the operation
  request schema.
- Tool results should include `structuredContent`; failures should set
  `isError: true`.

Services that are MCP-native, such as `beater.js` app tools or `tempo` browser
tools, should still publish a committed tool catalog fixture and drift-check it.
Use the current product name (`temp.js`) in public docs and reserve `beater.js`
for legacy package/binary identifiers that have not migrated yet.

## Schema Profile

Repos that are not REST services yet should still have one public shape:

- Contract schemas live in exactly one canonical directory.
- Conformance fixtures include at least one valid and one invalid example per
  public contract.
- The README points to the canonical directory and does not call any second copy
  canonical.
- If another directory exists for packaging, it is generated from the canonical
  source and checked for drift.

## Current Alignment

- `Palette`: reference implementation for REST/OpenAPI -> SDK/CLI/MCP.
- `cradle`: has the legacy `beatbox` OpenAPI and SDKs; should keep operation
  names, auth metadata, error docs, and future MCP projection tied to the same
  contract.
- `tempo`: MCP-native today; should add a committed MCP catalog fixture and, if
  it grows a REST control plane, an OpenAPI contract.
- `remi`: has legacy `beater-memory` `/v1` routes; should keep a committed route
  manifest now and add OpenAPI before publishing SDKs or MCP.
- `tempOS`: schema-first; should keep one canonical schema source and generate
  packaging copies from it.
- `Arrha`: JSON-RPC/gRPC domain with legacy `aether` binaries; should publish a
  JSON-RPC method manifest and SDK parity checks rather than pretending it is an
  OpenAPI service.
