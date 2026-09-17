"""Contracts for Milestone 2B Patch Release 2."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_provider_scan_has_single_parent_log_writer() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    scan = text.split("$scan=Phase 'PROVIDER_SCAN'", 1)[1].split("$scanResult", 1)[0]
    assert "Add-Content" not in scan
    assert "kind='heartbeat'" in scan
    assert "Receive-Job -Job $job" in text
    assert "PhaseLog $item.message" in text


def test_provider_scan_heartbeat_is_time_based() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    scan = text.split("$scan=Phase 'PROVIDER_SCAN'", 1)[1].split("$scanResult", 1)[0]
    assert "AddSeconds(30)" in scan
    assert "DateTime]::UtcNow -ge $nextHeartbeat" in scan
    assert "PROVIDER_SCAN HEARTBEAT scanned=$scanned of $total" in scan
    assert scan.count("kind='heartbeat'") == 1


def test_provider_filtering_logs_reduction_and_writes_exclusions() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    assert "PROVIDER_SCAN FILTERED total=$($scanResult.Total) included=$($scanResult.Included) excluded=$($scanResult.Excluded)" in text
    handoff_text = (SOURCE_RUNNER.parent / "provider-scan-handoff.ps1").read_text(encoding="utf-8")
    assert "provider_scan_exclusions.json" in handoff_text
    assert "PROVIDER_SCAN_FILTER_FAILURE" in text
    assert "$scanResult.Included -ge $scanResult.Total" in text


def test_provider_filtering_retains_required_runtime_families() -> None:
    text = SOURCE_RUNNER.read_text(encoding="utf-8")
    for family in (
        "com.sap.sl.",
        "com.businessobjects.mds.",
        "com.businessobjects.dsl.",
        "com.businessobjects.sdk.",
        "com.businessobjects.boesdk",
        "cesdk.jar",
        "cecore.jar",
        "celib.jar",
        "cesession.jar",
    ):
        assert family in text
    for excluded in ("eclipse", "jetty", "batik", "lucene", "poi", "axis2", "visualization", "help", "localization"):
        assert excluded in text


def test_regenerated_package_is_portable() -> None:
    forbidden_extensions = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden_extensions for path in files)
    forbidden_credential_patterns = ("password=", "client_secret=", "authorization: bearer")
    assert not any(
        pattern in path.read_text(encoding="utf-8", errors="ignore").lower()
        for path in files
        for pattern in forbidden_credential_patterns
    )
    assert (PACKAGE / "run-provider-discovery.ps1").exists()
