# SAP BusinessObjects Payload Contracts (Placeholder — Unconfirmed)

**Status:** Every structure in this document is a **placeholder ingestion contract**, not a
confirmed SAP payload shape. It exists so the NORMALIZE stage
(`src/bo_semantic_extractor/normalization/converters.py`) and the sanitized contract-test
fixtures (`tests/fixtures/bo_rest/*.sample.json`) have one documented, versioned source of truth
to converge on. Every field below must be verified against a real (sanitized) SAP response or
official documentation before it is treated as authoritative — see
[businessobjects_missing_inputs.md](businessobjects_missing_inputs.md).

All payloads are carried inside the pipeline's own `RawArtifact` evidence envelope
(`src/bo_semantic_extractor/models/common.py`), which **is** confirmed/owned by this project:

```jsonc
{
  "run_id": "string",
  "source_system": "string",
  "source_operation": "string",
  "source_identifier": "string",
  "retrieved_at_utc": "ISO-8601 timestamp",
  "http_status": "integer | null",
  "content_hash_sha256": "64-char hex string",
  "redactions_applied": ["string", "..."],
  "payload": { "...": "the placeholder shapes below" }
}
```

## 1. `getUniverse` payload (placeholder)

Backs `Universe` (`models/universe.py`) via
`universe_from_raw_artifact()`. Matches
`tests/fixtures/bo_rest/universe_detail.sample.json`.

```jsonc
{
  "cuid": "string",              // REQUIRED_INPUT: confirm actual CUID field name/format
  "name": "string",
  "type": "UNX | UNV",           // REQUIRED_INPUT: confirm actual enumerated values
  "path": "string",              // repository folder path
  "description": "string | null",
  "connections": ["string", "..."]  // REQUIRED_INPUT: confirm shape (IDs vs. nested objects)
}
```

## 2. `listUniverseObjects` payload (placeholder)

Backs `UniverseObject` (`models/universe.py`) via
`universe_objects_from_raw_artifact()`. Matches
`tests/fixtures/bo_rest/universe_objects.sample.json`.

```jsonc
{
  "objects": [
    {
      "id": "string",
      "technical_name": "string",
      "name": "string",
      "folder": "string",
      "type": "dimension | attribute | measure | filter | hierarchy | level | parameter | ...",
      // REQUIRED_INPUT: confirm the full real enumeration; unrecognized values are
      // normalized to ObjectType.UNKNOWN and never guessed.
      "description": "string | null",
      "data_type": "string | null",
      "select": "string | null",      // REQUIRED_INPUT: confirm field name for SELECT expression
      "where": "string | null",       // REQUIRED_INPUT: confirm field name for WHERE expression
      "aggregation": "string | null"  // REQUIRED_INPUT: confirm field name for aggregation function
      // REQUIRED_INPUT: projection_function, associated_dimension_id, list_of_values_id,
      // is_hidden, is_deprecated, access_level are not yet represented in this placeholder —
      // their real field names/shapes are unknown.
    }
  ]
  // REQUIRED_INPUT: confirm whether this list is paginated, and if so, the pagination
  // envelope (page token / offset / total-count fields).
}
```

## 3. `listDependentDocuments` payload (placeholder)

Backs `WebIDocument` (`models/webi.py`). Matches
`tests/fixtures/bo_rest/webi_documents.sample.json`.

```jsonc
{
  "documents": [
    {
      "cuid": "string",
      "name": "string",
      "path": "string",
      "universes": ["string", "..."],   // universe CUIDs this document depends on
      "last_modified": "ISO-8601 timestamp | null"
    }
  ]
  // REQUIRED_INPUT: confirm pagination envelope and the exact filter mechanism used to
  // scope this list to "documents dependent on universe X".
}
```

## 4. `getDocumentMetadata` payload (placeholder)

Backs `DataProvider` and `ReportVariable` (`models/webi.py`). Matches
`tests/fixtures/bo_rest/webi_document_metadata.sample.json`.

```jsonc
{
  "data_providers": [
    {
      "id": "string",
      "name": "string",
      "universe_cuid": "string",
      "result_objects": ["string", "..."],   // REQUIRED_INPUT: object IDs vs. object names?
      "filters": ["string", "..."],          // REQUIRED_INPUT: raw filter text vs. structured filter tree?
      "prompts": ["string", "..."]           // REQUIRED_INPUT: prompt shape (text/type/default/mandatory)
    }
  ],
  "variables": [
    {
      "id": "string",
      "name": "string",
      "qualification": "dimension | measure | detail | null",
      "formula": "string | null",
      "dependencies": ["string", "..."]       // REQUIRED_INPUT: object IDs vs. variable names?
    }
  ]
  // REQUIRED_INPUT: merged-dimension representation is entirely unknown; no placeholder
  // shape is defined here to avoid inventing one. See Section 14 of
  // businessobjects_api_requirements.md.
}
```

