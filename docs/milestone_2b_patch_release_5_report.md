# Milestone 2B Patch Release 5 Report

## Parser Defect and Fix

`included_jars.json` was parsed by splitting on an object whose first property had to be `file_name`. PowerShell emits pretty-printed JSON with flexible whitespace and property order, so the parser returned zero JARs. A shared token-aware JSON helper now reads object arrays and string properties with whitespace/newline tolerance, escaped Windows path decoding, property-order independence, and additional-property tolerance. The capability registry parser uses the same helper.

## Diagnostics

- Empty included-JAR results now fail with `INCLUDED_JARS_PARSE_FAILURE`, including file size, searched property, and the first 200 characters.
- PowerShell round-trips `included_jars.json`, compares the entry count to the filtered count, and fails with `INCLUDED_JARS_WRITE_MISMATCH` before Java.
- The handoff logs `INCLUDED_JARS_WRITTEN count=N bytes=N path=...`.

## Validation

Source and packaged PowerShell parsing passed. The source-only package was regenerated. Focused Route B contracts passed after updating the legacy capability-parser contract. Package audit found no SAP JARs, universe artifacts, or credential material. No CMS or HANA access was performed.
