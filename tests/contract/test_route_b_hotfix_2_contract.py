"""Contracts for Milestone 2B Hotfix 2: handoff ordering and legacy gate removal."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
HANDOFF = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "provider-scan-handoff.ps1"
SIMULATOR = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "simulate-provider-discovery.ps1"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_legacy_json_roundtrip_validation_is_removed() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    assert "INCLUDED_JARS_WRITE_MISMATCH" not in handoff
    assert "INCLUDED_JARS_WRITE_MISMATCH" not in runner
    assert "ConvertFrom-Json" not in handoff.split("Step 4", 1)[0].replace(
        "# Evidence only; never parsed, counted, or used to gate execution.", ""
    ) or "Get-Content -LiteralPath $includedJarsJsonPath" not in handoff


def test_included_jars_json_is_evidence_only() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    assert "included_jars.json" in handoff
    assert "Get-Content -LiteralPath $includedJarsJsonPath" not in handoff
    assert "never read back or used to gate execution" in handoff


def test_handoff_ordering_matches_required_sequence() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    included_write = handoff.index("Write-Utf8NoBomLines $includedJarsTextPath")
    confirmed_write = handoff.index("Write-Utf8NoBomLines $confirmedClassesPath")
    preflight_log = handoff.index('HANDOFF_PREFLIGHT included_jars_lines=')
    mismatch_check = handoff.index("INCLUDED_JARS_LINE_COUNT_MISMATCH")
    assert included_write < confirmed_write < preflight_log < mismatch_check

    runner = RUNNER.read_text(encoding="utf-8")
    filtered_log = runner.index("PROVIDER_SCAN FILTERED total=")
    handoff_call = runner.index("Invoke-ProviderScanHandoff")
    probe_invocation = runner.index("ProviderDiscoveryProbe $using:includedJarsTextPath")
    assert filtered_log < handoff_call < probe_invocation


def test_included_jars_line_count_mismatch_is_distinct_code() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    assert "INCLUDED_JARS_LINE_COUNT_MISMATCH" in handoff
    assert "Get-Content -LiteralPath $includedJarsTextPath" in handoff


def test_failure_diagnostics_covers_preflight_failures() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    catch_block = runner.rsplit("}catch{", 1)[1]
    assert "Write-FailureDiagnostics" in catch_block
    assert "Invoke-ProviderScanHandoff" in runner.rsplit("}catch{", 1)[0]


def test_simulation_produces_at_least_152_included_jars() -> None:
    simulator = SIMULATOR.read_text(encoding="utf-8")
    assert "$ProviderJarCount = 152" in simulator
    assert "SIMULATION_SCALE_FAILURE" in simulator
    assert "Invoke-ProviderScanHandoff" in simulator


def test_package_contains_shared_handoff_module() -> None:
    assert (PACKAGE / "provider-scan-handoff.ps1").exists()
    packaged_runner = (PACKAGE / "run-provider-discovery.ps1").read_text(encoding="utf-8")
    assert "provider-scan-handoff.ps1" in packaged_runner
