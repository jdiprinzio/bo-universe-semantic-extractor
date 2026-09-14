# SAP BusinessObjects Integration Readiness Plan

## ROUTE_B_SDK Evidence Reconciliation — 2026-09-14

Post-Milestone-1 javap evidence supersedes the earlier SDK dependency uncertainty in this plan.
Business Layer/Data Foundation collections, join accessors, alias/derived-table accessors,
Cardinality, OuterType, and JoinOperator values are `CONFIRMED_BY_JAVAP` in
`docs/sdk_javap_evidence_register.md`. The remaining Route B inputs are only the complete
transitive classpath, confirmed read-only BLX/DFX or CMS loading path, confirmed `DataSource`
and `DataFoundation` providers, conditional CMS details/permissions, and remote working/export
directories.

**Status:** Planning document only. No source code is created or modified by this document.
It synthesizes [docs/businessobjects_api_requirements.md](businessobjects_api_requirements.md),
[docs/businessobjects_payload_contracts.md](businessobjects_payload_contracts.md), and
[docs/businessobjects_missing_inputs.md](businessobjects_missing_inputs.md) into an actionable
plan for the critical path: acquiring real API/payload knowledge before any endpoint is
implemented in `src/bo_semantic_extractor/bo_client/rest_client.py`.

## 1. Inventory — Missing API Dependencies

| # | API Dependency | Blocks | Status |
|---|---|---|---|
| A1 | Logon/authentication endpoint contract (path, method, request/response shape, token header) | Everything | REQUIRED_INPUT |
| A2 | Session management contract (token lifetime, renewal, concurrency limits) | Everything | REQUIRED_INPUT |
| A3 | Logoff/session-termination endpoint | Clean shutdown, test hygiene | REQUIRED_INPUT |
| A4 | Universe discovery/listing endpoint (list/search published universes) | `discover` stage | REQUIRED_INPUT |
| A5 | Universe resolution by exact CUID or exact name (parameter contract) | `discover` stage | REQUIRED_INPUT |
| A6 | Universe metadata endpoint (`getUniverse`-equivalent) | `extract` stage | REQUIRED_INPUT |
| A7 | Universe object listing endpoint, incl. pagination contract | `extract` stage | REQUIRED_INPUT |
| A8 | Connection metadata endpoint (secrets excluded) | Documentation completeness | REQUIRED_INPUT |
| A9 | WebI dependent-document discovery endpoint (filter by universe CUID) | `extract` stage (WebI) | REQUIRED_INPUT |
| A10 | WebI document metadata endpoint (data providers, variables, prompts, merged dimensions) | `extract` stage (WebI) | REQUIRED_INPUT |
| A11 | Query-execution endpoint for controlled reconciliation sampling (if it exists) | RECONCILE stage (future) | REQUIRED_INPUT |
| A12 | Security-rule extraction endpoint(s) or SDK path | Security migration mapping (future) | REQUIRED_INPUT |

This table mirrors the per-area detail already recorded in
[businessobjects_api_requirements.md](businessobjects_api_requirements.md) §3–14; it exists here
as a single at-a-glance checklist for planning purposes.

## 2. Inventory — Missing Payload Samples

| # | Sample Needed | Used To Confirm | Placeholder Location |
|---|---|---|---|
| P1 | Real (sanitized) logon request + response, headers included | A1, A2 | Not yet placeholdered (no auth payload shape exists in code) |
| P2 | Universe listing/search response with ≥2 universes | A4, A5 | Not yet placeholdered |
| P3 | Single universe metadata response (`getUniverse`) | A6 | `docs/businessobjects_payload_contracts.md` §1; fixture `tests/fixtures/bo_rest/universe_detail.sample.json` |
| P4 | Universe object listing response covering **every** `ObjectType` (dimension, attribute, measure, filter, hierarchy, level, parameter) plus at least one unrecognized/unknown type | A7 | `docs/businessobjects_payload_contracts.md` §2; fixture `tests/fixtures/bo_rest/universe_objects.sample.json` (currently only dimension/measure/unknown are represented) |
| P5 | Paginated universe-object response (if pagination exists) showing page 1 and page 2 | A7 | Not yet placeholdered |
| P6 | Connection metadata response with all secret fields redacted by the provider | A8 | Not yet placeholdered |
| P7 | WebI dependent-document listing response | A9 | `docs/businessobjects_payload_contracts.md` §3; fixture `tests/fixtures/bo_rest/webi_documents.sample.json` |
| P8 | WebI document metadata response with ≥1 data provider, ≥1 filter, ≥1 prompt, ≥1 variable with formula | A10 | `docs/businessobjects_payload_contracts.md` §4; fixture `tests/fixtures/bo_rest/webi_document_metadata.sample.json` |
| P9 | WebI document metadata response for a document with ≥2 data providers and a merged dimension | A10 (merged dimensions) | Not yet placeholdered |
| P10 | Authentication failure response (already sanitized-placeholder only) | Negative contract tests | Fixture `tests/fixtures/bo_rest/auth_failure.sample.json` (placeholder, not derived from a real 401) |

