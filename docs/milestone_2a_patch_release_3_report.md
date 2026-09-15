# Milestone 2A Patch Release 3 Report

## Fix

The runner no longer passes the full generated runtime classpath to `javap`. Candidate classes
are discovered per JAR, and each `javap` invocation receives only the single JAR containing that
class:

```powershell
javap.exe -classpath $target.jar $target.class
```

This removes Windows command-line length dependence while preserving deterministic candidate
ordering and the existing SDK inventory/capability-validation flow. The reflection-only Java
probe uses a temporary Java argument file for its full classpath.

## Package

The packaged runner under `remote-sdk-extractor/dist/milestone-2a/` was regenerated. No SAP JARs,
credentials, universe files, CMS sessions, runtime output, or HANA artifacts are included.

## Validation

- Focused Route B contract tests: **14 passed**.
- Full Python suite: **134 passed**.
- Ruff: clean.
- Mypy: clean across 38 source files.
- PowerShell syntax: passed.
- JSON parsing: passed.
- Package portability/prohibited-artifact checks: passed.
- SAP SDK/JVM runtime discovery: not executed locally.
- CMS and HANA: not contacted.

## Remaining Boundary

Remote execution still requires the SAP-supported JVM, complete transitive SDK classpath, and
Milestone 2A path inputs. Milestone 2B has not started.
