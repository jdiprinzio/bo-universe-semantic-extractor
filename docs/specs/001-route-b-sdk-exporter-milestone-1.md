# Specification: ROUTE_B_SDK Milestone 1

## Purpose and Scope

Create a cross-machine SAP BusinessObjects Semantic Layer Java SDK exporter skeleton for
`DM_Invoice_Data_Mart.unx` and future configured universes. This milestone validates runtime
configuration/classpath, establishes stable JSON contracts, enforces read-only operation policy,
and provides a typed failure before any CMS connection or unconfirmed SDK loading call.

## Inputs

- Remote Windows machine with Java, SAP BI SDK JARs, and optional CMS environment variables.
- Non-secret universe configuration under `config/universes/`.
- SDK classpath supplied at runtime through `SAP_SDK_CLASSPATH` or PowerShell `-SdkClasspath`.
- Runtime-only credentials through environment variables; no credential files.

## Outputs

- `route_b_export/{universe_slug}/{run_id}/` artifact layout.
- Versioned JSON Schema contracts under `config/schemas/route_b/`.
- Runtime/classpath inventory and typed validation findings.
- No live export in Milestone 1; unconfirmed resource loading/retrieval fails with `REQUIRED_INPUT`.

## Business Rules / Edge Cases

- No CMS connection is attempted by any Milestone 1 command.
- No SDK write-capable operation is allowed.
- Credentials, tokens, cookies, and connection password parameters are never serialized.
- JSON serialization is UTF-8, deterministic, and uses stable field order.
- SDK classes are checked by reflection only; no SAP API is assumed beyond confirmed class names.
- Missing SDK JARs and unresolved loading/retrieval APIs are typed failures, not fallbacks.

## Acceptance Criteria

- [ ] Java module compiles with standard JDK only.
- [ ] Runtime classpath validation reports confirmed class names without connecting to CMS.
- [ ] Missing SDK classes produce a typed `REQUIRED_INPUT` failure.
- [ ] Read-only policy rejects write/publish/save/create/update/delete/convert operations.
- [ ] Secret redaction tests pass.
- [ ] Stable JSON and all six contract schemas are present.
- [ ] PowerShell compile/validation scripts work on Windows.
- [ ] README documents remote/local operating model and transfer runbook.

## Out of Scope

- CMS authentication execution.
- `.unx` retrieval or `.blx`/`.dfx` loading.
- Business Layer/Data Foundation extraction.
- HANA verification or artifact generation.
- Production deployment.
