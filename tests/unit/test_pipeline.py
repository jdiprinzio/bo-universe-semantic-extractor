"""Unit tests for the pipeline stage framework (manifests, restartability, error recording)."""

from __future__ import annotations

from pathlib import Path

import pytest

from bo_semantic_extractor.bo_client.errors import NotFoundError
from bo_semantic_extractor.pipeline import StageName, StageStatus, read_stage_manifest, stage_run


def test_stage_run_writes_success_manifest(tmp_path: Path) -> None:
    with stage_run(StageName.DISCOVER, "run-test-0001", tmp_path, "list_universes", "AAAA") as recorder:
        recorder.output_paths = ["some/path.json"]
    manifest = read_stage_manifest(tmp_path, "run-test-0001", StageName.DISCOVER)
    assert manifest.status is StageStatus.SUCCESS
    assert manifest.output_paths == ["some/path.json"]
    assert manifest.source_identifier == "AAAA"


def test_stage_run_writes_failed_manifest_and_reraises(tmp_path: Path) -> None:
    with pytest.raises(NotFoundError), stage_run(
        StageName.DISCOVER, "run-test-0002", tmp_path, "list_universes", "BBBB"
    ):
        raise NotFoundError("no universe found")
    manifest = read_stage_manifest(tmp_path, "run-test-0002", StageName.DISCOVER)
    assert manifest.status is StageStatus.FAILED
    assert manifest.error_code == "NOT_FOUND"


def test_stage_run_is_restartable_across_multiple_runs(tmp_path: Path) -> None:
    with stage_run(StageName.NORMALIZE, "run-test-0003", tmp_path, "normalize", "run-test-0003"):
        pass
    with stage_run(StageName.NORMALIZE, "run-test-0003", tmp_path, "normalize", "run-test-0003") as recorder:
        recorder.output_paths = ["normalized/objects.json"]
    manifest = read_stage_manifest(tmp_path, "run-test-0003", StageName.NORMALIZE)
    assert manifest.status is StageStatus.SUCCESS
    assert manifest.output_paths == ["normalized/objects.json"]
