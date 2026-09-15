# Milestone 2A Patch Release 11 Report

## Namespace Corrections

The capability registry now matches the installed BusinessObjects 4.3 runtime:

- Business Layer: `com.sap.sl.datasource.*` from `com.sap.sl.sdk.jar`.
- Data Foundation: `com.businessobjects.mds.datafoundation.*` from `com.businessobjects.mds.datafoundation.jar`.
- Enums: `Cardinality`, `Outer`, and `JoinOperator` use the runtime-confirmed Data Foundation namespace and preserve the confirmed values.

The probe still parses `capabilities[*].class`, loads each class reflectively, and now deduplicates missing-class diagnostics while including the expected JAR from each capability record.

This is a namespace correction only; the previously confirmed method evidence remains valid.

## Validation

- Focused Route B contract tests: **18 passed** after the patch.
- Full Python suite: **138 passed** after the patch.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- No SAP SDK runtime, CMS, HANA, or Milestone 2B execution performed.
