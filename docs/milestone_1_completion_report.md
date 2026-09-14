# Milestone 1 Completion Report — ROUTE_B_SDK

**Date:** 2026-09-14
**Milestone:** SDK Exporter Skeleton
**Status:** COMPLETE as a local/remote skeleton; remote Java SDK validation remains a required environmental step.

**Post-Milestone-1 evidence reconciliation:** javap evidence supplied after the original report
is authoritative for the SDK capabilities in `docs/sdk_javap_evidence_register.md` and
`config/route_b/confirmed_sdk_capabilities.json`. The obsolete accessor/JAR/JVM gaps below are
superseded by the reconciliation report.

See [milestone_1_evidence_reconciliation_report.md](milestone_1_evidence_reconciliation_report.md)
for the complete post-run capability and blocker reconciliation.

## 1. Recovery Audit

The previous run had already created the core Java skeleton and Route B schemas. Recovery did not recreate or replace those files. The incomplete items were PowerShell scripts, Java contract tests, runtime/classpath manifests, README operating-model documentation, and local Python contract coverage. Those items were added in this recovery run.

No CMS connection was attempted. No SAP SDK class was instantiated. No HANA artifact was generated. Route A components were not changed.

## 2. Files Created in This Recovery Run

- `config/route_b/sdk_runtime_manifest.example.json`
- `config/schemas/route_b/common.schema.json`
- `config/schemas/route_b/business_layer.schema.json`
- `config/schemas/route_b/data_foundation.schema.json`
- `config/schemas/route_b/join_metadata.schema.json`
- `config/schemas/route_b/connection_metadata.schema.json`
- `config/schemas/route_b/context_metadata.schema.json`
- `config/schemas/route_b/lineage_edges.schema.json`
- `remote-sdk-extractor/sdk-classpath.example.txt`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/RouteBMain.java`
- `remote-sdk-extractor/src/test/java/com/vistance/bo/routeb/RouteBContractTest.java`
- `scripts/compile-route-b.ps1`
- `scripts/validate-route-b.ps1`
- `scripts/run-route-b.ps1`
- `tests/contract/test_route_b_milestone_1_contract.py`
- `docs/specs/001-route-b-sdk-exporter-milestone-1.md`
- `docs/milestone_1_completion_report.md`

## 3. Files Modified in This Recovery Run

- `.gitignore` — ignores Route B generated exports, Java target output, SDK JARs, and runtime classpath files.
- `README.md` — adds the cross-machine model, artifact list, transfer boundary, PowerShell runbook, and Milestone 2 inputs.
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/StableJson.java` — fixes nested map/list serialization so manifests remain valid deterministic JSON.

## 4. Existing Milestone 1 Files Preserved

The following were present before recovery and were retained:

- `remote-sdk-extractor/pom.xml`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/RequiredInputException.java`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/ReadOnlyPolicy.java`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/SecretRedactor.java`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/SdkClasspathValidator.java`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/ExporterConfig.java`
- `remote-sdk-extractor/src/main/java/com/vistance/bo/routeb/RouteBExporter.java`
- `config/universes/dm_invoice_data_mart.yaml`
- `docs/specs/001-route-b-sdk-exporter-milestone-1.md`
- the seven versioned Route B schema files

## 5. Java Module Structure

```text
remote-sdk-extractor/
  pom.xml
  sdk-classpath.example.txt
  src/main/java/com/vistance/bo/routeb/
    ExporterConfig.java
    ReadOnlyPolicy.java
    RequiredInputException.java
    RouteBExporter.java
    RouteBMain.java
    SdkClasspathValidator.java
    SecretRedactor.java
    StableJson.java
  src/test/java/com/vistance/bo/routeb/
    RouteBContractTest.java
```

`RouteBMain manifest` is local-only and never connects to CMS. `RouteBMain export` fails with `REQUIRED_INPUT`. `RouteBMain validate-classpath` checks confirmed SAP class names only after a remote SDK classpath is supplied.

## 6. SDK Dependencies

Confirmed from repository SDK evidence/Javadocs:

- SAP Semantic Layer packages under `com.sap.sl.sdk.framework`, `com.sap.sl.sdk.framework.cms`, `com.sap.sl.sdk.authoring.cms`, `businesslayer`, `datafoundation`, and `connection`.
- Classic Enterprise SDK types `com.crystaldecisions.sdk.framework.IEnterpriseSession` and `CrystalEnterprise` for the documented CMS session handoff.

Unresolved:

- Complete transitive SDK classpath.
- Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
- Confirmed method or service returning `DataSource`.
- Confirmed method or service returning `DataFoundation`.
- CMS details and permissions only if CMS retrieval is selected.
- Remote working and export directories.

## 7. JSON Contracts

All seven files under `config/schemas/route_b/` use `route_b.sdk.v1` and require:

- `source_system`
- `extraction_method`
- `evidence_level`
- `verification_status`

Contracts cover Business Layer, Data Foundation, joins, connections, contexts, and lineage edges. HANA fields in the lineage contract are constrained to `UNKNOWN` during this milestone.

## 8. Security Controls

- No credentials are modeled in Java configuration.
- Secret-like values are redacted by `SecretRedactor`.
- Read-only policy rejects create/update/delete/publish/save/change/convert/modify/set operations.
- CMS logon is not called.
- Export boundary fails closed with typed `RequiredInputException`.
- `saveForAllUsers=false` is the configured design requirement for future retrieval.
- SDK JARs, classpath files, target output, and generated Route B exports are ignored.
- Connection passwords are never requested or serialized.

## 9. Tests and Results

Passed:

- Focused Route B Python contract tests: **6 passed**.
- Full Python suite: **126 passed**.
- Ruff: **clean**.
- Mypy strict: **38 source files, no issues**.
- PowerShell parser checks: all 3 scripts parsed successfully.
- Route B JSON schema parsing: all 7 schemas parsed successfully.

Not run because unavailable locally:

- `javac`: unavailable.
- `java`: unavailable.
- Maven: unavailable.
- SAP SDK runtime/classpath tests: intentionally not attempted.
- CMS connectivity: intentionally not attempted.

## 10. Exact Remote Commands

Run on the Windows RDP machine after setting paths and supplying the SDK classpath outside source control:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
Set-Location C:\path\to\bo-universe-semantic-extractor
$env:JAVA_HOME = 'C:\path\to\sap-supported-jvm'
$env:SAP_SDK_CLASSPATH = 'C:\path\to\sap\sdk\*;C:\path\to\enterprise\sdk\*'
.\scripts\validate-route-b.ps1
.\scripts\run-route-b.ps1 -Command manifest
.\scripts\run-route-b.ps1 -Command validate-classpath -SdkClasspath $env:SAP_SDK_CLASSPATH
```

Do not run `-Command export` until Milestone 2 retrieval/loading APIs are confirmed.

## 11. Exact Local Commands

```powershell
Set-Location C:\path\to\bo-universe-semantic-extractor
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = 'src'
python -m pytest -q
python -m ruff check .
python -m mypy src
Get-ChildItem config\schemas\route_b -File | ForEach-Object { Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null }
```

## 12. Required Inputs for Milestone 2

- Complete transitive SDK classpath.
- Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
- Confirmed method or service returning `DataSource`.
- Confirmed method or service returning `DataFoundation`.
- CMS details and permissions only if CMS retrieval is selected.
- Remote working and export directories.

Milestone 2 must begin only after these inputs are supplied. No HANA work is part of this report.
