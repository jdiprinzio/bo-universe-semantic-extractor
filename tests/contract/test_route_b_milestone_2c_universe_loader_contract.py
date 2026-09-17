"""Contracts for Milestone 2C: Universe Loader Discovery.

Reuses the Milestone 2B architecture exactly: Java owns discovery, filtering,
reflection, and logging; PowerShell only compiles and launches.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-universe-loader-discovery.ps1"
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "UniverseLoaderProbe.java"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2c-universe-loader-discovery"


def test_runner_compiles_then_launches_with_no_handoff_files() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "Start-Job" not in runner
    assert "ConvertFrom-Json" not in runner
    assert "'JAVA_COMPILATION_FAILURE'" in runner
    assert "-Xmx4g" in runner
    assert "com.vistance.bo.routeb.UniverseLoaderProbe" in runner


def test_probe_classloader_covers_all_jars_with_scoped_inspection() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "classpathUrls[i] = jars.get(i)" in probe
    assert "new URLClassLoader(classpathUrls" in probe
    assert "included.size()" in probe


def test_probe_uses_assignability_for_universe_and_datafoundationfile() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "universeType.isAssignableFrom(returnType)" in probe
    assert "dataFoundationFileType.isAssignableFrom(returnType) || acceptsType(method, dataFoundationFileType)" in probe


def test_probe_classifies_signatures_into_expected_categories() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    for category in ("FILE_BASED", "CMS_BASED", "WORKSPACE", "FACTORY", "UNKNOWN"):
        assert f'"{category}"' in probe


def test_target_verification_includes_required_classes_and_fails_fast() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    for target in (
        "com.businessobjects.mds.universe.Universe",
        "com.businessobjects.mds.repository.DataFoundationFile",
        "com.businessobjects.mds.services.helpers.UniverseHelper",
    ):
        assert target in probe
    assert "TARGET_CLASSES_UNLOADABLE" in probe
    assert "target_class_load_verification.json" in probe


def test_output_directory_and_required_files() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert 'resolve("universe_loader_discovery")' in probe
    for output_file in (
        "universe_providers.json",
        "file_based_loaders.json",
        "datafoundation_file_methods.json",
        "target_class_load_verification.json",
        "execution_report.md",
        "discovery_progress.log",
    ):
        assert output_file in probe


def test_failures_capped_with_aggregates() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "MAX_SAMPLE_FAILURES = 100" in probe
    assert "byErrorType" in probe and "byJar" in probe and "byPackagePrefix" in probe


def test_no_cms_no_instantiation_and_package_portability() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "CrystalEnterprise" not in probe
    assert "new Universe(" not in probe
    forbidden = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden for path in files)
    assert (PACKAGE / "run-universe-loader-discovery.ps1").exists()
    assert (PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "UniverseLoaderProbe.java").exists()
