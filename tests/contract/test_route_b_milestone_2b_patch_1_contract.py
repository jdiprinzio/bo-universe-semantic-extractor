"""Contracts for Milestone 2B Patch Release 1."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_packaged_scripts_do_not_use_unsupported_stop_job_force_parameter() -> None:
    for path in PACKAGE.rglob("*.ps1"):
        text = path.read_text(encoding="utf-8")
        if path.name not in ("invoke-informational-native.ps1", "simulate-provider-discovery.ps1", "provider-scan-handoff.ps1"):
            assert "Stop-Job" in text
        assert "Stop-Job $job -Force" not in text
        assert "Stop-Job -Job $job -Force" not in text


def test_provider_scan_uses_in_process_zip_enumeration() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    scan = text.split("$scan=Phase 'PROVIDER_SCAN'", 1)[1].split("$scan.Candidates", 1)[0]
    assert "included_jars.json" in text
    assert "provider_candidates.json" not in scan
    assert "jar.exe" not in scan


def test_provider_scan_filters_jars_and_records_exclusions() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    for prefix in (
        "com.sap.sl.",
        "com.businessobjects.mds.",
        "com.businessobjects.dsl.",
        "com.businessobjects.sdk.",
        "com.businessobjects.boesdk",
    ):
        assert prefix in text
    for jar_name in ("cesdk.jar", "cecore.jar", "celib.jar", "cesession.jar"):
        assert jar_name in text
    for irrelevant in ("eclipse", "localization", "jetty", "batik", "lucene", "poi", "axis2", "visualization", "help", "language"):
        assert irrelevant in text
    handoff_text = (SOURCE_RUNNER.parent / "provider-scan-handoff.ps1").read_text(encoding="utf-8")
    assert "provider_scan_exclusions.json" in handoff_text
    assert "does not match a provider runtime family" in text


def test_provider_scan_emits_progress_counters_and_uses_one_hour_default() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    assert "[int]$PhaseTimeoutSeconds = 3600" in text
    assert "PROVIDER_SCAN HEARTBEAT scanned=$scanned of $total" in text
    assert "Stop-Job -Job $job -ErrorAction SilentlyContinue" in text
    assert "Remove-Job -Job $job -Force" in text


def test_milestone_2b_package_is_portable_and_contains_required_sources() -> None:
    forbidden = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden for path in files)
    assert not any("GITHub" in path.read_text(encoding="utf-8", errors="ignore") for path in files)
    assert (PACKAGE / "run-provider-discovery.ps1").exists()
    assert (PACKAGE / "provider_scan_exclusions.json").exists() is False
    assert (PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java").exists()
