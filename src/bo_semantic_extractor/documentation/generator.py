"""Documentation-generation scaffolding for the DOCUMENT pipeline stage.

Generators consume already-normalized, typed models only (never raw payloads or model
memory) and write the artifacts listed under `output/{universe_slug}/` in
[README.md](../../../README.md). Functions implemented here produce real output from typed
input; functions still marked `NotImplementedError` are scaffolded but require later stages
(lineage enrichment, validation, reconciliation) that are out of scope for this change set.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import yaml

from bo_semantic_extractor.models import Universe, UniverseObject
from bo_semantic_extractor.models.query_panel_outline_normalized import QueryPanelOutlineRecord
from bo_semantic_extractor.pipeline import StageManifest
from bo_semantic_extractor.validation.findings import ValidationFinding

# Deterministic column order for object_catalog.csv, independent of dict/model field order.
OBJECT_CATALOG_COLUMNS = [
    "universe_cuid",
    "object_id",
    "technical_name",
    "object_name",
    "folder_path",
    "object_type",
    "description",
    "data_type",
    "aggregation_function",
    "is_hidden",
    "is_deprecated",
    "extraction_source",
    "source_evidence_path",
]


def generate_object_catalog_csv(objects: list[UniverseObject]) -> str:
    """Render `object_catalog.csv` with a stable column order, sorted by object_id."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=OBJECT_CATALOG_COLUMNS)
    writer.writeheader()
    for obj in sorted(objects, key=lambda o: o.object_id):
        row = obj.model_dump(include=set(OBJECT_CATALOG_COLUMNS))
        row["object_type"] = row["object_type"].value if hasattr(row["object_type"], "value") else row["object_type"]
        writer.writerow(row)
    return buffer.getvalue()


def generate_object_catalog_json(objects: list[UniverseObject]) -> str:
    """Render `object_catalog.json` sorted by object_id, using UTF-8/deterministic ordering."""
    sorted_objects = sorted(objects, key=lambda o: o.object_id)
    return json.dumps(
        [o.model_dump(mode="json") for o in sorted_objects],
        indent=2,
        sort_keys=True,
    )


def generate_object_catalog_json_from_outline_records(
    records: list[QueryPanelOutlineRecord],
) -> str:
    """Render `object_catalog.json` from parsed Query Panel outline records.

    Used while the officially documented universe-object REST endpoint remains unconfirmed
    (see `docs/businessobjects_api_requirements.md`). Records carry identifier-*pattern*
    classification and lineage *candidates* only; they never assign a semantic `ObjectType`.
    Sorted by `full_object_path` for determinism, not display name alone.
    """
    sorted_records = sorted(records, key=lambda r: r.full_object_path)
    return json.dumps(
        [r.model_dump(mode="json") for r in sorted_records],
        indent=2,
        sort_keys=True,
    )


