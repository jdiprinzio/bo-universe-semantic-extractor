"""Contracts for Milestone 2B Patch Release 5 JSON handoff parsing."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
PARSER = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "JsonTextParser.java"
CAPABILITY_PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "Milestone2aProbe.java"
RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "included_jars_powershell_convertto_json.json"


def test_powershell_fixture_contains_all_entries_and_escaped_windows_paths() -> None:
    entries = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(entries) == 2
    assert [entry["absolute_path"] for entry in entries] == [
        r"E:\Program Files (x86)\SAP BusinessObjects\win64_x64\cecore.jar",
        r"E:\Program Files (x86)\SAP BusinessObjects\win64_x64\com.sap.sl.sdk.jar",
    ]
    assert all('"absolute_path":  "' in line or '"absolute_path":  "' in FIXTURE.read_text(encoding="utf-8") for line in FIXTURE.read_text(encoding="utf-8").splitlines() if "absolute_path" in line)


def test_included_jars_parser_is_whitespace_tolerant_and_order_independent() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "Files.readAllLines" in probe
    assert "line.trim()" in probe
    assert "startsWith(\"#\")" in probe
    assert "JsonTextParser" not in probe


def test_parser_reports_required_empty_input_diagnostics() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "INCLUDED_JARS_PARSE_FAILURE" in probe
    assert "Files.size(path)" in probe
    assert "property=absolute_path" in probe
    assert "preview(path)" in probe


def test_capability_parser_uses_same_tolerant_property_parser() -> None:
    capability_probe = CAPABILITY_PROBE.read_text(encoding="utf-8")
    assert "Files.readAllLines" in capability_probe
    assert "JsonTextParser" not in capability_probe
    assert "confirmed_classes.txt" in capability_probe


def test_runner_validates_and_logs_included_jars_before_probe() -> None:
    handoff = (RUNNER.parent / "provider-scan-handoff.ps1").read_text(encoding="utf-8")
    assert "ConvertFrom-Json" not in handoff
    assert "INCLUDED_JARS_WRITE_MISMATCH" not in handoff
    assert "INCLUDED_JARS_LINE_COUNT_MISMATCH" in handoff
    assert "INCLUDED_JARS_WRITTEN path=" in handoff
    assert handoff.index("INCLUDED_JARS_WRITTEN path=") < handoff.index("INCLUDED_JARS_LINE_COUNT_MISMATCH")


def test_package_behavior_boundaries_remain_present() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "URLClassLoader" in probe
    assert "isAssignableFrom(returnType)" in probe
    assert "Class.forName(className, false, loader)" in probe
    for exception_name in ("NoClassDefFoundError", "ExceptionInInitializerError", "UnsatisfiedLinkError"):
        assert f"catch ({exception_name} error)" in probe
