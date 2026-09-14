---
name: bo-universe-semantic-extractor
description: Build and run the first implementation of a read-only SAP BusinessObjects universe semantic extraction pipeline. Use when asked to inventory a UNX or UNV universe, extract universe and Web Intelligence metadata, normalize semantics, enrich HANA lineage, generate documentation, or create reconciliation tests for an AI-agent or Power BI migration.
---

# SAP BusinessObjects Universe Semantic Extractor

## Purpose

Build a deterministic, auditable, read-only pipeline that extracts and documents the semantics of one SAP BusinessObjects universe and produces an agent-ready semantic package.

The pipeline must use SAP-supported APIs or SDKs as the source of technical facts. AI may generate code, organize extracted metadata, identify gaps, and propose descriptions, but it must never invent source metadata or mark AI-generated interpretations as approved business definitions.

## Operating Mode

1. Work specification-first.
2. Inspect the repository before changing files.
3. Create a plan, then execute it without repeatedly asking for information already available in repository files or environment variables.
4. Use read-only access to BusinessObjects and SAP HANA.
5. Make small, reviewable changes.
6. Run tests after each meaningful implementation stage.
7. Preserve raw source evidence and data lineage.
8. Stop rather than perform a write, publish, delete, security-change, or unrestricted SQL operation.

## Scope of the First Implementation

The first implementation supports one selected universe and its dependent Web Intelligence documents. It must:

- Authenticate to the SAP BusinessObjects BI platform.
- Identify the target universe by CUID or exact name.
- Detect whether it is UNX or UNV.
- Extract published universe metadata.
- Extract folders, dimensions, attributes/details, measures, predefined filters, prompts, lists of values, object identifiers, descriptions, data types, expressions when exposed, and aggregation metadata when exposed.
- Extract connection metadata without secrets.
- Extract dependent Web Intelligence document metadata, data providers, selected result objects, query filters, prompts, variables, formulas when exposed, merged dimensions, and document identifiers.
- Archive unmodified API responses.
- Normalize extracted metadata into stable schemas.
- Optionally enrich physical lineage from SAP HANA metadata using read-only queries.
- Generate human-readable and machine-readable documentation.
- Generate reconciliation test definitions and a runnable comparison harness.
- Report unsupported, missing, ambiguous, and unexposed metadata explicitly.

## Out of Scope

Do not:

- Modify, publish, republish, delete, promote, or overwrite a universe or Web Intelligence document.
- Change BusinessObjects security, connections, or user/group membership.
- Execute DDL, DML, procedures with side effects, or arbitrary LLM-generated SQL.
- Store passwords, tokens, client secrets, cookies, or service keys in source control, logs, outputs, screenshots, fixtures, or prompts.
- Infer business approval from technical metadata.
- Claim complete physical lineage when the API or SDK does not expose it.
- Translate a universe automatically into a production Power BI model or production OData service in this first implementation.

## Source Priority

Use sources in this order:

1. SAP BI Semantic Layer REST API for published universe discovery, metadata browsing, controlled query construction, and query results when available.
2. SAP Web Intelligence REST API for document, data-provider, prompt, variable, merged-dimension, query, and result metadata.
3. SAP Semantic Layer Java SDK only for required design-time metadata not available through REST.
4. Retrieved IDT resources only when explicitly supplied and safely readable.
5. SAP HANA system catalog or approved metadata interface for read-only physical lineage enrichment.
6. BusinessObjects audit or approved usage source for prioritization and report/object usage.
7. Business-owner review for definitions, exceptions, valid dimensional combinations, security intent, and certification.

Never scrape the Central Management Console UI if a supported API or SDK is available.

## Required Repository Layout

Create or preserve this structure:

