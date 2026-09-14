"""Raw evidence archiving (ARCHIVE stage): unmodified API responses with hashes, timestamps,
source identifiers, and redaction records.

Layout:

    raw/{run_id}/
        run_manifest.json
        universe/
        connections/
        objects/
        webi_documents/
        webi_queries/
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from bo_semantic_extractor.models import RawArtifact

RAW_EVIDENCE_CATEGORIES = (
    "universe",
    "connections",
    "objects",
    "webi_documents",
    "webi_queries",
)


class EvidenceCategory(str, Enum):
    UNIVERSE = "universe"
    CONNECTIONS = "connections"
    OBJECTS = "objects"
    WEBI_DOCUMENTS = "webi_documents"
    WEBI_QUERIES = "webi_queries"


_OPERATION_CATEGORY_MAP: dict[str, EvidenceCategory] = {
    "getUniverse": EvidenceCategory.UNIVERSE,
    "listUniverseObjects": EvidenceCategory.OBJECTS,
    "listDependentDocuments": EvidenceCategory.WEBI_DOCUMENTS,
    "getDocumentMetadata": EvidenceCategory.WEBI_QUERIES,
}


def categorize_artifact(artifact: RawArtifact) -> EvidenceCategory:
    """Map a RawArtifact's source operation to its raw-evidence category folder."""
    return _OPERATION_CATEGORY_MAP.get(artifact.source_operation, EvidenceCategory.OBJECTS)


class RunManifest(BaseModel):
    """Top-level manifest for one extraction run's raw evidence tree."""

    run_id: str
    created_at_utc: datetime
    universe_cuid: str | None = None
    artifact_count: int = 0


def new_run_id() -> str:
    return f"run-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"


def compute_content_hash(payload_bytes: bytes) -> str:
    return hashlib.sha256(payload_bytes).hexdigest()


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def build_raw_artifact(
    *,
    run_id: str,
    source_system: str,
    source_operation: str,
    source_identifier: str,
    payload: dict[str, Any],
    http_status: int | None = None,
    redactions_applied: list[str] | None = None,
    retrieved_at_utc: datetime | None = None,
) -> RawArtifact:
    """Build a `RawArtifact` with a content hash computed from its (redacted) payload."""
    return RawArtifact(
        run_id=run_id,
        source_system=source_system,
        source_operation=source_operation,
        source_identifier=source_identifier,
        retrieved_at_utc=retrieved_at_utc or datetime.now(UTC),
        http_status=http_status,
        content_hash_sha256=compute_content_hash(_canonical_payload_bytes(payload)),
        redactions_applied=redactions_applied or [],
        payload=payload,
    )


def run_root(raw_root: Path, run_id: str) -> Path:
    return raw_root / run_id


def init_run_directories(raw_root: Path, run_id: str) -> Path:
    """Create the raw/{run_id}/ directory tree. Idempotent, so a run can be restarted safely."""
    root = run_root(raw_root, run_id)
    for category in RAW_EVIDENCE_CATEGORIES:
        (root / category).mkdir(parents=True, exist_ok=True)
    return root


def archive_raw_artifact(
    raw_root: Path,
    run_id: str,
    category: EvidenceCategory,
    artifact: RawArtifact,
) -> Path:
    """Write one RawArtifact to raw/{run_id}/{category}/{source_identifier}.json.

    Verifies the artifact's `content_hash_sha256` against its payload before writing, so raw
    evidence can never be silently altered.
    """
    expected_hash = compute_content_hash(_canonical_payload_bytes(artifact.payload))
    if expected_hash != artifact.content_hash_sha256:
        raise ValueError(
            f"content_hash_sha256 mismatch for {artifact.source_identifier}: "
            f"expected {expected_hash}, got {artifact.content_hash_sha256}"
        )
    category_dir = run_root(raw_root, run_id) / category.value
    category_dir.mkdir(parents=True, exist_ok=True)
    safe_name = artifact.source_identifier.replace("/", "_")
    artifact_path = category_dir / f"{safe_name}.json"
    artifact_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
    return artifact_path


def write_run_manifest(raw_root: Path, manifest: RunManifest) -> Path:
    root = run_root(raw_root, manifest.run_id)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "run_manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest_path


def read_run_manifest(raw_root: Path, run_id: str) -> RunManifest:
    manifest_path = run_root(raw_root, run_id) / "run_manifest.json"
    return RunManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
