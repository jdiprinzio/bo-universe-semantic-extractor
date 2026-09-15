# bo-universe-semantic-extractor

## Purpose

Extract and normalize semantic metadata (universes, classes, objects, joins, contexts) from SAP BusinessObjects Universe files (`.unv` / `.unx`) into structured, machine-readable output for downstream analysis, migration, and AI-assisted documentation.

## Objectives

- Parse BusinessObjects universe files and extract their semantic layer definitions.
- Normalize extracted metadata into a consistent, versioned schema.
- Support repeatable, auditable extraction runs driven by written specifications.
- Provide a foundation for AI-assisted (GitHub Copilot Agent Mode) development, testing, and documentation.

## Architecture

```text
repository-root/
│
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
│
├── .github/
│   ├── copilot-instructions.md
│   ├── prompts/
│   ├── workflows/
│   └── skills/
│
├── config/        # Runtime and extraction configuration
├── docs/          # Specifications and design documents
├── scripts/       # Operational / utility scripts
├── src/           # Application source code
├── tests/         # Automated tests
└── output/        # Generated extraction output (gitignored)
```

## Setup

1. Install Python 3.11 or later.
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -e .[dev]`
4. Copy `.env.example` to `.env` and populate local values (never commit `.env`).

## Copilot Usage

This repository is configured for GitHub Copilot Agent Mode:

- Repository-wide guidance lives in [.github/copilot-instructions.md](.github/copilot-instructions.md).
- Reusable skills live in [.github/skills/](.github/skills/), including [github-repository-bootstrap](.github/skills/github-repository-bootstrap/SKILL.md).
- Reusable prompts live in [.github/prompts/](.github/prompts/).
- CI workflows live in [.github/workflows/](.github/workflows/).

## Security Requirements

- Never commit secrets, credentials, or `.env` files.
- All configuration values must be sourced from environment variables or `config/`.
- Validate and sanitize all file inputs (universe files may originate from untrusted sources).
- Keep an audit trail of extraction runs (inputs, timestamps, output locations).

## Repository Structure

| Path | Purpose |
|------|---------|
| `src/` | Extraction and normalization source code |
| `config/` | Configuration files (non-secret) |
| `docs/` | Specifications, design docs, ADRs |
| `scripts/` | Helper / operational scripts |
| `tests/` | Unit and integration tests |
| `output/` | Generated artifacts (gitignored) |
| `.github/skills/` | Copilot Agent Mode skills |
| `.github/prompts/` | Reusable Copilot prompts |
| `.github/workflows/` | CI/CD pipelines |

## Development Workflow

1. Write or update a specification in `docs/specs/` before implementing a feature.
2. Implement the feature in `src/`, guided by the specification.
3. Add or update tests in `tests/` covering the new behavior.
4. Run `pytest`, `ruff check .`, and `mypy` locally before committing.
5. Keep commits small and reviewable; reference the relevant specification in the commit message.

## Implementation Specification — Read-Only Semantic Extraction Pipeline

This section is the authoritative, high-level specification for the first implementation of the
SAP BusinessObjects universe semantic extraction pipeline. Detailed operating rules live in
[.github/skills/bo-universe-semantic-extractor/SKILL.md](.github/skills/bo-universe-semantic-extractor/SKILL.md);
this section summarizes what is built and why.

### Purpose

Build a deterministic, auditable, **read-only** pipeline that extracts and documents the semantics
of one SAP BusinessObjects universe (and its dependent Web Intelligence documents) and produces an
agent-ready semantic package. Source metadata always comes from SAP-supported APIs/SDKs — never
from AI invention. AI may organize, summarize, and propose descriptions, but proposals are always
kept separate from extracted facts and default to an unapproved review state.

### Scope of the First Implementation

- One selected universe (UNX or UNV), identified by exact CUID or exact name.
- Published universe metadata: folders, dimensions, attributes/details, measures, filters, prompts,
  lists of values, object identifiers, descriptions, data types, expressions and aggregation
  metadata when exposed, and connection metadata without secrets.
- Dependent Web Intelligence document metadata: data providers, result objects, query filters,
  prompts, variables, formulas (when exposed), merged dimensions, and document identifiers.
- Archived, unmodified API responses (raw evidence) with content hashes and redaction records.
- Normalized, versioned, typed metadata (Pydantic models + JSON Schema).
- Optional, read-only HANA lineage enrichment.
- Generated human- and machine-readable documentation.
- Reconciliation test definitions and a runnable comparison harness.
- Explicit reporting of unsupported, missing, ambiguous, and unexposed metadata.

### Out of Scope (First Implementation)

- Any write, publish, republish, delete, promote, or overwrite operation against BusinessObjects.
- Any change to BusinessObjects security, connections, or user/group membership.
- Arbitrary or LLM-generated SQL execution; DDL/DML/procedures with side effects.
- Storing passwords, tokens, cookies, or service keys anywhere in the repository.
- Automatic production migration to Power BI or OData.

### Pipeline Stages

```text
DISCOVER -> EXTRACT -> ARCHIVE -> NORMALIZE -> ENRICH -> VALIDATE -> DOCUMENT -> RECONCILE
```

Each stage accepts typed input, returns typed output, writes a structured stage manifest, and is
restartable without corrupting previously archived evidence.

### Configuration Contract

Secrets are supplied only via environment variables (see `.env.example`); non-secret extraction
settings live in a YAML extraction profile such as [config/extraction_profiles/dev.yaml](config/extraction_profiles/dev.yaml).

Required environment variables: `BO_BASE_URL`, `BO_AUTH_TYPE`, `BO_USERNAME`, `BO_PASSWORD`.
Optional: `BO_CLIENT_ID`, `BO_CLIENT_SECRET`, `HANA_ADDRESS`, `HANA_PORT`, `HANA_USER`, `HANA_PASSWORD`.

### Normalized Data Model

Typed Pydantic models (`src/bo_semantic_extractor/models/`) define stable, versioned schemas for:
`Universe`, `UniverseObject`, `PhysicalSource`, `Relationship`, `WebIDocument`, `DataProvider`,
`ReportVariable`, `SecurityRule`, and `SemanticEnrichment` (AI-proposed metadata, kept separate from
extracted facts and defaulted to `review_status = AI_PROPOSED`).

### BusinessObjects Client

A `SemanticLayerClient` protocol (`src/bo_semantic_extractor/bo_client/`) abstracts REST/SDK access
so implementations can be swapped without changing extraction logic. Endpoint paths are never
invented: until an endpoint is confirmed from official documentation or configuration, the REST
implementation raises a clear `SDK_UNAVAILABLE`/`CONFIG_ERROR` describing the missing prerequisite
rather than guessing a URL.

### Generated Output

`output/{universe_slug}/` contains a universe manifest, human-readable summary, object catalog
(CSV/JSON), physical lineage, joins/contexts, prompts/filters, security rules, WebI inventory,
variable usage, business definitions, agent metadata, validation findings, an extraction report,
and reconciliation test cases. Scaffolding for this generation lives in
`src/bo_semantic_extractor/documentation/`.

### Current Status

This first change set adds scaffolding only: typed models, client interfaces, normalization
schemas, sanitized contract-test fixtures, and documentation-generation scaffolding. Extractors,
the CLI, HANA lineage enrichment, and the reconciliation harness are not yet implemented.

## BusinessObjects Integration Status

**No live connection to SAP BusinessObjects exists yet, and no endpoint path has been
implemented.** `RestSemanticLayerClient` intentionally raises `SdkUnavailableError` for every
operation until a real endpoint is confirmed and configured — see
[bo_client/rest_client.py](src/bo_semantic_extractor/bo_client/rest_client.py).

| Document | Purpose |
|---|---|
| [docs/businessobjects_api_requirements.md](docs/businessobjects_api_requirements.md) | What's confirmed vs. `REQUIRED_INPUT` for every API area (auth, session, universe discovery/metadata/objects, connections, WebI documents, data providers, queries, prompts, variables, merged dimensions). |
| [docs/businessobjects_payload_contracts.md](docs/businessobjects_payload_contracts.md) | Placeholder response shapes the NORMALIZE stage currently targets, matching the sanitized test fixtures — explicitly unconfirmed against real SAP payloads. Section 7 documents **confirmed** shapes from the internal Query Panel API (a separate surface from the `/biprws/` REST API). |
| [docs/businessobjects_missing_inputs.md](docs/businessobjects_missing_inputs.md) | Consolidated, prioritized checklist of exact documentation/samples/decisions needed before implementing any endpoint. |
| [docs/integration_readiness_plan.md](docs/integration_readiness_plan.md) | Inventories missing API/payload/SDK dependencies and prioritizes implementation tasks once real payloads become available. |

**Readiness to connect to a real BI Platform instance: ~0%.** Interfaces, typed models, and
placeholder payload contracts exist; zero `/biprws/` REST endpoint paths have been confirmed or
implemented. Priority 1 (authentication and session management) blocks everything else — see
the missing inputs document for the full list and how to resolve each item.

### Query Panel Outline Parser (Internal API, Not `/biprws/` REST)

A production parser exists for BusinessObjects' **internal Query Panel** outline tree — a
different, undocumented API surface confirmed only from sanitized evidence
(`docs/evidence/`), not the officially documented REST API used by `RestSemanticLayerClient`:

- Raw models: [models/query_panel_outline_raw.py](src/bo_semantic_extractor/models/query_panel_outline_raw.py)
  (`QueryPanelOutlineNode`, `QueryPanelOutlineUserData`; every raw field preserved, including
  unknown/future fields via `extra="allow"`).
- Normalized record: [models/query_panel_outline_normalized.py](src/bo_semantic_extractor/models/query_panel_outline_normalized.py)
  (`QueryPanelOutlineRecord`) — classifies `CLS_*`/`OBJ_*`/`BJ_*` identifier *patterns* and
  extracts unverified `table.column` lineage *candidates*; it never assigns a semantic
  `ObjectType` from the raw numeric codes (`objType`, `userData.c`, `userData.s` remain
  unmapped).
- Parser: [normalization/query_panel_outline.py](src/bo_semantic_extractor/normalization/query_panel_outline.py)
  (`parse_query_panel_outline_artifact`, `iter_outline_nodes`, `normalize_outline_artifact`).
- `object_catalog.json` can now be generated from parsed outline records via
  `generate_object_catalog_json_from_outline_records()` in
  [documentation/generator.py](src/bo_semantic_extractor/documentation/generator.py).

## ROUTE_B_SDK Milestone 1

The repository now contains the **SDK Exporter Skeleton** for the authoritative SAP Semantic
Layer Java SDK route. This milestone is deliberately CMS-disconnected: it validates local Java
runtime/classpath configuration, defines versioned JSON contracts, enforces read-only policy,
redacts secrets, and fails with `REQUIRED_INPUT` before any unconfirmed resource-loading or CMS
operation can run.

### Cross-Machine Operating Model

**Local workstation:** maintain Python orchestration, schemas, tests, Route A evidence/catalogs,
and review the transferred Route B package. Do not install or commit SAP SDK JARs here.

**Remote Windows RDP machine:** install/use Java 11+, SAP BusinessObjects 4.3 SDK JARs, IDT/CMS
connectivity, and the target universe permissions. Compile and run the exporter there using the
PowerShell scripts in `scripts/`. Credentials are environment variables only.

**Transfer boundary:** transfer only a sanitized, hashed `route_b_export/<universe>/<run_id>/`
package. Do not transfer credentials, session files, cookies, SAP installation media, or raw
connection secrets. Verify `hashes.sha256` after transfer.

### Milestone 1 Artifacts

- Java module: `remote-sdk-extractor/`
- Runtime/classpath manifest: `config/route_b/sdk_runtime_manifest.example.json`
- Remote classpath template: `remote-sdk-extractor/sdk-classpath.example.txt`
- Versioned contracts: `config/schemas/route_b/`
- Compile locally/remotely: `scripts/compile-route-b.ps1`
- Run local-only manifest/classpath/export boundary: `scripts/run-route-b.ps1`
- Run Java contract tests: `scripts/validate-route-b.ps1`
- Detailed specification: [docs/specs/001-route-b-sdk-exporter-milestone-1.md](docs/specs/001-route-b-sdk-exporter-milestone-1.md)
- SDK architecture package: [docs/sdk_extraction_architecture.md](docs/sdk_extraction_architecture.md), [docs/sdk_component_design.md](docs/sdk_component_design.md), [docs/sdk_json_contracts.md](docs/sdk_json_contracts.md), [docs/sdk_required_artifacts.md](docs/sdk_required_artifacts.md)

### Route B Runbook

On the remote Windows machine:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Set-Location C:\path\to\bo-universe-semantic-extractor
$env:JAVA_HOME = 'C:\path\to\sap-supported-jvm'
$env:SAP_SDK_CLASSPATH = 'C:\path\to\sap\sdk\*;C:\path\to\enterprise\sdk\*'
.\scripts\validate-route-b.ps1
.\scripts\run-route-b.ps1 -Command manifest
```

