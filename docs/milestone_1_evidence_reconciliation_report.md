# Milestone 1 Evidence Reconciliation Report — ROUTE_B_SDK

**Date:** 2026-09-14
**Status:** COMPLETE

## Scope

This reconciliation was performed before Milestone 2. It did not write extraction logic, connect
to CMS, load a universe, or generate HANA artifacts. The repository did not contain a raw javap
transcript; the authoritative post-Milestone-1 javap capability list supplied with this task was
recorded as `CONFIRMED_BY_JAVAP` rather than attributed to an invented file path.

## Confirmed by javap

The new register and machine-readable capability file record all supplied Business Layer and Data
Foundation classes/methods, including:

- Business Layer identity/path, DataSource providers, Business Layer collections, hierarchies,
  analysis dimensions, dimension attributes, and measure default aggregation.
- Data Foundation tables, columns, SQL table metadata, aliases, derived expressions, join tables,
  columns, expressions, cardinality, outer type, operator, auto/custom flags, and context joins/
  exclusions.
- Exact enum values for `Cardinality`, `OuterType`, and `JoinOperator`.
- Core JARs: `com.sap.sl.sdk.jar`, `com.sap.sl.edp.relational.jar`,
  `com.sap.sl.edp.hana.jar`, `com.businessobjects.mds.datafoundation.jar`.

## Obsolete blockers removed

The following are no longer prerequisites:

- Join left/right table and column accessors.
- Join expression and cardinality accessors.
- SQL join outer type, operator, auto-join, and custom flags.
- Context join and excluded-join accessors.
- Alias base-table accessor.
- Derived table expression and encoded-expression accessors.
- Business Layer collection accessors, hierarchy/analysis-dimension accessors, and dimension
  attribute accessors.
- Measure default aggregation accessor.
- Core SDK JAR identification.
- A hard requirement for Java 11.

## Remaining True Blockers

1. Complete transitive SDK classpath.
2. Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
3. Confirmed method or service returning `DataSource`.
4. Confirmed method or service returning `DataFoundation`.
5. CMS details and permissions only if CMS retrieval is selected.
6. Remote working and export directories.

Milestone 2 must detect and report the SAP-supported JVM version and architecture matching the
installed BusinessObjects 4.3 client runtime; it must not enforce Java 11 without evidence.

## Files Created

- `docs/sdk_javap_evidence_register.md`
- `config/route_b/confirmed_sdk_capabilities.json`
- `docs/milestone_1_evidence_reconciliation_report.md`

## Files Modified

- `docs/milestone_1_completion_report.md`
- `docs/sdk_required_artifacts.md`
- `docs/sdk_extraction_architecture.md`
- `docs/sdk_component_design.md`
- `docs/sdk_json_contracts.md`
- `docs/businessobjects_missing_inputs.md`
- `docs/integration_readiness_plan.md`
- `config/route_b/sdk_runtime_manifest.example.json`

## Validation Results

- Full Python tests: **126 passed**.
- Route B contract tests: **6 passed**.
- Ruff: **clean**.
- Mypy strict: **38 source files, no issues**.
- JSON parsing: all Route B schemas and the confirmed capabilities file parsed successfully.
- PowerShell syntax: compile, validate, and run scripts parsed successfully.
- Java SDK runtime tests: not attempted; SAP SDK/JDK are not installed on this local workstation.
- CMS: not contacted.
- HANA: not contacted.
- HANA artifacts: not generated.