```text
bo-universe-semantic-extractor/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── .github/
│   ├── copilot-instructions.md
│   ├── prompts/
│   └── workflows/
├── config/
│   ├── extraction_profiles/
│   ├── catalog_schema.json
│   └── subject_areas.yaml
├── src/bo_semantic_extractor/
│   ├── cli.py
│   ├── config.py
│   ├── logging_config.py
│   ├── bo_client/
│   ├── extractors/
│   ├── models/
│   ├── normalization/
│   ├── lineage/
│   ├── documentation/
│   └── validation/
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── fixtures/
│   └── reconciliation/
├── raw/
├── normalized/
└── output/
```

Do not place secrets or production data samples in the repository. Keep `raw/`, `normalized/`, and `output/` ignored by default unless sanitized fixtures are intentionally committed.

## Configuration Contract

Use environment variables for secrets and a YAML extraction profile for non-secret settings.

Required environment variables:

```text
BO_BASE_URL
BO_AUTH_TYPE
BO_USERNAME
BO_PASSWORD
```

Optional environment variables:

```text
BO_CLIENT_ID
BO_CLIENT_SECRET
HANA_ADDRESS
HANA_PORT
HANA_USER
HANA_PASSWORD
```

Example profile:

```yaml
profile_name: dev
universe:
  cuid: null
  exact_name: null
  expected_type: UNX
repository:
  folder_path: null
extraction:
  include_webi_dependencies: true
  include_usage: false
  include_hana_lineage: false
  preserve_raw_responses: true
  fail_on_unknown_object_type: true
  max_documents: 500
output:
  root: output
  formats:
    - json
    - csv
    - markdown
security:
  read_only: true
  redact_headers:
    - Authorization
    - Cookie
    - Set-Cookie
```

Require either `universe.cuid` or `universe.exact_name`. Prefer CUID when both are present.

## Technical Architecture

Implement the pipeline as discrete stages:

```text
DISCOVER -> EXTRACT -> ARCHIVE -> NORMALIZE -> ENRICH -> VALIDATE -> DOCUMENT -> RECONCILE
```

Each stage must:

- Accept typed input.
- Return typed output.
- Write a structured stage manifest.
- Record source endpoint or SDK operation, extraction timestamp, source identifier, and status.
- Be restartable without corrupting previous evidence.
- Fail with a clear error category.

Use Python 3.11 or later for orchestration and normalization. Use `httpx` for HTTP, `pydantic` for models, `typer` for CLI, `pytest` for tests, `tenacity` for bounded retries, and standard logging with secret redaction. If the Java SDK is required, isolate it in a small Java module that emits versioned JSON matching the Python ingestion contract.

## Authentication and Secret Handling

- Load secrets only from environment variables or an approved secret provider.
- Never echo secrets.
- Redact authorization headers, cookies, tokens, passwords, and service keys.
- Disable HTTP body logging by default.
- Sanitize exception messages before writing logs.
- Add `.env`, credentials, raw cookies, and token files to `.gitignore`.
- Provide `.env.example` with placeholders only.
- Fail closed if authentication is unavailable.

## Raw Evidence Rules

Store raw responses unchanged except for removal or replacement of secrets and personal tokens.

Use this layout:

```text
raw/{run_id}/
  run_manifest.json
  universe/
  connections/
  objects/
  webi_documents/
  webi_queries/
  usage/
  hana_metadata/
```

Every raw file must have a companion metadata record containing:

- `run_id`
- `source_system`
- `source_operation`
- `source_identifier`
- `retrieved_at_utc`
- `http_status` when applicable
- `content_hash_sha256`
- `redactions_applied`

Never silently discard an API field. Preserve unknown fields in raw evidence and report them in the extraction summary.

## Normalized Data Model

Create versioned Pydantic models and JSON Schemas for at least:

### Universe

- universe_cuid
- universe_name
- universe_type
- repository_path
- description
- connection_ids
- source_system
- extracted_at_utc

### UniverseObject

- universe_cuid
- object_id
- technical_name
- object_name
- folder_path
- object_type
- description
- data_type
- select_expression
- where_expression
- aggregation_function
- projection_function
- associated_dimension_id
- list_of_values_id
- is_hidden
- is_deprecated
- access_level
- extraction_source
- source_evidence_path

Allowed object types:

```text
dimension
attribute
measure
filter
hierarchy
level
parameter
unknown
```

Do not map an unknown type to the closest known type. Preserve it as `unknown` and create a validation finding.

### PhysicalSource

- source_id
- source_platform
- database_name
- schema_name
- object_name
- object_type
- column_name
- evidence

### Relationship

- relationship_id
- left_source_id
- right_source_id
- join_expression
- join_type
- cardinality
- context_name
- is_shortcut
- extraction_source
- evidence

### WebIDocument

- document_cuid
- document_name
- repository_path
- universe_cuids
- last_modified_at when exposed
- extraction_source

### DataProvider

- document_cuid
- data_provider_id
- data_provider_name
- universe_cuid
- result_object_ids
- query_filters
- prompts
- query_properties

### ReportVariable

- document_cuid
- variable_id
- variable_name
- qualification
- formula
- dependencies
- extraction_source

### SecurityRule

- rule_id
- universe_cuid
- security_type
- restricted_resource
- source_rule_reference
- target_mapping
- validation_status

### SemanticEnrichment

Keep AI additions separate from extracted facts:

- canonical_term
- synonyms
- proposed_plain_language_definition
- proposed_compatible_dimensions
- proposed_required_filters
- proposed_question_examples
- generated_by_model
- generated_at_utc
- review_status
- reviewed_by
- reviewed_at_utc

Default `review_status` to `AI_PROPOSED`. Never set `APPROVED` automatically.

## Extraction Workflow

### Step 1: Inspect and Plan

- Read `README.md`, `.github/copilot-instructions.md`, profile YAML, schemas, and existing tests.
- Summarize what exists and what is missing.
- Produce a concise implementation plan linked to acceptance criteria.
- Do not replace working code without evidence that replacement is needed.

### Step 2: Scaffold

- Create the repository layout.
- Configure Python packaging, linting, typing, testing, and secret scanning.
- Add `.env.example` and `.gitignore`.
- Add a CLI with `discover`, `extract`, `normalize`, `document`, `validate`, and `reconcile` commands.

### Step 3: Implement BusinessObjects Client

Create an interface so REST and Java implementations can be swapped:

```python
class SemanticLayerClient(Protocol):
    def list_universes(self) -> list[UniverseSummary]: ...
    def get_universe(self, universe_cuid: str) -> RawArtifact: ...
    def list_universe_objects(self, universe_cuid: str) -> list[RawArtifact]: ...
    def list_dependent_documents(self, universe_cuid: str) -> list[RawArtifact]: ...
    def get_document_metadata(self, document_cuid: str) -> RawArtifact: ...
```

- Implement bounded retry for transient errors only.
- Do not retry authentication or authorization failures blindly.
- Support pagination explicitly.
- Add contract tests using sanitized fixtures.
- Record endpoint version and response media type.

Do not fabricate endpoint paths. Obtain them from repository documentation, supplied API specifications, or the installed SAP SDK documentation. If the exact endpoint is not established, create an interface and a failing test marked with a specific configuration requirement instead of inventing a URL.

### Step 4: Extract One Universe

- Resolve the universe by exact CUID or exact name.
- Fail on multiple exact-name matches.
- Archive the universe record and object tree.
- Traverse folders recursively.
- Preserve stable source IDs.
- Record missing descriptions, missing expressions, unknown types, and duplicate names.

### Step 5: Extract WebI Dependencies

- Discover documents that reference the universe using supported repository or document APIs.
- Extract data providers, selected objects, query filters, prompts, variables, formulas, and merged dimensions when exposed.
- Record features that the API does not expose.
- Create report-to-object and variable-dependency mappings.

### Step 6: Normalize

- Convert source payloads to typed normalized models.
- Preserve source evidence paths.
- Write deterministic JSON and CSV with stable column order.
- Use UTF-8.
- Sort records by stable identifiers, not display names alone.
- Validate normalized output against JSON Schema.

### Step 7: Enrich HANA Lineage

This stage is optional and read-only.