Every placeholder fixture listed above must be re-validated against the real sample once
received — do not assume the placeholder shape is correct.

## 3. Inventory — Missing SDK Dependencies

| # | SDK/Tooling | Why It May Be Needed | Status |
|---|---|---|---|
| S1 | SAP BI Semantic Layer Java SDK (design-time universe authoring/metadata access) | Fallback source (skill priority #3) for universe metadata not exposed via REST — e.g., certain expression or context/join details | REQUIRED_INPUT: confirm whether this environment's universes expose full metadata via REST first; only pursue if REST is confirmed insufficient |
| S2 | SAP BusinessObjects BI Platform Java SDK | Only relevant if the RESTful Web Service SDK cannot reach a required resource (e.g., low-level CMS query) | REQUIRED_INPUT: same as above |
| S3 | A supported HTTP client library version compatible with this BI Platform's TLS/cipher requirements | Runtime connectivity | REQUIRED_INPUT: confirm TLS requirements from the platform administrator; `httpx` is already a project dependency and should suffice unless a custom CA or client-cert auth is required |
| S4 | SAP HANA Python client / ODBC driver for lineage enrichment | ENRICH stage (already optional/deferred) | REQUIRED_INPUT: confirm HANA driver availability/licensing for this environment when ENRICH stage work begins |

No SDK has been installed or added as a project dependency for S1/S2/S4. Do not add them
speculatively — only add once a REQUIRED_INPUT above confirms they are actually necessary.

## 4. Minimum Payload Sample Set to Implement Each Extraction Path

This section defines the **smallest** set of real (sanitized) samples needed to move each
extraction path from placeholder to confirmed, in priority order.

### 4.1 Universe extraction (DISCOVER + `getUniverse`)

Minimum set:
1. One logon request/response pair (P1) — needed before any authenticated call can be made.
2. One universe listing/search response containing at least the target universe (P2).
3. One single-universe metadata response for that same universe (P3).

Any additional universes in P2 are useful for testing `AmbiguousMatchError` behavior on
exact-name collisions, but are not required for the minimum path.

### 4.2 Universe-object extraction (`listUniverseObjects`)

Minimum set:
1. Everything in §4.1 (a universe must be resolved before its objects can be listed).
2. One universe-object listing response (P4) that includes **at least one object of each**
   `ObjectType` currently modeled (`dimension`, `attribute`, `measure`, `filter`, `hierarchy`,
   `level`, `parameter`) plus one object with a type value not in that list, to confirm the
   `ObjectType.UNKNOWN` fallback path against a real (not fixture-invented) unrecognized value.
3. If the real API paginates this response, one additional page (P5) — otherwise confirmation
   in writing that the response is never paginated for a universe of this size.

### 4.3 WebI dependency extraction (`listDependentDocuments` + `getDocumentMetadata`)

Minimum set:
1. Everything in §4.1 (a universe must be resolved first).
2. One dependent-document listing response for that universe (P7), containing at least one
   document.
3. One document-metadata response for that document (P8) containing at least one data
   provider, one query filter, one prompt, and one report variable with a formula.
4. Optional but recommended: one document-metadata response with a merged dimension (P9), to
   confirm the currently-undefined merged-dimension shape before modeling it.

## 5. Manual Validation Procedures

These procedures apply once any real payload sample (P1–P10) is provided, **before** it is used
to update a fixture or implement an endpoint.

1. **Redact before anything else touches the file.** Confirm the sample contains no passwords,
   tokens, session cookies, API keys, or PII. If the sample was captured with `curl -v` or a
   browser network trace, strip `Authorization`, `Cookie`, and `Set-Cookie` header values before
   the file is saved anywhere in this repository or shared in chat.
2. **Confirm provenance.** Record, at minimum: BI Platform version/patch level, the exact
   request that produced the response (method + path, with placeholders for any IDs), and the
   date captured. This becomes the fixture's evidence trail (mirrors the `RawArtifact` evidence
   fields already used at runtime).
3. **Diff against the current placeholder.** Compare the real sample's field names/types against
   the corresponding placeholder in
   [businessobjects_payload_contracts.md](businessobjects_payload_contracts.md). List every
   field that differs (renamed, restructured, missing, or additional) before changing any code.
4. **Validate against the pipeline's evidence envelope.** Confirm the real response can be
   wrapped in the existing `RawArtifact` model (`run_id`, `source_system`, `source_operation`,
   `source_identifier`, `retrieved_at_utc`, `http_status`, `content_hash_sha256`,
   `redactions_applied`, `payload`) without modification — this envelope is project-owned and
   should not need to change.
