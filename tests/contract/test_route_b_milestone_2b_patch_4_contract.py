"""Contracts for Milestone 2B Patch Release 4."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_probe_receives_full_included_jar_list_and_candidates_are_output_only() -> None:
    script = SOURCE_RUNNER.read_text(encoding="utf-8")
    assert "included_jars.json" in script
    assert "ProviderDiscoveryProbe $using:includedJarsTextPath" in script
    assert "provider_candidates.json')" not in script.split("$scanResult.Exclusions", 1)[0]
    assert "IncludedJars" in script


def test_powershell_filters_only_jars() -> None:
    script = SOURCE_RUNNER.read_text(encoding="utf-8")
    scan = script.split("$scan=Phase 'PROVIDER_SCAN'", 1)[1].split("$scanResult", 1)[0]
    assert "OpenRead" not in scan
    assert ".class" not in scan
    assert "IncludedJars" in scan
    assert "providerJarPrefixes" in scan


def test_probe_enumerates_each_included_jar_and_uses_url_class_loader() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "new URLClassLoader" in probe
    assert "new JarFile(jar.path)" in probe
    assert "archive.entries()" in probe
    assert "endsWith(\".class\")" in probe
    assert "replace('/', '.')" in probe
    assert "Class.forName(className, false, loader)" in probe
    assert "getDeclaredMethods()" in probe
    assert "isAssignableFrom(returnType)" in probe


def test_probe_scope_matches_filtered_count_and_has_distinct_guard() -> None:
    script = SOURCE_RUNNER.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    assert "findings.scope.jars" in script
    assert "scanResult.Included" in script
    assert "PROBE_SCOPE_MISMATCH" in script
    assert "findings.scope.jars -ne" in script
    assert "classesEnumerated < jars.size() * 10" in probe
    assert "scopeFailure" in probe


def test_probe_scope_heartbeat_and_candidate_output_contract() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "PROBE_SCOPE HEARTBEAT jar=" in probe
    assert "provider_candidates.json" in probe
    assert "identified" in probe
    assert "included_jars.txt" in probe


def test_patch_4_package_is_portable() -> None:
    forbidden = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden for path in files)
    assert (PACKAGE / "run-provider-discovery.ps1").exists()
    assert (PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java").exists()