def generate_universe_summary_markdown(
    universe: Universe,
    objects: list[UniverseObject],
    *,
    generated_at_utc: datetime | None = None,
) -> str:
    """Render `universe_summary.md` from normalized facts only (counts, not narrative claims)."""
    generated_at_utc = generated_at_utc or datetime.now(UTC)
    type_counts: dict[str, int] = {}
    missing_descriptions = 0
    unknown_types = 0
    for obj in objects:
        object_type = obj.object_type.value if hasattr(obj.object_type, "value") else str(obj.object_type)
        type_counts[object_type] = type_counts.get(object_type, 0) + 1
        if not obj.description:
            missing_descriptions += 1
        if object_type == "unknown":
            unknown_types += 1

    lines = [
        f"# Universe Summary: {universe.universe_name}",
        "",
        f"- Universe CUID: `{universe.universe_cuid}`",
        f"- Type: {universe.universe_type}",
        f"- Repository path: `{universe.repository_path}`",
        f"- Source system: {universe.source_system}",
        f"- Extracted at (UTC): {universe.extracted_at_utc.isoformat()}",
        f"- Summary generated at (UTC): {generated_at_utc.isoformat()}",
        "",
        "## Object Counts (from current extraction output)",
        "",
    ]
    for object_type, count in sorted(type_counts.items()):
        lines.append(f"- {object_type}: {count}")
    lines += [
        "",
        "## Data Quality Findings",
        "",
        f"- Objects missing a description: {missing_descriptions}",
        f"- Objects with an unknown type: {unknown_types}",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_universe_documentation(
    universe: Universe,
    objects: list[UniverseObject],
    output_root: Path,
) -> dict[str, Path]:
    """Write the currently-implemented documentation artifacts for one universe.

    Returns a mapping of artifact name to written path. Artifacts that depend on
    lineage enrichment, security extraction, WebI extraction, validation, or
    reconciliation are not produced by this function yet; see `generator.py`
    module docstring.
    """
    universe_dir = output_root / universe.universe_cuid
    universe_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    summary_path = universe_dir / "universe_summary.md"
    summary_path.write_text(
        generate_universe_summary_markdown(universe, objects), encoding="utf-8"
    )
    written["universe_summary.md"] = summary_path

    catalog_csv_path = universe_dir / "object_catalog.csv"
    catalog_csv_path.write_text(generate_object_catalog_csv(objects), encoding="utf-8")
    written["object_catalog.csv"] = catalog_csv_path

    catalog_json_path = universe_dir / "object_catalog.json"
    catalog_json_path.write_text(generate_object_catalog_json(objects), encoding="utf-8")
    written["object_catalog.json"] = catalog_json_path

    return written


def generate_physical_lineage_csv(*_args: object, **_kwargs: object) -> str:
    """Scaffolded: requires the ENRICH stage's verified `PhysicalSource`/`Relationship` data."""
    raise NotImplementedError("Requires HANA lineage enrichment (ENRICH stage), not yet implemented.")


def generate_security_rules_csv(*_args: object, **_kwargs: object) -> str:
    """Scaffolded: requires extracted `SecurityRule` records, not yet implemented."""
    raise NotImplementedError("Requires security-rule extraction, not yet implemented.")


def generate_webi_report_inventory_csv(*_args: object, **_kwargs: object) -> str:
    """Scaffolded: requires extracted `WebIDocument`/`DataProvider` records."""
    raise NotImplementedError("Requires WebI extraction (Step 5), not yet implemented.")


def generate_agent_metadata_json(*_args: object, **_kwargs: object) -> str:
    """Scaffolded: requires validated `SemanticEnrichment` review status, not yet implemented."""
    raise NotImplementedError("Requires the VALIDATE stage and enrichment review, not yet implemented.")


VALIDATION_FINDING_COLUMNS = [
    "finding_id",
    "category",
    "severity",
    "message",
    "universe_cuid",
    "object_id",
]


def generate_validation_findings_csv(findings: list[ValidationFinding]) -> str:
    """Render `validation_findings.csv`, sorted by finding_id for determinism."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=VALIDATION_FINDING_COLUMNS)
    writer.writeheader()
    for finding in sorted(findings, key=lambda f: f.finding_id):
        row = finding.model_dump(mode="json", include=set(VALIDATION_FINDING_COLUMNS))
        writer.writerow(row)
    return buffer.getvalue()


def generate_universe_manifest_yaml(
    universe: Universe,
    run_id: str,
    stage_manifests: list[StageManifest],
) -> str:
    """Render `universe_manifest.yaml` summarizing the run's stages, from typed models only."""
    manifest: dict[str, object] = {
        "run_id": run_id,
        "universe_cuid": universe.universe_cuid,
        "universe_name": universe.universe_name,
        "universe_type": universe.universe_type,
        "source_system": universe.source_system,
        "extracted_at_utc": universe.extracted_at_utc.isoformat(),
        "stages": [
            {
                "stage": manifest_entry.stage.value,
                "status": manifest_entry.status.value,
                "started_at_utc": manifest_entry.started_at_utc.isoformat(),
                "completed_at_utc": manifest_entry.completed_at_utc.isoformat(),
                "error_code": manifest_entry.error_code,
            }
            for manifest_entry in stage_manifests
        ],
    }
    return yaml.safe_dump(manifest, sort_keys=False)


def generate_extraction_report_markdown(
    universe: Universe,
    objects: list[UniverseObject],
    findings: list[ValidationFinding],
    stage_manifests: list[StageManifest],
) -> str:
    """Render `extraction_report.md` from normalized models and validation findings only."""
    findings_by_category: dict[str, int] = {}
    for finding in findings:
        findings_by_category[finding.category.value] = (
            findings_by_category.get(finding.category.value, 0) + 1
        )

    lines = [f"# Extraction Report: {universe.universe_name}", ""]
    lines.append("## Stage Results")
    lines.append("")
    if stage_manifests:
        for manifest_entry in stage_manifests:
            suffix = f" ({manifest_entry.error_code})" if manifest_entry.error_code else ""
            lines.append(f"- {manifest_entry.stage.value}: {manifest_entry.status.value}{suffix}")
    else:
        lines.append("- No stage manifests supplied to this report.")
    lines += [
        "",
        f"## Object Count: {len(objects)}",
        "",
        "## Validation Findings",
        "",
    ]
    if findings_by_category:
        for category, count in sorted(findings_by_category.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- No validation findings.")
    lines.append("")
    return "\n".join(lines)


def generate_reconciliation_cases_yaml(*_args: object, **_kwargs: object) -> str:
    """Scaffolded: requires the RECONCILE stage harness, not yet implemented."""
    raise NotImplementedError("Requires the RECONCILE stage, not yet implemented.")
