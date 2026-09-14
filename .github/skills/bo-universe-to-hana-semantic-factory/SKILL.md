---
name: bo-universe-to-hana-semantic-factory
description: Build a reusable factory that extracts authoritative SAP BusinessObjects UNX metadata with SAP Semantic Layer and MDS SDKs, normalizes it, verifies HANA lineage, generates HANA Calculation View project artifacts, and reconciles results. Use DM_Invoice_Data_Mart.unx as the first golden universe, while keeping shared code configuration-driven for additional universes.
---

# BusinessObjects Universe to HANA Semantic Factory

## Mission

Build a repeatable pipeline that converts an SAP BusinessObjects UNX universe into governed SAP HANA semantic artifacts that can be consumed by Power BI, APIs, Copilot agents, and workflows.

Initial golden universe:

```text
DM_Invoice_Data_Mart.unx
```

End state:

```text
BO Universe
  -> authoritative SDK export
  -> canonical semantic model
  -> verified HANA lineage
  -> HANA implementation plan
  -> generated HANA project
  -> build and reconciliation
  -> certified HANA semantic views
```

Do not hard-code Invoice Data Mart logic into shared framework code. Each additional universe must be onboarded through configuration and extracted metadata.

## Governing Rules

1. Route B, the SAP SDK extraction, is authoritative for universe design metadata.
2. Route A, Query Panel and PDF extraction, remains a fallback and reconciliation source.
3. Preserve raw evidence before transformation.
4. Separate extracted facts, deterministic derivations, configuration mappings, AI proposals, and approved decisions.
5. Never invent SAP methods, metadata, HANA mappings, expressions, joins, cardinalities, security rules, or deployment behavior.
6. Never call SDK create, update, delete, publish, save-to-CMS, convert, or security-modification APIs.
7. Never store credentials, tokens, cookies, session data, or raw connection secrets.
8. Generate HANA artifacts only from verified canonical metadata and an approved plan.
9. Never deploy automatically.
10. Reconcile metadata, data, and security before certification.
11. Fail closed when ambiguity affects grain, joins, contexts, aggregation, security, or source lineage.
12. Produce the optimal complete implementation for the requested milestone, not a weak first version followed by an optional better version.

# Deliverables

## Deliverable 1: Remote Windows SDK Exporter

Runs on the Windows RDP machine containing IDT, SAP JVM, SAP SDK JARs, CMS connectivity, and universe access.

Inputs:

```text
CMS name
authentication type
runtime-only credentials
universe CUID or exact repository path
SDK JAR manifest
temporary workspace
output directory
run ID
```

Outputs:

```text
route_b_export/{universe_slug}/{run_id}/
  export_manifest.json
  universe_metadata.json
  business_layer.json
  business_objects.json
  prompts_lovs.json
  data_foundation.json
  tables_columns.json
  joins.json
  contexts.json
  aliases.json
  derived_tables.json
  connection_metadata.json
  sdk_environment.json
  extraction_findings.json
  hashes.sha256
```

Every record must be traceable to:

```text
schema_version
run_id
universe_cuid
universe_name
source_environment
source_system
extraction_method
extracted_at_utc
verification_status
SDK version
source identifier
content hash
```

### Confirmed SDK surfaces

Use only confirmed methods, installed Javadocs, `javap` evidence, or working SAP samples.

Confirmed business-layer surfaces include:

```text
DataSourceElement.getName()
DataSourceElement.getDescription()
DataSourceElement.getIdentifier()
BusinessLayerItem.getPath()
BusinessLayerItem.getFullPath()
BusinessLayer.getDimensions()
BusinessLayer.getMeasures()
BusinessLayer.getFilters()
Measure.getDefaultAggregation()
DataSource.getBusinessLayer()
DataSource.getPrompts()
DataSource.getListsOfValues()
DataSource.getContexts()
DataSource.getBusinessLayerItemFlatList()
```

Confirmed Data Foundation surfaces include:

```text
DataFoundation.getTables()
DataFoundation.getJoins()
DataFoundation.getContexts()
Table.getColumns()
SQLTable.getOwner()
SQLTable.getQualifier()
SQLTable.getType()
AliasTable.getAliasedTable()
DerivedTable.getExpression()
Join.getLeftColumns()
Join.getRightColumns()
Join.getExpression()
Join.getCardinality()
Join.getLeftTable()
Join.getRightTable()
SQLJoin.getOuterType()
SQLJoin.getOperator()
Context.getJoins()
Context.getExcludedJoins()
```

