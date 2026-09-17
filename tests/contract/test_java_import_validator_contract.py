"""Static Java import validation, wired into the local test suite so missing-import
defects (like the Hotfix 3 StandardCharsets regression) fail locally instead of on the
remote BusinessObjects machine.
"""

from pathlib import Path

from tools.java_import_validator import format_failure, validate_directory

REPO_ROOT = Path(__file__).resolve().parents[2]
JAVA_SRC = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java"


def test_all_java_sources_have_no_missing_imports() -> None:
    findings = validate_directory(JAVA_SRC)
    assert not findings, format_failure(findings)


def test_validator_detects_a_removed_import_and_recovers() -> None:
    path = JAVA_SRC / "com" / "vistance" / "bo" / "routeb" / "ProviderDiscoveryProbe.java"
    original = path.read_text(encoding="utf-8")
    mutated = original.replace("import java.nio.charset.StandardCharsets;\n", "")
    assert mutated != original, "fixture no longer contains the expected import line"
    try:
        path.write_text(mutated, encoding="utf-8")
        findings = validate_directory(JAVA_SRC)
        assert any(item.type_name == "StandardCharsets" for item in findings)
    finally:
        path.write_text(original, encoding="utf-8")
    assert not validate_directory(JAVA_SRC)
