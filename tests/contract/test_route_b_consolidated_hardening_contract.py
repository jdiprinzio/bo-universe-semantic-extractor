"""Contracts for the consolidated Milestone 2B hardening release."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
SIMULATOR = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "simulate-provider-discovery.ps1"
HANDOFF = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "provider-scan-handoff.ps1"
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
M2A_PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "Milestone2aProbe.java"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_line_handoff_replaces_java_json_inputs() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    m2a = M2A_PROBE.read_text(encoding="utf-8")
    assert "included_jars.txt" in runner and "included_jars.json" in runner
    assert "Files.readAllLines" in probe
    assert "confirmed_classes.txt" in runner and "confirmed_classes.txt" in m2a
    assert "ConvertFrom-Json" not in probe
    assert "JsonTextParser" not in m2a


def test_preflight_and_failure_diagnostics_are_present() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    handoff = HANDOFF.read_text(encoding="utf-8")
    for marker in ("HANDOFF_PREFLIGHT included_jars_lines=", "HANDOFF_PREFLIGHT confirmed_classes_lines=", "HANDOFF_PREFLIGHT java_tools_present=", "HANDOFF_PREFLIGHT probe_source_present=", "HANDOFF_PREFLIGHT_FAILURE"):
        assert marker in handoff
    assert "failure_diagnostics.json" in runner
    assert "Write-FailureDiagnostics" in runner.rsplit("}catch{", 1)[1]
    for field in ("phase=", "error_code=", "handoff_files", "probe_scope", "java_tools", "last_progress_lines"):
        assert field in runner


def test_collection_boundaries_are_explicit_arrays() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "@(Receive-Job" in runner
    assert "@($scan|Where-Object" in runner
    assert "@(@(Get-Content" in runner
    assert "$handoffJarLines=@(" in HANDOFF.read_text(encoding="utf-8")


def test_simulation_harness_creates_synthetic_jars_and_round_trips_handoffs() -> None:
    simulator = SIMULATOR.read_text(encoding="utf-8")
    assert "New-SyntheticJar" in simulator
    assert "ZipArchiveMode]::Create" in simulator
    assert "Invoke-ProviderScanHandoff" in simulator
    assert "IncludedJarsTextPath" in simulator
    assert "ConfirmedClassesPath" in simulator
    assert "SIMULATION_HANDOFF_FAILURE" in simulator
    assert "SIMULATION_PASSED" in simulator


def test_prior_runtime_safety_and_probe_guards_remain() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    probe = PROBE.read_text(encoding="utf-8")
    assert "Stop-Job -Job $job -ErrorAction SilentlyContinue" in runner
    assert "Remove-Job -Job $job -Force" in runner
    assert "PROBE_SCOPE_MISMATCH" in runner or "PROBE_SCOPE_MISMATCH" in probe
    assert "new URLClassLoader" in probe
    assert "isAssignableFrom(returnType)" in probe
    assert "catch (NoClassDefFoundError error)" in probe
    assert "PROBE_SCOPE HEARTBEAT" in probe
    assert "provider_scan_exclusions.json" in HANDOFF.read_text(encoding="utf-8")


def test_package_is_source_only_and_portable() -> None:
    forbidden = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden for path in files)
    assert not any("GITHub" in path.read_text(encoding="utf-8", errors="ignore") for path in files)
    assert not any("password=" in path.read_text(encoding="utf-8", errors="ignore").lower() for path in files)
