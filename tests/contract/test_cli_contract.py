"""Contract tests for the CLI: verifies fail-closed behavior without fabricating SAP endpoints."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from bo_semantic_extractor.cli import app

runner = CliRunner()


def test_discover_fails_closed_when_universe_selector_missing(monkeypatch, tmp_path: Path) -> None:
    """The default dev profile has no universe selected; config validation must fail closed."""
    monkeypatch.setenv("BO_BASE_URL", "https://bo.example.invalid")
    monkeypatch.setenv("BO_AUTH_TYPE", "secEnterprise")
    monkeypatch.setenv("BO_USERNAME", "sample-user")
    monkeypatch.setenv("BO_PASSWORD", "sample-password")
    result = runner.invoke(app, ["discover", "--profile", "config/extraction_profiles/dev.yaml"])
    assert result.exit_code != 0


def test_discover_fails_closed_without_required_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("BO_BASE_URL", raising=False)
    monkeypatch.delenv("BO_USERNAME", raising=False)
    monkeypatch.delenv("BO_PASSWORD", raising=False)
    monkeypatch.delenv("BO_AUTH_TYPE", raising=False)
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        "profile_name: test\nuniverse:\n  cuid: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["discover", "--profile", str(profile_path)])
    assert result.exit_code != 0


def test_extract_fails_with_sdk_unavailable_when_endpoints_unconfirmed(
    monkeypatch, tmp_path: Path
) -> None:
    """Documents that extract never fabricates a SAP endpoint: it fails closed instead."""
    profile_path = tmp_path / "profile.yaml"
    profile_path.write_text(
        "profile_name: test\nuniverse:\n  cuid: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BO_BASE_URL", "https://bo.example.invalid")
    monkeypatch.setenv("BO_AUTH_TYPE", "secEnterprise")
    monkeypatch.setenv("BO_USERNAME", "sample-user")
    monkeypatch.setenv("BO_PASSWORD", "sample-password")
    result = runner.invoke(app, ["extract", "--profile", str(profile_path)])
    assert result.exit_code == 1
    assert "SDK_UNAVAILABLE" in result.stdout


def test_normalize_fails_closed_when_no_archived_evidence_exists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["normalize", "--run-id", "run-does-not-exist"])
    assert result.exit_code == 1