Preserve raw SAP enums exactly in Route B output.

### Business-layer fields

Capture where exposed:

```text
identifier
name
description
object type
path
full path
hidden
data type
format
result/filter/sort eligibility
LOV status
default aggregation
aggregation overload
custom properties
attributes
hierarchies
select expression
where expression
```

If an expression accessor is not confirmed, emit `UNSUPPORTED_BY_CONFIRMED_API` and retain Route A evidence.

### Data Foundation fields

Capture:

```text
foundation identifier and name
table identifier and name
runtime type
owner
qualifier
table type
columns and data types
keys
alias base table
derived SQL
HANA view type
HANA variables
```

### Join fields

Capture:

```text
join identifier
left and right tables
left and right columns
expression
cardinality
outer type
operator
shortcut flag
auto-join flag
custom flag
ANSI-92 level
context membership
```

### Security controls

Do not invoke setters even when interfaces expose them. Do not persist passwords. Delete temporary artifacts after export unless a non-production debug profile explicitly retains them. Close all sessions and SDK resources.

## Deliverable 2: Canonical Semantic Model Builder

Runs in the local VS Code repository. It ingests Route B JSON, compares Route A evidence, validates identifiers, and builds a versioned semantic graph.

Outputs:

```text
normalized/{universe_slug}/{run_id}/
  canonical_universe.json
  canonical_objects.json
  canonical_expressions.json
  canonical_sources.json
  canonical_joins.json
  canonical_contexts.json
  canonical_lineage_edges.json
  canonical_security.json
  normalization_findings.json
  route_a_vs_b_reconciliation.json
```

Canonical entities:

```text
Universe
BusinessFolder
BusinessObject
BusinessExpression
Prompt
ListOfValues
DataFoundation
SourceEntity
SourceColumn
AliasEntity
DerivedEntity
Join
Context
Connection
LineageEdge
SecurityRule
GenerationDecision
ValidationFinding
```

Verification statuses:

```text
VERIFIED_FROM_SDK
VERIFIED_FROM_HANA
CONFIRMED_FROM_ROUTE_A
DERIVED_DETERMINISTICALLY
PARSED_UNVERIFIED
AI_PROPOSED
CONFLICT
UNKNOWN
```

Normalization rules:

```text
C1_1 -> ONE_TO_ONE
C1_N -> ONE_TO_MANY
CN_1 -> MANY_TO_ONE
CN_N -> MANY_TO_MANY
CUNKNOWN -> UNKNOWN

OUTER_NONE -> INNER
OUTER_LEFT -> LEFT_OUTER
OUTER_RIGHT -> RIGHT_OUTER
OUTER_FULL -> FULL_OUTER
OUTER_UNKNOWN -> UNKNOWN
```

Preserve raw values. Resolve aliases through authoritative base-table references, but preserve role-playing aliases as distinct semantic nodes. Store derived SQL unchanged and parse its dependencies separately. Keep each BusinessObjects context as a distinct join-path graph. Match Route A to Route B by stable identifier first, then exact full path and name. Report ambiguity and conflicts.

## Deliverable 3: HANA Lineage Verifier

Uses read-only SAP HANA metadata access to verify each canonical source object and column.

Outputs:

```text
output/{universe_slug}/{run_id}/hana-lineage/
  hana_objects.json
  hana_columns.json
  hana_dependencies.json
  source_resolution.json
  unresolved_sources.json
  environment_mapping_report.json
  hana_lineage_findings.json
```

Rules:

1. Apply configured schema and object mappings.
2. Verify source object existence and type.
3. Verify each referenced column.
4. retrieve view and Calculation View dependencies through approved catalog metadata.
5. Do not execute extracted SQL to discover lineage.
6. Do not query business data during metadata verification.
7. Treat multiple physical matches as `AMBIGUOUS_SOURCE`.
8. Block generation when required sources or columns remain unverified.

## Deliverable 4: HANA Semantic Design Planner

Transforms the canonical graph into an explicit, reviewable HANA implementation plan.

Outputs:

```text
output/{universe_slug}/{run_id}/hana-plan/
  semantic_implementation_plan.json
  node_graph.json
  output_semantics.json
  parameter_plan.json
  filter_plan.json
  measure_plan.json
  context_strategy.json
  unsupported_logic.json
  generation_findings.json
```

The planner decides whether logic becomes:

```text
synonym
projection node
join node
aggregation node
calculated column
input parameter
variable
SQL view
SQLScript table function
dimension Calculation View
fact Calculation View
consumption Calculation View
```

### Model design

Prefer source synonyms, reusable dimension projections, fact projections, reusable joins, then one or more consumption views. Do not force every universe into one giant view.

### Contexts

A BO context can represent an alternative valid join path. Choose one of:

```text
ONE_CONTEXT_ONE_CONSUMPTION_VIEW
CONTEXT_PARAMETER_WITH_VALIDATED_BRANCHING
CONTEXT_SPLIT_BY_SUBJECT_AREA
SINGLE_CONTEXT_NOT_REQUIRED
UNSUPPORTED_CONTEXT_CONFIGURATION
```

Never merge conflicting contexts silently.

### Joins

Preserve authoritative join type and cardinality. Treat many-to-many joins as blocking until an approved bridge or aggregation strategy exists.

### Aliases

Create separate aliases or projections for role-playing dimensions, including multiple date, address, customer, or organization roles.

### Derived tables

Classify each as:

```text
PROJECTION_COMPATIBLE
JOIN_GRAPH_COMPATIBLE
AGGREGATION_COMPATIBLE
SQL_VIEW_REQUIRED
TABLE_FUNCTION_REQUIRED
MANUAL_REVIEW_REQUIRED
```

### Expressions

Classify each as:

```text
DIRECT_COLUMN
CALCULATED_COLUMN
CASE_EXPRESSION
AGGREGATED_MEASURE
AGGREGATE_AWARE
CROSS_OBJECT_REFERENCE
FILTER_EXPRESSION
DATABASE_FUNCTION
UNSUPPORTED
```

Preserve null handling, data type, precision, aggregation, currency, unit, date, and snapshot semantics.

### Grain

The plan must establish:

```text
base grain
business key
fact key
snapshot behavior
duplicate risk
aggregation grain
```

Stop generation if grain remains unresolved.

## Deliverable 5: HANA Artifact Generator

Generates a complete SAP HANA database project from an approved plan and approved templates.

Output:

```text
generated-hana/{universe_slug}/{run_id}/
  mta.yaml
  db/
    package.json
    src/
      synonyms/
      grants/
      views/dimensions/
      views/facts/
      views/consumption/
      sqlviews/
      functions/
      roles/
      tests/
  metadata/
    generation_manifest.json
    source_to_artifact_map.json
    lineage.json
    unsupported_logic.json
    manual_review_checklist.md
  README.md
```

Supported generated artifact types:

```text
.hdbcalculationview
.hdbview
.hdbfunction
.hdbsynonym
.hdbsynonymconfig
.hdbgrants
.hdbrole
```

Controls:

1. Use approved known-good BAS/HANA templates. Never fabricate artifact XML or schemas.
2. Record template version.
3. Use deterministic names and node IDs.
4. Keep environment-specific sources behind synonyms where appropriate.
5. Generate no credentials.
6. Do not generate production deployment by default.
7. Link each generated node to canonical IDs and evidence.
8. Produce unsupported-logic findings rather than approximating behavior.
9. Generate multiple consumption views when contexts or subject areas require separation.

Initial universe configuration:

```yaml
universe:
  exact_name: DM_Invoice_Data_Mart.unx
  slug: dm_invoice_data_mart
  format: UNX
  expected_fact_candidates:
    - FCTV_INVOICE
route_a:
  enabled_for_reconciliation: true
route_b:
  enabled: true
hana_generation:
  deployment_enabled: false
  require_hana_source_verification: true
  require_reconciliation_before_certification: true
  context_strategy: AUTO_WITH_REVIEW_GATE
```

The fact candidate is a validation expectation, not permission to override SDK evidence.

## Deliverable 6: Reconciliation and Certification Harness

Perform four validation levels.

### Metadata reconciliation

Compare Route A and Route B for objects, identifiers, paths, expressions, aggregations, sources, joins, contexts, filters, prompts, and counts.

