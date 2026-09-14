"""Typer CLI: command wiring only.

Business logic lives in `extractors/`, `normalization/`, `validation/`, and `documentation/`;
this module only parses options, loads configuration, and dispatches to those modules. No SAP
endpoint paths are defined or invented here — `extract` fails closed with `SDK_UNAVAILABLE`
until real endpoints are confirmed and configured (see `bo_client/rest_client.py`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import typer

from bo_semantic_extractor.bo_client.errors import BoClientError
from bo_semantic_extractor.bo_client.rest_client import RestSemanticLayerClient
from bo_semantic_extractor.config import load_app_config
from bo_semantic_extractor.documentation.generator import (
    generate_extraction_report_markdown,
    generate_validation_findings_csv,
    write_universe_documentation,
)
from bo_semantic_extractor.extractors.archive import (
    RunManifest,
    archive_raw_artifact,
    categorize_artifact,
    init_run_directories,
    new_run_id,
    write_run_manifest,
)
from bo_semantic_extractor.extractors.discover import discover_universe
from bo_semantic_extractor.extractors.extract import extract_universe_artifacts
from bo_semantic_extractor.logging_config import configure_logging, get_logger
from bo_semantic_extractor.models import RawArtifact, Universe, UniverseObject
from bo_semantic_extractor.normalization.converters import (
    universe_from_raw_artifact,
    universe_objects_from_raw_artifact,
    write_normalized_output,
)
from bo_semantic_extractor.pipeline import StageName, stage_run
from bo_semantic_extractor.validation.rules import run_all_validations

app = typer.Typer(help="Read-only SAP BusinessObjects universe semantic extraction pipeline.")

_DEFAULT_PROFILE = Path("config/extraction_profiles/dev.yaml")
_RAW_ROOT = Path("raw")
_NORMALIZED_ROOT = Path("normalized")
_OUTPUT_ROOT = Path("output")

logger = get_logger(__name__)


def _fail(exc: BoClientError) -> typer.Exit:
    typer.secho(f"{exc.error_code}: {exc.message}", fg=typer.colors.RED)
    return typer.Exit(code=1)


@app.command()
def discover(
    profile: Path = typer.Option(_DEFAULT_PROFILE, help="Extraction profile YAML path."),
) -> None:
    """Resolve the target universe by CUID or exact name (read-only, no extraction)."""
    run_id = new_run_id()
    try:
        config = load_app_config(profile)
        configure_logging(config.environment.log_level)
        client = RestSemanticLayerClient(base_url=config.environment.base_url)
        selector = config.profile.universe
        with stage_run(
            StageName.DISCOVER,
            run_id,
            _RAW_ROOT,
            "list_universes",
            selector.cuid or selector.exact_name,
        ):
            summary = discover_universe(client, selector)
    except BoClientError as exc:
        raise _fail(exc) from exc
    typer.echo(f"[{run_id}] Resolved universe: {summary.universe_name} ({summary.universe_cuid})")


@app.command()
def extract(
    profile: Path = typer.Option(_DEFAULT_PROFILE, help="Extraction profile YAML path."),
) -> None:
    """DISCOVER + EXTRACT + ARCHIVE raw evidence for the configured universe.

    Fails with SDK_UNAVAILABLE until confirmed SAP REST endpoint paths are configured; this
    is expected and intentional until real endpoints are supplied.
    """
    run_id = new_run_id()
    try:
        config = load_app_config(profile)
        configure_logging(config.environment.log_level)
        client = RestSemanticLayerClient(base_url=config.environment.base_url)
        selector = config.profile.universe

        with stage_run(
            StageName.DISCOVER,
            run_id,
            _RAW_ROOT,
            "list_universes",
            selector.cuid or selector.exact_name,
        ):
            summary = discover_universe(client, selector)

        with stage_run(
            StageName.EXTRACT,
            run_id,
            _RAW_ROOT,
            "extract_universe_artifacts",
            summary.universe_cuid,
        ):
            artifacts = extract_universe_artifacts(
                client, summary.universe_cuid, config.profile.extraction
            )
    except BoClientError as exc:
        raise _fail(exc) from exc

    init_run_directories(_RAW_ROOT, run_id)
    with stage_run(
        StageName.ARCHIVE, run_id, _RAW_ROOT, "archive_raw_artifacts", summary.universe_cuid
    ) as recorder:
        written_paths = [
            str(archive_raw_artifact(_RAW_ROOT, run_id, categorize_artifact(artifact), artifact))
            for artifact in artifacts
        ]
        write_run_manifest(
            _RAW_ROOT,
            RunManifest(
                run_id=run_id,
                created_at_utc=datetime.now(UTC),
                universe_cuid=summary.universe_cuid,
                artifact_count=len(artifacts),
            ),
        )
        recorder.output_paths = written_paths

    typer.echo(f"[{run_id}] Archived {len(artifacts)} raw artifacts under raw/{run_id}/")


@app.command()
def normalize(
    run_id: str = typer.Option(..., help="Run ID produced by 'extract' (raw/{run_id}/)."),
) -> None:
    """Convert archived raw evidence into typed, versioned normalized models."""
    universe_dir = _RAW_ROOT / run_id / "universe"
    objects_dir = _RAW_ROOT / run_id / "objects"
    universe_files = sorted(universe_dir.glob("*.json")) if universe_dir.exists() else []
    if not universe_files:
        typer.secho(f"No archived universe evidence found under {universe_dir}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    with stage_run(StageName.NORMALIZE, run_id, _RAW_ROOT, "normalize_universe", run_id) as recorder:
        universe_artifact = RawArtifact.model_validate_json(
            universe_files[0].read_text(encoding="utf-8")
        )
        universe = universe_from_raw_artifact(universe_artifact)

        objects: list[UniverseObject] = []
        object_files = sorted(objects_dir.glob("*.json")) if objects_dir.exists() else []
        for object_file in object_files:
            artifact = RawArtifact.model_validate_json(object_file.read_text(encoding="utf-8"))
            objects.extend(universe_objects_from_raw_artifact(artifact))

        paths = write_normalized_output(_NORMALIZED_ROOT, run_id, universe, objects)
        recorder.output_paths = [str(p) for p in paths]

    typer.echo(f"[{run_id}] Normalized {len(objects)} objects to {_NORMALIZED_ROOT / run_id}/")


@app.command()
def validate(
    run_id: str = typer.Option(..., help="Run ID previously normalized."),
) -> None:
    """Run validation rules against normalized models for a given run."""
    objects_path = _NORMALIZED_ROOT / run_id / "objects.json"
    if not objects_path.exists():
        typer.secho(
            f"No normalized objects found for run {run_id}; run 'normalize' first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    with stage_run(StageName.VALIDATE, run_id, _RAW_ROOT, "run_all_validations", run_id) as recorder:
        objects = [
            UniverseObject.model_validate(entry)
            for entry in json.loads(objects_path.read_text(encoding="utf-8"))
        ]
        findings = run_all_validations(objects, Path.cwd())
        output_dir = _OUTPUT_ROOT / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        findings_path = output_dir / "validation_findings.csv"
        findings_path.write_text(generate_validation_findings_csv(findings), encoding="utf-8")
        recorder.output_paths = [str(findings_path)]

    typer.echo(f"[{run_id}] {len(findings)} validation findings written to {findings_path}")


@app.command()
def document(
    run_id: str = typer.Option(..., help="Run ID previously normalized."),
) -> None:
    """Generate documentation artifacts from normalized models for a given run."""
    universe_path = _NORMALIZED_ROOT / run_id / "universe.json"
    objects_path = _NORMALIZED_ROOT / run_id / "objects.json"
    if not universe_path.exists() or not objects_path.exists():
        typer.secho(
            f"No normalized data found for run {run_id}; run 'normalize' first.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    with stage_run(StageName.DOCUMENT, run_id, _RAW_ROOT, "generate_documentation", run_id) as recorder:
        universe = Universe.model_validate_json(universe_path.read_text(encoding="utf-8"))
        objects = [
            UniverseObject.model_validate(entry)
            for entry in json.loads(objects_path.read_text(encoding="utf-8"))
        ]
        findings = run_all_validations(objects, Path.cwd())
        written = write_universe_documentation(universe, objects, _OUTPUT_ROOT)
        report_path = _OUTPUT_ROOT / universe.universe_cuid / "extraction_report.md"
        report_path.write_text(
            generate_extraction_report_markdown(universe, objects, findings, []),
            encoding="utf-8",
        )
        recorder.output_paths = [str(p) for p in written.values()] + [str(report_path)]

    typer.echo(f"[{run_id}] Documentation written to {_OUTPUT_ROOT / universe.universe_cuid}/")


if __name__ == "__main__":
    app()
