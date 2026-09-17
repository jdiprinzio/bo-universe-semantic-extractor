"""Contracts for the Milestone 2B Classpath Fix.

The classloader must resolve against every discovered JAR (transitive dependencies),
while inspection remains scoped to the smaller provider-family JAR set. Counters must
reconcile, findings must be capped with aggregates, and a target-class verification
phase must fail fast before the full sweep.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"


def test_classloader_resolves_against_all_discovered_jars_not_the_filtered_subset() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "classpathUrls[i] = jars.get(i)" in probe
    assert "new URLClassLoader(classpathUrls" in probe
    assert "urls[i] = included.get(i)" not in probe


def test_class_load_counter_only_counts_full_success() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    scan = probe.split("for (int index = 0; index < classNames.size(); index++) {", 1)[1].split("Map<String, Object> scope = scopeCounters", 1)[0]
    load_index = scan.index("Class.forName(className, false, loader)")
    counter_index = scan.index("classesLoaded++;")
    catch_index = scan.index("catch (ClassNotFoundException error)")
    assert load_index < counter_index < catch_index


def test_target_class_verification_runs_before_full_sweep_and_fails_fast() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    verify_index = probe.index("verifyTargetClasses(loader, output)")
    sweep_index = probe.index("for (int jarIndex = 0; jarIndex < included.size(); jarIndex++) {")
    assert verify_index < sweep_index
    assert "TARGET_CLASSES_UNLOADABLE" in probe
    assert "target_class_load_verification.json" in probe
    for target in (
        "com.sap.sl.datasource.DataSource",
        "com.sap.sl.datasource.DataSourceElement",
        "com.sap.sl.datasource.BusinessLayer",
        "com.businessobjects.mds.datafoundation.DataFoundation",
        "com.businessobjects.mds.datafoundation.Join",
        "com.sap.sl.repository.service.RepositoryService",
        "com.sap.sl.workspace.service.WorkspaceManagerService",
    ):
        assert target in probe


def test_findings_are_capped_with_aggregates() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "MAX_SAMPLE_FAILURES = 100" in probe
    assert "by_error_type" in probe
    assert "by_jar" in probe
    assert "by_package_prefix" in probe
    assert "total_failure_count" in probe


def test_no_class_def_found_error_captures_missing_dependency_name() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "missingDependencyName" in probe
    assert "instanceof NoClassDefFoundError" in probe
    assert "replace('/', '.')" in probe
