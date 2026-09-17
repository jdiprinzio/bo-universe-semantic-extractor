# Milestone 2B Provider Discovery Specification

## Intent
Discover SDK methods that may provide Business Layer `DataSource` or Data Foundation `DataFoundation` objects on the installed BusinessObjects runtime.

## Inputs
- SAP BusinessObjects installation and IDT plugin directories supplied externally.
- SAP-supported JVM `bin` directory supplied externally.
- A generated candidate registry containing candidate class names and source JAR paths.
- The confirmed runtime capability registry.

## Outputs
- Candidate class registry.
- `javap` method inventory with source JAR attribution.
- DataSource provider matches.
- DataFoundation provider matches.
- Local-resource loader candidates.
- Findings for classes that cannot be loaded due to missing transitive dependencies.
- Execution progress, report, and SHA-256 manifest.

## Constraints
- Reflection-only class loading with initialization disabled.
- No SDK object instantiation.
- No CMS logon, repository retrieval, universe loading, HANA connection, or write operation.
- The process exit code is the failure condition for native tools.
- External SAP paths are never copied into the repository package.
- Java source remains Java 8 compatible.

## Matching rules
- A provider match requires an exact return type of the confirmed runtime `DataSource` or `DataFoundation` class.
- Candidate class discovery is limited to configured repository, workspace, datasource-info, and MDS service/universe/toolkit namespaces.
- Methods whose names indicate create, save, publish, delete, update, set, or convert are excluded from local-loader recommendations but remain visible in provider inventories.

## Edge cases
- Missing transitive runtime classes are reported per candidate without aborting the complete scan.
- Empty candidate output is an explicit failure because it indicates an inventory or namespace problem.
- JVM/compiler diagnostics on stderr are retained as diagnostics and do not fail successful native commands.
