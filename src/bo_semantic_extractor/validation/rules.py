"""Validation rules for the VALIDATE stage.

Each rule inspects normalized models only (never raw payloads or model memory) and returns
explicit `ValidationFinding`s. Nothing here silently passes or fails a run.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from bo_semantic_extractor.models import ObjectType, UniverseObject
from bo_semantic_extractor.validation.findings import (
    FindingCategory,
    FindingSeverity,
    ValidationFinding,
)


def find_duplicate_object_names(objects: list[UniverseObject]) -> list[ValidationFinding]:
    """Flag every member of a group of objects sharing the same display name."""
    groups: dict[str, list[UniverseObject]] = {}
    for obj in objects:
        groups.setdefault(obj.object_name, []).append(obj)

    findings: list[ValidationFinding] = []
    for name, group in groups.items():
        if len(group) <= 1:
            continue
        folders = ", ".join(sorted({o.folder_path for o in group}))
        for obj in group:
            findings.append(
                ValidationFinding(
                    finding_id=f"DUP-{obj.object_id}",
                    category=FindingCategory.DUPLICATE_OBJECT_NAME,
                    severity=FindingSeverity.WARNING,
                    message=f"Duplicate object name {name!r} found in folders: {folders}.",
                    universe_cuid=obj.universe_cuid,
                    object_id=obj.object_id,
                )
            )
    return findings


def find_missing_descriptions(objects: list[UniverseObject]) -> list[ValidationFinding]:
    return [
        ValidationFinding(
            finding_id=f"NODESC-{obj.object_id}",
            category=FindingCategory.MISSING_DESCRIPTION,
            severity=FindingSeverity.INFO,
            message=f"Object {obj.object_name!r} ({obj.object_id}) has no description.",
            universe_cuid=obj.universe_cuid,
            object_id=obj.object_id,
        )
        for obj in objects
        if not obj.description
    ]


def find_unknown_object_types(objects: list[UniverseObject]) -> list[ValidationFinding]:
    return [
        ValidationFinding(
            finding_id=f"UNKTYPE-{obj.object_id}",
            category=FindingCategory.UNKNOWN_OBJECT_TYPE,
            severity=FindingSeverity.WARNING,
            message=f"Object {obj.object_name!r} ({obj.object_id}) has an unknown object type.",
            universe_cuid=obj.universe_cuid,
            object_id=obj.object_id,
        )
        for obj in objects
        if obj.object_type is ObjectType.UNKNOWN
    ]


def validate_schema(objects: list[UniverseObject]) -> list[ValidationFinding]:
    """Re-validate every normalized object against its Pydantic schema (round-trip check)."""
    findings: list[ValidationFinding] = []
    for obj in objects:
        try:
            UniverseObject.model_validate(obj.model_dump())
        except ValidationError as exc:
            findings.append(
                ValidationFinding(
                    finding_id=f"SCHEMA-{obj.object_id}",
                    category=FindingCategory.SCHEMA_VALIDATION_ERROR,
                    severity=FindingSeverity.ERROR,
                    message=str(exc),
                    universe_cuid=obj.universe_cuid,
                    object_id=obj.object_id,
                )
            )
    return findings


def validate_raw_evidence_linkage(
    objects: list[UniverseObject], repo_root: Path
) -> list[ValidationFinding]:
    """Every normalized object must link to a raw evidence file that actually exists."""
    findings: list[ValidationFinding] = []
    for obj in objects:
        evidence_path = repo_root / obj.source_evidence_path
        if not evidence_path.exists():
            findings.append(
                ValidationFinding(
                    finding_id=f"NOEVID-{obj.object_id}",
                    category=FindingCategory.MISSING_RAW_EVIDENCE,
                    severity=FindingSeverity.ERROR,
                    message=f"Raw evidence file not found: {obj.source_evidence_path}",
                    universe_cuid=obj.universe_cuid,
                    object_id=obj.object_id,
                )
            )
    return findings


def run_all_validations(
    objects: list[UniverseObject], repo_root: Path
) -> list[ValidationFinding]:
    """Run every validation rule and return the combined list of findings."""
    findings: list[ValidationFinding] = []
    findings.extend(find_duplicate_object_names(objects))
    findings.extend(find_missing_descriptions(objects))
    findings.extend(find_unknown_object_types(objects))
    findings.extend(validate_schema(objects))
    findings.extend(validate_raw_evidence_linkage(objects, repo_root))
    return findings
