"""Contracts for Milestone 2B Patch Release 3."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_candidate_selection_does_not_filter_class_or_package_names() -> None:
    script = SOURCE_RUNNER.read_text(encoding="utf-8")
    scan = script.split("$scan=Phase 'PROVIDER_SCAN'", 1)[1].split("$scanResult", 1)[0]
    assert "providerPrefixes" not in scan
    assert "System.IO.Compression.ZipFile" not in scan
    assert "includedJars" in scan


def test_probe_enumerates_all_classes_and_inspects_declared_methods() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "getDeclaredMethods()" in probe
    assert "classesEnumerated = classNames.size()" in probe
    assert "methodsInspected++" in probe
    assert "related_return_type_inventory.json" in probe


def test_probe_uses_assignability_for_provider_return_types() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "isAssignableFrom(returnType)" in probe
    assert "returnType.getName().equals" not in probe
    assert "DataSource" in probe and "DataFoundation" in probe


def test_probe_tolerates_required_class_load_failures() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    for exception_name in (
        "ClassNotFoundException",
        "NoClassDefFoundError",
        "ExceptionInInitializerError",
        "UnsatisfiedLinkError",
    ):
        assert f"catch ({exception_name} error)" in probe
    assert "classesSkipped++" in probe


def test_probe_scope_counters_are_emitted_and_logged() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    script = SOURCE_RUNNER.read_text(encoding="utf-8")
    for counter in ("jars", "classes_enumerated", "classes_loaded", "classes_skipped", "methods_inspected"):
        assert f'"{counter}"' in probe
        assert f"PROBE_SCOPE {counter}=" in script


def test_probe_fails_closed_on_implausibly_small_enumeration() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "classesEnumerated < jars.size() * 10" in probe
    assert "PROBE_SCOPE_MISMATCH" in probe


def test_patch_3_package_is_portable_and_contains_probe() -> None:
    forbidden_extensions = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden_extensions for path in files)
    assert (PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java").exists()
    assert (PACKAGE / "run-provider-discovery.ps1").exists()
