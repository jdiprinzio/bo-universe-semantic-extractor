# Milestone 2B Classpath Fix Report

## Root cause

`NoClassDefFoundError` indicated missing transitive dependencies, not missing classes: the `URLClassLoader` was built only from the 152 filtered JARs, but SAP semantic layer classes (e.g. `DataSourceElement extends org.eclipse.emf.ecore.EObject`) reference types in the excluded 1,820 JARs. Separately, `classesLoaded` was incremented immediately after `Class.forName` succeeded but before `getDeclaredMethods()` ran; a lazy `NoClassDefFoundError` during method reflection then hit the *same* catch blocks and incremented `classesSkipped` too, double-counting classes.

## Fix

The classloader now resolves against **all** discovered JARs; class enumeration (inspection scope) remains limited to the 152 provider-family JARs for performance. `classesLoaded++` moved to after the full per-class method loop completes, so `classes_loaded + classes_skipped == classes_enumerated` exactly. Added `verifyTargetClasses`, run before the full sweep against the full classpath, writing `target_class_load_verification.json` and failing fast with `TARGET_CLASSES_UNLOADABLE` if any of the 7 target classes can't resolve. `provider_discovery_findings.json` now caps individual records at 100 and adds `by_error_type`/`by_jar`/`by_package_prefix` aggregates plus `total_failure_count`. `NoClassDefFoundError` failures capture the missing dependency's dotted name from the exception message.

## Validation

- Full suite: **152 passed**.
- Import validator + classpath-fix contracts: **7 passed**.
- Ruff: **All checks passed**.
- Mypy: **7 errors**, all pre-existing/unrelated to Route B.

Read-only behavior, no CMS/SDK instantiation, no SAP JARs in package, assignability matching, and `related_return_type_inventory.json` are all preserved.