5. **Identify unknown/unmapped values explicitly.** For universe-object `type` values, list any
   value not already in the `ObjectType` enum. Per the skill's rule, these must map to
   `ObjectType.UNKNOWN`, never be coerced to the closest known type and never silently dropped.
6. **Get explicit sign-off before implementation.** A payload sample resolves a `REQUIRED_INPUT`
   item only after someone with authority over this environment confirms it is representative
   (not a one-off or malformed edge case).

## 6. Converting Real Payloads into Sanitized Fixtures

Follow this procedure for every real sample that passes manual validation (§5):

1. **Start from a copy, never the original.** Never edit or commit the original captured file.
2. **Replace all real identifiers with fixture-safe placeholders**, keeping structure intact:
   - CUIDs → repeated letters matching the real length/format seen (e.g., 40 `A`/`B`/`C`
     characters, consistent with the existing fixtures under `tests/fixtures/bo_rest/`).
   - Real universe/document/object names → clearly fictitious names (e.g., `SAMPLE_SALES_UNIVERSE`,
     following the existing fixture naming convention).
   - Server hostnames, database names, schema names → generic placeholders
     (e.g., `sample-host.invalid`, `SAMPLE_DB`).
   - Timestamps → fixed, clearly-fictitious dates (existing fixtures use `2026-01-15T...`).
3. **Preserve structural fidelity.** Keep the same nesting, field names, field types, and
   cardinality (e.g., if the real response has 3 result objects in a data provider, keep 3, not
   1) so the fixture is a faithful contract test, not a simplification.
4. **Wrap in the `RawArtifact` envelope** exactly as the existing fixtures do — `run_id`,
   `source_system`, `source_operation`, `source_identifier`, `retrieved_at_utc`, `http_status`,
   `content_hash_sha256` (recompute via
   `bo_semantic_extractor.extractors.archive.compute_content_hash` over the canonicalized
   payload), and `redactions_applied` (list every field type redacted, e.g., `"Authorization"`).
5. **Save under `tests/fixtures/bo_rest/`** using the existing naming convention
   (`<operation>.sample.json`), replacing or adding alongside the current placeholder file.
6. **Update the corresponding contract/unit tests** (`tests/contract/test_bo_rest_contract.py`,
   `tests/unit/test_normalization_converters.py`) to assert against the new, real-shaped fixture.
7. **Update `docs/businessobjects_payload_contracts.md`** to replace the placeholder shape with
   the confirmed shape, and move the corresponding row in
   `docs/businessobjects_api_requirements.md` from `REQUIRED_INPUT` to `CONFIRMED` with a
   citation (the sample's provenance recorded in §5.2).
8. **Run the full test suite** (`ruff`, `mypy`, `pytest`) to confirm nothing regresses before
   considering the fixture conversion complete.

## 7. Prioritized Implementation Tasks (Once Payloads Become Available)

Ordered so each task's prerequisites are satisfied by the tasks above it. No task in this list
should begin until its listed payload sample(s) have passed §5 and §6.

| Order | Task | Requires |
|---|---|---|
| 1 | Implement authentication in `RestSemanticLayerClient` (real logon path, token handling, logoff) | P1 validated + converted |
| 2 | Implement `list_universes` | P2 validated + converted |
| 3 | Implement `get_universe`; update `universe_from_raw_artifact` mapping if field names differ | P3 validated + converted |
| 4 | Implement `list_universe_objects`, including pagination handling if confirmed necessary; update `universe_objects_from_raw_artifact` mapping | P4 (+ P5 if paginated) validated + converted |
| 5 | Re-run `tests/unit/test_validation_rules.py` and `tests/unit/test_normalization_converters.py` against real-shaped fixtures; adjust `ObjectType` enum only if a business-approved new type is confirmed (never guessed) | Tasks 1–4 complete |
| 6 | Implement `list_dependent_documents` | P7 validated + converted |
| 7 | Implement `get_document_metadata`; extend `models/webi.py`/converters for merged dimensions if P9 is available | P8 (+ P9 if available) validated + converted |
| 8 | Add a connection-metadata client method and model (currently unmodeled) | P6 validated + converted |
| 9 | Re-validate end-to-end `extract` → `normalize` → `validate` → `document` CLI flow against one real universe in a non-production environment | Tasks 1–7 complete |
| 10 | Revisit security-rule extraction and HANA lineage enrichment scoping | A12, S4 resolved |

## 8. Summary

| Category | Confirmed | Required Input |
|---|---|---|
| API dependencies (§1) | 0 | 12 |
| Payload samples (§2) | 0 | 10 |
| SDK dependencies (§3) | 0 | 4 (all conditional — none confirmed necessary yet) |

The critical path is unchanged from
[businessobjects_missing_inputs.md](businessobjects_missing_inputs.md): nothing in this plan can
begin until Priority 1 (authentication/session) is resolved, because every other endpoint
requires an authenticated session.