### Structural reconciliation

Compare the canonical model with generated HANA design for source, column, join, cardinality, context, measure, filter, and unsupported-logic coverage.

### Data reconciliation

Compare BusinessObjects and HANA using approved cases:

```text
row counts
distinct business keys
grand totals
grouped totals
null counts
minimum and maximum dates
currency totals
quantity totals
sample records
```

### Security reconciliation

Validate configured security personas and restrictions. Do not assume BO security transfers automatically to HANA.

Certification statuses:

```text
NOT_READY
METADATA_EXTRACTED
METADATA_RECONCILED
HANA_PLAN_APPROVED
ARTIFACTS_GENERATED
BUILD_VALIDATED
DATA_RECONCILED
SECURITY_RECONCILED
CERTIFIED_FOR_CONSUMPTION
FAILED
```

Outputs:

```text
output/{universe_slug}/{run_id}/certification/
  metadata_reconciliation.json
  structural_reconciliation.json
  data_reconciliation.json
  security_reconciliation.json
  exceptions.csv
  certification_manifest.json
  certification_report.md
```

## Deliverable 7: Multi-Universe Orchestrator

Create one configuration per universe under `config/universes/`. Do not duplicate framework code.

Required command flow, adapted to the existing Typer CLI:

```text
bo-semantic sdk-package --universe dm_invoice_data_mart
bo-semantic ingest-sdk --input route_b_export/...
bo-semantic normalize --universe dm_invoice_data_mart --run-id ...
bo-semantic verify-hana --universe dm_invoice_data_mart --run-id ...
bo-semantic plan-hana --universe dm_invoice_data_mart --run-id ...
bo-semantic generate-hana --universe dm_invoice_data_mart --run-id ...
bo-semantic reconcile --universe dm_invoice_data_mart --run-id ...
bo-semantic status --universe dm_invoice_data_mart --run-id ...
bo-semantic batch --manifest config/universe_batch.yaml
```

Batch generation must not imply production deployment.

# Cross-Machine Operating Model

## Local workstation

Use VS Code and GitHub Copilot to maintain all source, tests, schemas, local Python processing, HANA generation, and review.

## Remote Windows machine

Use installed SAP JVM, IDT, SDK JARs, and CMS connectivity to compile and run the Java SDK exporter.

## Transfer boundary

Transfer only the Route B export package. Do not transfer credentials, session files, or SAP installation files unless policy permits. Verify hashes after transfer.

# Target Repository Structure

```text
bo-universe-semantic-extractor/
  .github/skills/bo-universe-to-hana-semantic-factory/SKILL.md
  config/universes/
  config/environments/
  config/mappings/
  config/schemas/
  remote-sdk-extractor/
    pom.xml
    scripts/
    src/main/java/
    src/test/java/
  src/bo_semantic_extractor/
    route_a/
    route_b/
    canonical/
    lineage/
    hana_planner/
    hana_generator/
    reconciliation/
    orchestration/
  tests/
  evidence/
  raw/
  normalized/
  output/
  generated-hana/
```

Ignore evidence and generated output directories unless content is sanitized and intentionally committed.

# Test Requirements

Java tests:

```text
configuration
runtime dependency inventory
secret redaction
resource cleanup
stable JSON
unknown enums
alias resolution
derived-table extraction
join extraction
context extraction
empty and malformed resources
```

Python tests:

```text
JSON schemas
Route B normalization
Route A reconciliation
identifier matching
expression parsing
lineage graph
HANA verification adapters
planning decisions
unsupported logic
artifact generation
multi-universe isolation
deterministic output
```

Use DM_Invoice_Data_Mart.unx as the initial golden universe. Do not generalize an Invoice-specific behavior until a second universe provides confirming evidence.

# Stop Conditions

Stop HANA generation when any of these affect the requested output:

```text
ambiguous universe
conflicting SDK metadata
critical Route A versus Route B conflict
unknown required join type or cardinality
many-to-many join without approved strategy
unresolved context
unresolved alias role
unclassified derived SQL
unverified HANA object or column
unknown measure aggregation
unresolved grain
undefined security migration
unverified HANA artifact template
failed reconciliation
```

Partial catalogs may still be generated, but they must not be described as equivalent or certified.

# Implementation Milestones

## Milestone 1: SDK Exporter Skeleton