`-Command validate-classpath` is intentionally expected to fail on a machine without the SAP
JARs. `-Command export` is intentionally expected to fail with `REQUIRED_INPUT` in Milestone 1;
it does not connect to CMS. The first live operation is deferred to Milestone 2 after exact
SDK loading/retrieval APIs and remote artifacts are confirmed.

On the local workstation after transferring a sanitized export package:

```powershell
python -m json.tool route_b_export\dm_invoice_data_mart\<run_id>\export_manifest.json
Get-FileHash route_b_export\dm_invoice_data_mart\<run_id>\*.json -Algorithm SHA256
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = 'src'
python -m pytest -q
python -m ruff check .
python -m mypy src
```

### Milestone 2 Required Inputs

- Exact SAP SDK JAR filenames and versions on the remote machine.
- Java 11+ path and a successful remote `javac`/`java` environment check.
- CMS host/port and valid authentication type supplied outside source control.
- Exact CMS repository path or CUID for `DM_Invoice_Data_Mart.unx`.
- Confirmed local `.blx`/`.dfx` loading API from installed Javadocs or `javap` output.
- Read-only CMC View permissions for the universe and attached connections.
- A sanctioned non-production read-only test window.

## Milestone 2A: Runtime Discovery and Loading Bridge Discovery

Milestone 2A is implemented as a remote-only discovery bridge. It does not connect to CMS,
retrieve or load a universe, or generate HANA artifacts. The package is
`remote-sdk-extractor/dist/milestone-2a/`; the repository entrypoint is
`remote-sdk-extractor/scripts/run-milestone-2a.ps1` and the runbook is
[docs/milestone_2a_remote_runbook.md](docs/milestone_2a_remote_runbook.md).

The runner accepts SAP install root, IDT plugin directory, SAP-supported JVM bin directory,
local IDT project directory, working directory, and output directory. It inventories external
JARs without copying them, validates `config/route_b/confirmed_sdk_capabilities.json`, runs
`javap`, and executes only a reflection/class-loading probe. JVM version and architecture are
detected at runtime; Java 11 is not required.