- Use only approved catalog queries or a read-only metadata tool.
- Parse extracted universe expressions for candidate schema, object, and column references.
- Verify candidates against HANA metadata.
- Distinguish `VERIFIED`, `PARSED_UNVERIFIED`, and `UNKNOWN` lineage.
- Never execute extracted SQL solely to discover lineage.
- Never query raw business data during metadata extraction unless a reconciliation test explicitly requires controlled data retrieval.

### Step 8: Generate Documentation

Generate:

```text
output/{universe_slug}/
  universe_manifest.yaml
  universe_summary.md
  object_catalog.csv
  object_catalog.json
  physical_lineage.csv
  joins_contexts.csv
  prompts_filters.csv
  security_rules.csv
  webi_report_inventory.csv
  report_object_usage.csv
  business_definitions.md
  agent_metadata.json
  validation_findings.csv
  extraction_report.md
  reconciliation_cases.yaml
```

The summary must include:

- Universe identity and type
- Extraction sources and timestamps
- Counts derived from normalized output
- Source connections without secrets
- Object-type summary
- Missing descriptions
- Unknown types
- Duplicate display names
- Report dependencies
- Variables outside the universe
- Lineage coverage by verification status
- Security metadata found and not found
- Extraction limitations
- Required business-owner decisions

Clearly label calculated counts as generated from the current extraction output.

### Step 9: Create Agent Metadata

Generate a machine-readable catalog but keep it non-authoritative until reviewed.

For each semantic object include:

- Stable ID
- Business name
- Object type
- Extracted description
- Expression lineage reference
- Aggregation
- Validated synonyms only
- Allowed dimensions only when explicitly configured or approved
- Required filters only when explicitly configured or approved
- Security classification
- Source evidence
- Review status

The agent metadata generator must not infer approved joins, aggregations, or security from names.

### Step 10: Create Reconciliation Harness

- Define YAML test cases.
- Build adapters for BusinessObjects and the intended target.
- Compare row count, totals, grouped totals, null behavior, and sample keys.
- Use explicit tolerances.
- Write machine-readable differences.
- Never treat narrative similarity as reconciliation.
- Do not store unrestricted production extracts.

Statuses:

```text
PASS
FAIL_DEFINITION
FAIL_JOIN
FAIL_AGGREGATION
FAIL_SECURITY
FAIL_FILTER
FAIL_DATE
FAIL_CURRENCY
FAIL_SOURCE
FAIL_AI_INTERPRETATION
NOT_RUN
```

## Validation Rules

At minimum, validate:

- Universe CUID is unique.
- Object IDs are unique within a universe.
- Every normalized record links to raw evidence.
- Object type is recognized or explicitly marked unknown.
- Measures identify aggregation metadata when exposed.
- Attributes reference an associated dimension when exposed.
- Duplicate business names are reported with folder paths.
- WebI object references resolve to extracted universe objects or are flagged.
- Variable dependencies resolve or are flagged.
- No secret patterns appear in outputs.
- No write-capable operations are invoked.
- Content hashes exist for raw artifacts.
- Documentation was generated from normalized data, not model memory.

## Testing Requirements

Create:

- Unit tests for parsing, normalization, redaction, hashing, and schema validation.
- Contract tests for every API response shape using sanitized fixtures.
- Negative tests for authentication failure, ambiguous universe name, pagination failure, unknown object type, and malformed payload.
- Snapshot tests for deterministic documentation output.
- Reconciliation tests with synthetic or approved test data clearly labeled as such.

Never use invented source data as if it came from BusinessObjects or HANA.

Run before completion:

```bash
python -m ruff check .
python -m mypy src
python -m pytest -q
```

If a configured tool is not installed, document the missing prerequisite and keep generated project files internally consistent.

## Error Categories

Use stable error codes:

