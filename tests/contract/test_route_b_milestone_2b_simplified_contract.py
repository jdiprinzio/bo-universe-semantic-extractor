"""Contracts for the Milestone 2B Architecture Simplification.

Orchestration (JAR discovery, filtering, class enumeration, reflection, progress
logging, diagnostics) now runs entirely inside ProviderDiscoveryProbe. PowerShell is
reduced to path validation, compilation, and a single java invocation with no
PowerShell-to-Java handoff files and no Start-Job usage.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "remote-sdk-extractor" / "scripts" / "run-provider-discovery.ps1"
PROBE = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
PACKAGE = REPO_ROOT / "remote-sdk-extractor" / "dist" / "milestone-2b-provider-discovery"


def test_runner_has_no_start_job_or_handoff_files() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "Start-Job" not in runner
    assert "Receive-Job" not in runner
    assert "included_jars" not in runner
    assert "confirmed_classes" not in runner
    assert "ConvertFrom-Json" not in runner


def test_runner_compiles_then_launches_with_xmx4g() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    assert "'JAVA_COMPILATION_FAILURE'" in runner
    assert "-Xmx4g" in runner
    assert "com.vistance.bo.routeb.ProviderDiscoveryProbe" in runner
    assert "$SapInstallRoot,$IdtPluginDirectory,$OutputDirectory" in runner


def test_runner_passes_only_three_probe_arguments() -> None:
    runner = RUNNER.read_text(encoding="utf-8")
    launch_line = next(line for line in runner.splitlines() if "ProviderDiscoveryProbe" in line and "Invoke-InformationalNativeCommand" in line)
    assert launch_line.count(",") == 6  # java.exe args array: -Xmx4g,-cp,classes,class,3 probe args


def test_probe_performs_discovery_filtering_and_enumeration_internally() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "Files.walkFileTree" in probe
    assert "PROVIDER_JAR_PREFIXES" in probe
    assert "KNOWN_JAR_NAMES" in probe
    assert "IRRELEVANT_JAR_TERMS" in probe
    assert "new JarFile(" in probe
    assert "readJars" not in probe
    assert "readLines" not in probe


def test_probe_uses_assignability_and_tolerates_class_load_failures() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "isAssignableFrom(returnType)" in probe
    for exception_name in ("ClassNotFoundException", "NoClassDefFoundError", "ExceptionInInitializerError", "UnsatisfiedLinkError"):
        assert f"catch ({exception_name} error)" in probe
    assert "related_return_type_inventory.json" in probe
    assert "new URLClassLoader" in probe


def test_probe_owns_single_writer_progress_logging_and_scope_counters() -> None:
    probe = PROBE.read_text(encoding="utf-8")
    assert "discovery_progress.log" in probe
    assert "System.out.println(line)" in probe
    assert "PROBE_SCOPE HEARTBEAT jar=" in probe
    assert "PROBE_SCOPE jars=" in probe
    assert "PROBE_SCOPE_MISMATCH" in probe
    assert "import java.nio.charset.StandardCharsets;" in probe


def test_package_is_source_only_and_portable_with_no_orchestration_modules() -> None:
    forbidden_extensions = {".jar", ".unx", ".blx", ".dfx", ".cns"}
    files = [path for path in PACKAGE.rglob("*") if path.is_file()]
    assert files
    assert all(path.suffix.lower() not in forbidden_extensions for path in files)
    assert not (PACKAGE / "provider-scan-handoff.ps1").exists()
    assert not (PACKAGE / "failure-diagnostics.ps1").exists()
    assert not (PACKAGE / "simulate-provider-discovery.ps1").exists()
    assert (PACKAGE / "run-provider-discovery.ps1").exists()
    assert (PACKAGE / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java").exists()
