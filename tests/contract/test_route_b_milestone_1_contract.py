"""Local contract tests for ROUTE_B_SDK Milestone 1.

These tests intentionally do not require SAP JARs, a Java runtime, or CMS connectivity. They
validate repository-owned schemas, configuration, source-level safety markers, and the explicit
REQUIRED_INPUT boundary for the remote exporter.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "config" / "schemas" / "route_b"
JAVA_DIR = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb"
M2A_SCRIPT = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-milestone-2a.ps1"
M2A_PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2a"
M2A_NATIVE_HELPER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "invoke-informational-native.ps1"

EXPECTED_SCHEMAS = {
    "business_layer.schema.json",
    "common.schema.json",
    "connection_metadata.schema.json",
    "context_metadata.schema.json",
    "data_foundation.schema.json",
    "join_metadata.schema.json",
    "lineage_edges.schema.json",
}


def test_route_b_schema_inventory_is_complete_and_valid_json() -> None:
    assert {path.name for path in SCHEMA_DIR.glob("*.json")} == EXPECTED_SCHEMAS
    for path in SCHEMA_DIR.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert document["$id"].endswith(path.name)


def test_route_b_contracts_require_common_evidence_fields() -> None:
    for path in SCHEMA_DIR.glob("*.schema.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "common.schema.json":
            assert set(document["required"]) >= {
                "source_system",
                "extraction_method",
                "evidence_level",
                "verification_status",
            }
        else:
            assert {"$ref": "common.schema.json"} in document["allOf"]


def test_lineage_contract_forbids_fabricated_hana_values() -> None:
    document = json.loads((SCHEMA_DIR / "lineage_edges.schema.json").read_text(encoding="utf-8"))
    properties = document["properties"]["items"]["items"]["properties"]
    assert properties["physical_hana_object"]["const"] == "UNKNOWN"
    assert properties["physical_hana_column"]["const"] == "UNKNOWN"


def test_universe_config_is_shared_and_non_secret() -> None:
    profile = yaml.safe_load(
        (REPO_ROOT / "config" / "universes" / "dm_invoice_data_mart.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert profile["universe"]["slug"] == "dm_invoice_data_mart"
    assert profile["route_b"]["enabled"] is True
    assert profile["route_b"]["save_for_all_users"] is False
    assert "password" not in json.dumps(profile).lower()


def test_java_skeleton_has_read_only_and_required_input_boundaries() -> None:
    read_only = (JAVA_DIR / "ReadOnlyPolicy.java").read_text(encoding="utf-8")
    exporter = (JAVA_DIR / "RouteBExporter.java").read_text(encoding="utf-8")
    assert "publish" in read_only and "save" in read_only and "create" in read_only
    assert "RequiredInputException" in exporter
    assert "cms_connection_attempted" in exporter
    assert "CMS connection" in exporter


def test_java_skeleton_contains_no_live_cms_logon_or_write_calls() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in JAVA_DIR.glob("*.java"))
    assert "CrystalEnterprise.getSessionMgr().logon" not in source
    assert ".publish(" not in source
    assert ".save(" not in source
    assert ".create(" not in source


def test_milestone_2a_package_contains_no_sap_jars_or_universe_artifacts() -> None:
    forbidden_suffixes = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    package_files = [path for path in M2A_PACKAGE.rglob("*") if path.is_file()]
    assert all(path.suffix.lower() not in forbidden_suffixes for path in package_files)
    assert not any("password" in path.read_text(encoding="utf-8", errors="ignore").lower() for path in package_files if path.suffix in {".json", ".md", ".ps1"})


def test_milestone_2a_script_externalizes_runtime_paths_and_uses_capability_registry() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    for parameter in (
        "$SapInstallRoot",
        "$IdtPluginDirectory",
        "$SapJvmBinDirectory",
        "$LocalIdtProjectDirectory",
        "$WorkingDirectory",
        "$OutputDirectory",
    ):
        assert parameter in script
    assert "$CapabilityRegistry" in script
    assert "..\\" not in script
    assert "Join-Path $script:PackageRoot 'config\\confirmed_sdk_capabilities.json'" in script
    assert "Sort-Object FullName" in script
    assert "Get-FileHash" in script


def test_milestone_2a_package_runner_is_self_contained() -> None:
    packaged_scripts = list(M2A_PACKAGE.rglob("*.ps1"))
    assert packaged_scripts
    for script_path in packaged_scripts:
        script = script_path.read_text(encoding="utf-8")
        assert "..\\" not in script, script_path
        assert "GITHub" not in script, script_path
        assert "repository" not in script.lower(), script_path
    script = (M2A_PACKAGE / "run-milestone-2a.ps1").read_text(encoding="utf-8")
    assert "Join-Path $script:PackageRoot 'config\\confirmed_sdk_capabilities.json'" in script
    assert "config\\confirmed_sdk_capabilities.json" in script
    assert (M2A_PACKAGE / "config" / "confirmed_sdk_capabilities.json").exists()
    assert (M2A_PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "Milestone2aProbe.java").exists()


def test_packaged_runner_does_not_depend_on_source_repository_layout() -> None:
    script = (M2A_PACKAGE / "run-milestone-2a.ps1").read_text(encoding="utf-8")
    assert "$PSScriptRoot '.." not in script
    assert "config\\route_b" not in script
    assert "remote-sdk-extractor\\scripts" not in script


def test_milestone_2a_script_has_structured_failure_codes_and_no_cms_call() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    for code in (
        "MISSING_JAVA_TOOL",
        "MISSING_SDK_JARS",
        "MISSING_CONFIRMED_CLASSES",
        "CLASSPATH_FAILURE",
        "MALFORMED_OUTPUT",
        "ARCHITECTURE_MISMATCH",
    ):
        assert code in script
    assert "CrystalEnterprise" not in script
    assert "logon(" not in script


def test_milestone_2a_java_version_uses_stderr_safe_helper_and_exit_code() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    helper = M2A_NATIVE_HELPER.read_text(encoding="utf-8")
    assert "invoke-informational-native.ps1" in script
    assert "-Arguments @('-version')" in script
    assert "-FailureCode 'JVM_DISCOVERY_FAILURE'" in script
    assert "System.Diagnostics.ProcessStartInfo" in helper
    assert "RedirectStandardError" in helper
    assert "ReadToEndAsync" in helper
    assert "$process.ExitCode" in helper
    assert "stdout = $stdout.Trim()" in helper
    assert "stderr = $stderr.Trim()" in helper
    assert "exit_code = $exitCode" in helper
    assert "discovery_progress.log" in script
    assert "JVM_DISCOVERY_START" in script
    assert "JVM_DISCOVERY_COMPLETE" in script
    assert "$process.ExitCode" in helper
    assert "if ($exitCode -ne 0)" in helper


def test_milestone_2a_runner_preserves_classpath_and_capability_steps() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    assert "runtime_classpath.txt" in script
    assert "sdk_jar_inventory.json" in script
    assert "validated_capabilities.json" in script
    assert "Milestone2aProbe" in script
    assert "-classpath $target.jar" in script
    assert "-classpath $classpath" not in script
    assert "ONE_JAR_PER_INVOCATION" in script
    assert "probeClasspathArgument" in script
    assert "milestone-2a-java.args" not in script
    assert "Join-Path $_ '*'" in script
    assert "Invoke-InformationalNativeCommand -Executable $tools['javac.exe']" in script
    assert "& $tools['javac.exe']" not in script
    assert "com.sap.sl.datasource.DataSource" in script
    assert "com.businessobjects.mds.datafoundation.DataFoundation" in script
    assert "javax.activation.DataSource" not in script
    assert "function Invoke-Phase" in script
    assert "Start-Job" in script
    assert "PHASE_TIMEOUT" in script
    assert "HEARTBEAT" in script
    assert "JAR_INVENTORY" in script
    assert "CANDIDATE_DISCOVERY" in script
    assert "JAVAP_DISCOVERY" in script


def test_milestone_2a_javac_stderr_is_exit_code_governed() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    compile_section = script.split("$compileArguments", 1)[1].split("$probeOutput", 1)[0]
    assert "-FailureCode 'CLASSPATH_FAILURE'" in compile_section
    assert "| Out-Null" in compile_section


def test_milestone_2a_discovery_prioritizes_exact_loading_classes() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    discovery = script.split("$discoveryClassNames", 1)[1].split("$candidateTargets", 1)[0]
    assert "com.sap.sl.datasource.DataSource" in discovery
    assert "com.businessobjects.mds.datafoundation.DataFoundation" in discovery
    assert "javax.activation.DataSource" not in discovery


def test_milestone_2a_probe_matches_capabilities_class_schema() -> None:
    probe = (JAVA_DIR / "Milestone2aProbe.java").read_text(encoding="utf-8")
    assert "Files.readAllLines" in probe
    assert "confirmed_classes.txt" in probe
    assert 'marker = "\\\"class\\\":\\\""' not in probe
    assert "CAPABILITY_HANDOFF_FAILURE" in probe


def test_runtime_capability_registry_uses_installed_namespaces_and_jars() -> None:
    registry = json.loads((REPO_ROOT / "config" / "route_b" / "confirmed_sdk_capabilities.json").read_text(encoding="utf-8"))
    capabilities = registry["capabilities"]
    assert not any("com.sap.sl.sdk.authoring" in item["class"] for item in capabilities)
    assert not any("com.sap.sl.sdk.authoring" in key for key in registry["enum_values"])
    business = [item for item in capabilities if item["class"].startswith("com.sap.sl.datasource.")]
    foundation = [item for item in capabilities if item["class"].startswith("com.businessobjects.mds.datafoundation.")]
    assert business and all(item["jar"] == "com.sap.sl.sdk.jar" for item in business)
    assert foundation and all(item["jar"] == "com.businessobjects.mds.datafoundation.jar" for item in foundation)
    assert "com.businessobjects.mds.datafoundation.Cardinality" in registry["enum_values"]
    assert "com.businessobjects.mds.datafoundation.Outer" in registry["enum_values"]
    assert "com.businessobjects.mds.datafoundation.JoinOperator" in registry["enum_values"]


def test_milestone_2a_javap_strategy_does_not_depend_on_windows_command_line_length() -> None:
    script = M2A_SCRIPT.read_text(encoding="utf-8")
    javap_section = script.split("$javapOutput", 1)[1].split("$javaSourceRoot", 1)[0]
    assert "-classpath $target.jar" in javap_section
    assert "$classpath" not in javap_section
    assert "deterministic per-JAR inspection" in script
