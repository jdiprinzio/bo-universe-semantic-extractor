"""Pipeline stage framework: DISCOVER -> EXTRACT -> ARCHIVE -> NORMALIZE -> VALIDATE -> DOCUMENT.

Every stage writes a `StageManifest` recording its source operation, timestamps, source
identifier, and status, so a run is always auditable and restartable without corrupting
previously archived evidence. Use `stage_run` as a context manager around a stage's work.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from bo_semantic_extractor.bo_client.errors import BoClientError


class StageName(str, Enum):
    DISCOVER = "DISCOVER"
    EXTRACT = "EXTRACT"
    ARCHIVE = "ARCHIVE"
    NORMALIZE = "NORMALIZE"
    ENRICH = "ENRICH"
    VALIDATE = "VALIDATE"
    DOCUMENT = "DOCUMENT"
    RECONCILE = "RECONCILE"


class StageStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class StageManifest(BaseModel):
    """Structured, auditable record of one pipeline-stage execution."""

    stage: StageName
    run_id: str
    started_at_utc: datetime
    completed_at_utc: datetime
    status: StageStatus
    source_operation: str | None = None
    source_identifier: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    output_paths: list[str] = Field(default_factory=list)


class StageRecorder:
    """Mutable handle used inside a `stage_run` block to record stage output paths."""

    def __init__(self) -> None:
        self.output_paths: list[str] = []


def stage_manifest_path(manifest_root: Path, run_id: str, stage: StageName) -> Path:
    return manifest_root / run_id / f"{stage.value.lower()}_manifest.json"


def write_stage_manifest(manifest_root: Path, manifest: StageManifest) -> Path:
    path = stage_manifest_path(manifest_root, manifest.run_id, manifest.stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return path


def read_stage_manifest(manifest_root: Path, run_id: str, stage: StageName) -> StageManifest:
    path = stage_manifest_path(manifest_root, run_id, stage)
    return StageManifest.model_validate_json(path.read_text(encoding="utf-8"))


@contextmanager
def stage_run(
    stage: StageName,
    run_id: str,
    manifest_root: Path,
    source_operation: str | None = None,
    source_identifier: str | None = None,
) -> Iterator[StageRecorder]:
    """Run one pipeline stage, always writing a manifest, even on failure.

    On `BoClientError`, records the error's stable `error_code`/message and re-raises so
    callers (e.g. the CLI) stop rather than proceed past a failed stage.
    """
    started_at = datetime.now(UTC)
    recorder = StageRecorder()
    try:
        yield recorder
    except BoClientError as exc:
        write_stage_manifest(
            manifest_root,
            StageManifest(
                stage=stage,
                run_id=run_id,
                started_at_utc=started_at,
                completed_at_utc=datetime.now(UTC),
                status=StageStatus.FAILED,
                source_operation=source_operation,
                source_identifier=source_identifier,
                error_code=exc.error_code,
                error_message=exc.message,
            ),
        )
        raise
    write_stage_manifest(
        manifest_root,
        StageManifest(
            stage=stage,
            run_id=run_id,
            started_at_utc=started_at,
            completed_at_utc=datetime.now(UTC),
            status=StageStatus.SUCCESS,
            source_operation=source_operation,
            source_identifier=source_identifier,
            output_paths=recorder.output_paths,
        ),
    )