```text
CONFIG_ERROR
AUTHENTICATION_ERROR
AUTHORIZATION_ERROR
NOT_FOUND
AMBIGUOUS_MATCH
API_CONTRACT_ERROR
PAGINATION_ERROR
RATE_LIMITED
SDK_UNAVAILABLE
UNSUPPORTED_METADATA
NORMALIZATION_ERROR
SCHEMA_VALIDATION_ERROR
LINEAGE_UNVERIFIED
SECRET_DETECTED
RECONCILIATION_FAILED
```

Produce a useful error message without leaking secrets.

## Human Review Gates

Require explicit review for:

- Final metric definitions
- Synonyms that affect query interpretation
- Compatible and incompatible dimensions
- Context and multi-fact behavior
- Currency and unit conversions
- Fiscal calendar logic
- Snapshot rules
- Row-level and object-level security migration
- WebI-variable migration destination
- Reconciliation certification
- Production publishing

AI proposals remain `AI_PROPOSED` until a named reviewer updates the status through a controlled review file or approved workflow.

## GitHub Copilot Behavior

When using this skill, Copilot must:

- Prefer repository evidence over assumptions.
- Explain which source file, API payload, schema, or test supports a change.
- Separate extracted facts, deterministic derivations, and AI proposals.
- Avoid placeholders in executable code unless paired with explicit failing tests or configuration errors.
- Never hard-code credentials, CUIDs, URLs, schema names, or environment-specific identifiers.
- Never weaken tests to make a build pass.
- Never suppress an unknown metadata type.
- Never silently truncate paginated results.
- Never claim reconciliation without executing the defined comparison.
- Use parameterized queries and allowlists.
- Keep approval prompts enabled for external tool calls.

## Definition of Done

The first implementation is complete only when:

- The target universe is resolved by stable identifier.
- Raw sanitized evidence is archived with hashes.
- Universe objects are normalized and schema-valid.
- WebI dependencies are extracted or limitations are explicitly documented.
- Every normalized record has source evidence.
- Documentation outputs are generated deterministically.
- Unknown and missing metadata are reported.
- No credentials or tokens are present in outputs.
- Unit and contract tests pass.
- A reconciliation harness and at least one non-production test definition exist.
- The extraction report states what is extracted, inferred, proposed, unsupported, and awaiting business review.

## Initial Prompt to Use with This Skill

Use this prompt after placing this file in `.github/skills/bo-universe-semantic-extractor/SKILL.md`:

```text
Use the bo-universe-semantic-extractor skill.

Inspect this repository and implement the first read-only SAP BusinessObjects universe semantic extraction pipeline described by the skill. Start by creating or updating README.md with the implementation specification and an acceptance-criteria checklist. Then scaffold the repository, implement typed configuration and models, create the BusinessObjects client interfaces, add sanitized fixture-based tests, and implement the deterministic extraction, normalization, documentation, and validation stages.

Do not invent SAP endpoint paths. If endpoint documentation or a sample response is not present, implement the interface, fixture contract, configuration requirement, and explicit error handling, then list the exact missing input in the extraction report. Do not perform write operations. Do not log secrets. Preserve raw evidence and distinguish extracted facts from AI proposals.

Target universe configuration must come from config/extraction_profiles/dev.yaml and secrets must come from environment variables. Run linting, type checking, and tests, fix failures without weakening the requirements, and finish with a concise summary of files created, tests executed, remaining prerequisites, and the command to run the extractor.
```

## Suggested CLI Contract

```bash
python -m bo_semantic_extractor discover --profile config/extraction_profiles/dev.yaml
python -m bo_semantic_extractor extract --profile config/extraction_profiles/dev.yaml
python -m bo_semantic_extractor validate --run-id RUN_ID
python -m bo_semantic_extractor document --run-id RUN_ID
python -m bo_semantic_extractor reconcile --case output/UNIVERSE/reconciliation_cases.yaml
```

## Completion Response Format

At completion, report:

1. Implementation summary
2. Files created or changed
3. Source interfaces implemented
4. Tests executed and outcomes
5. Security controls applied
6. Metadata extracted versus unsupported
7. Business-review items
8. Exact run commands
9. Remaining external prerequisites