Create the Java module, runtime inventory, classpath manifest, JSON contracts, PowerShell compile/run scripts, read-only enforcement, secret redaction, and tests. Do not connect live.

## Milestone 2: Local Resource Proof of Concept

Load or retrieve DM_Invoice_Data_Mart through confirmed APIs. Export business-layer and Data Foundation counts. Compare to Route A.

## Milestone 3: Full Route B Export

Export all authoritative JSON, hashes, and findings. Close resources and transfer the package.

## Milestone 4: Canonical Model

Ingest, normalize, reconcile Route A and Route B, and emit conflicts.

## Milestone 5: HANA Verification

Verify source objects, columns, mappings, and dependencies.

## Milestone 6: HANA Plan

Build a context-aware node graph, resolve grain, classify expressions and derived tables, and create an approval package.

## Milestone 7: HANA Generation

Generate a HANA database project from approved templates and validate it structurally.

## Milestone 8: Build and Reconciliation

Build in development, run approved comparisons, and correct only source-backed differences.

## Milestone 9: Certification

Require successful data and security reconciliation. Never deploy to production automatically.

## Milestone 10: Multi-Universe Generalization

Add a second universe, run the pipeline, identify Invoice-specific assumptions, and generalize only evidence-backed patterns.

# Copilot Behavior

When this skill is active, Copilot must:

1. Inspect existing source, tests, evidence, and skills first.
2. Reuse the working Route A pipeline.
3. Use only confirmed SAP classes and methods.
4. Mark unknown APIs as `REQUIRED_INPUT` with typed failure.
5. Keep shared code universe-neutral.
6. Never hard-code secrets, hosts, transient IDs, or production identifiers.
7. Never invoke write-capable SDK operations.
8. Never weaken tests.
9. Preserve raw evidence and hashes.
10. Prefer one complete, optimal script or implementation over progressive alternatives.
11. Keep PowerShell and code outputs free of formatting corruption.
12. Report unsupported semantics explicitly.
13. Run all applicable checks after every milestone.

# Definition of Done for a Universe

```text
Route B export succeeds
JSON schemas validate
Route A and Route B reconcile
critical conflicts are resolved
HANA objects and columns are verified
contexts have approved implementations
aliases preserve roles
derived tables are implemented or explicitly unsupported
measures have authoritative aggregation
grain is defined
generated HANA artifacts validate and build
data reconciliation passes
security reconciliation passes
certification is approved
```

# Initial Agent Mode Prompt

Place this file at:

```text
.github/skills/bo-universe-to-hana-semantic-factory/SKILL.md
```

Then run:

```text
Use the bo-universe-to-hana-semantic-factory skill.

Inspect the current repository and implement Milestone 1, SDK Exporter Skeleton, completely.

DM_Invoice_Data_Mart.unx is the first golden universe, but all shared code, schemas, scripts, and configuration must support additional universes without duplication.

Reuse the existing Query Panel, PDF extraction, catalog, validation, and test assets. Do not replace working Route A components.

Create the remote Java SDK module, versioned JSON schemas, SDK runtime and classpath validation, clean PowerShell compile and run scripts, read-only enforcement, secret redaction, stable JSON serialization, and unit and contract tests. Use only SAP classes and methods confirmed in repository evidence, installed Javadocs, or javap output. Mark every unconfirmed loading or retrieval call as REQUIRED_INPUT with a typed failure. Do not invent APIs. Do not connect to CMS. Do not generate HANA artifacts yet.

Update README.md with the cross-machine operating model, exact artifacts, transfer procedure, and runbook.

Run all applicable Java and Python checks and fix failures without weakening requirements.

Finish with:
1. Files created and modified
2. Java module structure
3. SDK dependencies confirmed and unresolved
4. JSON contracts
5. Security controls
6. Tests and results
7. Exact remote commands
8. Exact local commands
9. Required inputs for Milestone 2
```

For later stages, use:

```text
Use the bo-universe-to-hana-semantic-factory skill.

Continue from the current passing repository state and implement Milestone N exactly as defined by the skill. Use DM_Invoice_Data_Mart.unx as the golden universe while keeping shared code universe-neutral. Execute all available tests, preserve evidence, do not weaken controls, and stop at the milestone boundary with a complete implementation report.
```