## 5. Fields Deliberately Not Modeled Yet

The following are named in the skill's required normalized data model but have **no placeholder
payload shape** here because inventing one would risk being mistaken for a confirmed contract:

- Connection metadata (server, database, data-source type) without secrets.
- Security rules (row-level/object-level security mapping).
- Merged dimensions across data providers.
- Physical lineage / HANA catalog cross-reference fields (populated by the ENRICH stage from
  SAP HANA `SYS.*` metadata, not from BusinessObjects REST).

These remain `REQUIRED_INPUT` in
[businessobjects_missing_inputs.md](businessobjects_missing_inputs.md).

## 6. Contract Test Alignment

The sanitized fixtures under `tests/fixtures/bo_rest/*.sample.json` implement exactly the shapes
above and are validated by `tests/contract/test_bo_rest_contract.py` (envelope conformance) and
`tests/unit/test_normalization_converters.py` (mapping conformance). When any shape in this
document changes, update the corresponding fixture and re-run:

```bash
python -m pytest -q tests/contract tests/unit/test_normalization_converters.py
```

## 7. CONFIRMED — BusinessObjects Internal Query Panel Shapes

**Unlike sections 1–5 above, the shapes in this section are CONFIRMED** — derived directly from
sanitized evidence (`docs/evidence/`), not invented. They come from BusinessObjects' **internal
Query Panel service** (`source_system="BO_QUERY_PANEL_INTERNAL"`), which is a **different, less
formally documented API surface than the officially documented `/biprws/` REST API** that
sections 1–5 target. Confirming these shapes does **not** resolve any `REQUIRED_INPUT` item for
the `/biprws/` REST endpoints in
[businessobjects_api_requirements.md](businessobjects_api_requirements.md) — treat them as a
separate, additional evidence source.

### 7.1 Query Panel outline tree (`queryPanelOutline`)

Raw shape (typed as `QueryPanelOutlineNode` / `QueryPanelOutlineUserData` in
`src/bo_semantic_extractor/models/query_panel_outline_raw.py`; parser in
`src/bo_semantic_extractor/normalization/query_panel_outline.py`):

```jsonc
{
  "name": "string",
  "child": "boolean",       // whether this node has children
  "objType": "integer",     // CONFIRMED to exist; semantic meaning NOT yet mapped
  "help": "string | null",  // tooltip/description; sometimes a raw table.column mapping
  "userData": {
    "b": "string",          // CLS_* = class identifier, OBJ_* = object identifier (CONFIRMED patterns)
    "c": "integer",         // numeric type code; semantic meaning NOT yet mapped
    "g": "string | null",   // BJ_* = related identifier (CONFIRMED pattern)
    "h": "string | null",   // parent folder path (redundant with computed parent_object_path)
    "i": "string | null",   // description/tooltip, sometimes containing a table.column mapping
    "j": "integer | null",  // unmapped
    "s": "integer | null"   // unmapped qualification code
  },
  "nodes": ["...recursively, same shape..."]
}
```

Every field is preserved via `extra="allow"` on both raw models, so any additional key not
listed here is retained rather than silently dropped.

Normalized output (`QueryPanelOutlineRecord`, one per tree node, produced by
`normalize_outline_artifact()`): `source_node_id`, `related_source_id`, `object_name`,
`full_object_path`, `parent_object_path` (computed via traversal, not trusted solely from
`userData.h`), `description` (from `help`), `raw_obj_type` (raw `objType`, unmapped),
`classification_status` (`CONFIRMED_CLASS` / `CONFIRMED_OBJECT` / `UNKNOWN_IDENTIFIER_PATTERN`,
from the `userData.b` prefix only), `lineage_candidates` (unverified `table.column` matches
found in `help`/`userData.i`), `source_evidence_path`.

**Still unconfirmed:** the semantic meaning of `objType`, `userData.c`, `userData.s`, and
`userData.j` — no `ObjectType` is assigned from these codes; see
[businessobjects_missing_inputs.md](businessobjects_missing_inputs.md).

### 7.2 Query Panel universe listing (`getUniverseList`)

Confirmed shape: `payload.universes.universe[]`, each with `id` (int), `cuid`, `name` (includes
file extension, e.g. `.unx`), `description`, `type` (lowercase, e.g. `"unx"`), `subType` (e.g.
`"UnxRelational"`), `folderId`, `path`, `pathIds`, `revision`. Fixture:
`tests/fixtures/bo_rest/universe_listing.real_shape.sample.json`. No `connections` field is
present in this shape (unlike the `/biprws/` placeholder in section 1).

### 7.3 Query Panel initialization (`queryPanelInitialization`)

Confirmed shape includes `unvParameterArr[]` — real universe **prompt** metadata, each with
`question`, `name`, `dataType` (integer, unmapped), `id`. Fixture:
`tests/fixtures/bo_rest/query_panel_initialization.real_shape.sample.json`.
