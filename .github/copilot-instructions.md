# Copilot Instructions — bo-universe-semantic-extractor

## Development Approach

- Use specification-driven development: before implementing a feature, write or update a specification in `docs/specs/` describing intent, inputs, outputs, and edge cases. Implement against that specification.
- Prefer small, reviewable, incremental commits over large sweeping changes.

## Security

- Do not hardcode secrets, credentials, hostnames, or tokens. Use environment variables (see `.env.example`) or files under `config/`.
- Never commit `.env` or any file containing real credentials.
- Treat BusinessObjects universe files as untrusted input; validate and sanitize before parsing.

## Code Style

- Prefer typed models (e.g. `dataclasses`, `pydantic`) over untyped dicts for extracted metadata.
- Target Python 3.11+, type-check with `mypy`, lint with `ruff`.
- Keep functions small and single-purpose; favor pure functions for parsing/normalization logic.

## Testing

- Require tests for all new behavior under `tests/`, mirroring the `src/` package structure.
- Use `pytest` as the test runner.
- Prefer fixtures with sample/anonymized universe metadata over live BI Platform connections in unit tests.

## Auditability

- Preserve auditability: log extraction run inputs, timestamps, and output locations.
- Do not silently discard or mutate source data during normalization; record transformations explicitly.

## Repository Conventions

- Source code lives in `src/`.
- Configuration (non-secret) lives in `config/`.
- Specifications and design docs live in `docs/specs/`.
- Generated output lives in `output/` and is gitignored.
- Reusable Copilot skills live in `.github/skills/`; reusable prompts live in `.github/prompts/`.
