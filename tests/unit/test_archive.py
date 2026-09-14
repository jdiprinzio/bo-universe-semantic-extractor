"""Unit tests for the raw-evidence archiving framework (ARCHIVE stage)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from bo_semantic_extractor.extractors.archive import (
    EvidenceCategory,
    RunManifest,
    archive_raw_artifact,
    build_raw_artifact,
    categorize_artifact,
    init_run_directories,
    new_run_id,
    read_run_manifest,
    write_run_manifest,
)


def test_new_run_id_is_unique() -> None:
    assert new_run_id() != new_run_id()


def test_init_run_directories_creates_required_layout(tmp_path: Path) -> None:
    run_id = "run-test-0001"
    root = init_run_directories(tmp_path, run_id)
    for category in ("universe", "connections", "objects", "webi_documents", "webi_queries"):
        assert (root / category).is_dir()


def test_build_raw_artifact_computes_a_sha256_hash() -> None:
    artifact = build_raw_artifact(
        run_id="run-test-0001",
        source_system="BO_SEMANTIC_LAYER_REST",
        source_operation="getUniverse",
        source_identifier="AAAA",
        payload={"cuid": "AAAA"},
    )
    assert len(artifact.content_hash_sha256) == 64


def test_archive_raw_artifact_rejects_tampered_hash(tmp_path: Path) -> None:
    artifact = build_raw_artifact(
        run_id="run-test-0001",
        source_system="BO_SEMANTIC_LAYER_REST",
        source_operation="getUniverse",
        source_identifier="AAAA",
        payload={"cuid": "AAAA"},
    )
    tampered = artifact.model_copy(update={"content_hash_sha256": "0" * 64})
    init_run_directories(tmp_path, "run-test-0001")
    with pytest.raises(ValueError):
        archive_raw_artifact(tmp_path, "run-test-0001", EvidenceCategory.UNIVERSE, tampered)


def test_archive_raw_artifact_writes_file_in_expected_category(tmp_path: Path) -> None:
    run_id = "run-test-0001"
    init_run_directories(tmp_path, run_id)
    artifact = build_raw_artifact(
        run_id=run_id,
        source_system="BO_SEMANTIC_LAYER_REST",
        source_operation="getUniverse",
        source_identifier="AAAA",
        payload={"cuid": "AAAA"},
    )
    path = archive_raw_artifact(tmp_path, run_id, EvidenceCategory.UNIVERSE, artifact)
    assert path.exists()
    assert path.parent.name == "universe"


def test_categorize_artifact_maps_known_operations() -> None:
    artifact = build_raw_artifact(
        run_id="run-test-0001",
        source_system="BO_SEMANTIC_LAYER_REST",
        source_operation="getUniverse",
        source_identifier="AAAA",
        payload={},
    )
    assert categorize_artifact(artifact) is EvidenceCategory.UNIVERSE


def test_categorize_artifact_defaults_unknown_operations_to_objects() -> None:
    artifact = build_raw_artifact(
        run_id="run-test-0001",
        source_system="BO_SEMANTIC_LAYER_REST",
        source_operation="someFutureOperation",
        source_identifier="AAAA",
        payload={},
    )
    assert categorize_artifact(artifact) is EvidenceCategory.OBJECTS


def test_run_manifest_round_trips(tmp_path: Path) -> None:
    manifest = RunManifest(
        run_id="run-test-0001",
        created_at_utc=datetime.now(UTC),
        universe_cuid="AAAA",
        artifact_count=1,
    )
    write_run_manifest(tmp_path, manifest)
    loaded = read_run_manifest(tmp_path, "run-test-0001")
    assert loaded.universe_cuid == "AAAA"
    assert loaded.artifact_count == 1
