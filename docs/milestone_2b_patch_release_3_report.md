# Milestone 2B Patch Release 3 Report

## Root Cause

Patch Release 2 filtered class entries by provider-looking package names before the Java probe ran. The probe then used exact return-type equality, so unrelated classes such as `IScope` could survive while confirmed provider methods were discarded.

## Changes

- Provider JAR filtering remains bounded to the required runtime families and CE SDK JAR names.
- Every class entry in every included JAR is now enumerated; only module/package descriptors are omitted.
- Java reflection loads each class without initialization and inspects declared methods.
- Provider matches use `Class.isAssignableFrom`, supporting subtypes and implementations.
- Required class-load/linkage failures are recorded and skipped.
- Related return types containing `DataSource`, `DataFoundation`, `BusinessLayer`, `Universe`, `Workspace`, or `Repository` are written to `related_return_type_inventory.json`.
- Probe scope counters are emitted in all probe JSON documents and logged in `discovery_progress.log`.
- Enumeration fails closed when the class count is smaller than the included-JAR count.
- The source-only portable package was regenerated.

## Validation

- Source and packaged PowerShell parsing passed.
- Patch Release 1, Patch Release 2, Patch Release 3, and existing Route B contracts: `35 passed`.
- Directory package audit found no SAP JARs, universe artifacts, or credential material.
- No CMS or HANA connections were made.
