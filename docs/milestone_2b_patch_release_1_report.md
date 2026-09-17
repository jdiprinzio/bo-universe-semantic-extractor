# Milestone 2B Patch Release 1 Report

## Changes

- Removed the unsupported `Stop-Job -Force` invocation. Timeout cancellation now uses Windows PowerShell 5.1-compatible `Stop-Job -Job $job`; `Remove-Job -Force` remains for cleanup.
- Replaced per-JAR `jar.exe tf` provider scanning with in-process `System.IO.Compression.ZipFile` enumeration.
- Restricted scanning to provider-oriented runtime JAR families and the confirmed CE SDK JAR names. Every excluded JAR is recorded at runtime in `provider_scan_exclusions.json` with an explanation.
- Added `PROVIDER_SCAN HEARTBEAT scanned=N of M` progress records.
- Raised the configurable default phase timeout from 900 to 3600 seconds.
- Regenerated the source-only portable package.

## Safety

The package remains read-only. It does not connect to CMS or HANA, instantiate SDK objects, copy SAP JARs, load universe resources, or invoke write APIs. Java source remains Java 8-compatible.

## Validation

- Windows PowerShell parser: passed.
- Milestone 2B Patch Release 1 contract tests: passed.
- Existing Route B contract tests: passed.
- Package artifact audit: passed; no SAP JARs or universe artifacts included.

The remote provider discovery run should be repeated with the regenerated package. This patch does not start Milestone 2C or perform provider loading.
