# Universe Lineage Acquisition Strategy

**Status:** Strategy/design document only. No code is added or changed by this document. It
defines *how* authoritative physical lineage (Business Object → Expression → Data Foundation
Object → Join → Calculation View/Table → HANA Column) will eventually be acquired for
`DM_Invoice_Data_Mart.unx`, and which artifact/tool each layer of that chain requires. Actual
retrieval logic (Java SDK calls, IDT export parsing, HANA catalog queries) is out of scope here
— see [businessobjects_missing_inputs.md](businessobjects_missing_inputs.md) and
[integration_readiness_plan.md](integration_readiness_plan.md) for the implementation backlog
this strategy feeds.

## 1. Why Lineage Cannot Be Fully Derived From Query Panel Alone

The Query Panel outline parser implemented for `DM_Invoice_Data_Mart.unx`
(`src/bo_semantic_extractor/normalization/query_panel_outline.py`) gives a **presentation-layer
view** of the universe: the folder/object tree a report author sees, with a free-text `help`
tooltip that *sometimes* happens to contain a `table.column`-shaped string (e.g.
`SAMPLE_DIMENSION.ORG_NAME` for the `Organization` object). That string is a **lineage
candidate**, never a verified physical mapping — the Query Panel service does not expose the
universe's actual SELECT expression, WHERE clause, join graph, or underlying Data Foundation
table/column references. Authoritative lineage requires descending into the artifacts below.

## 2. Metadata Available From Query Panel (Already Acquired)

| Metadata | Source | Confidence |
|---|---|---|
| Business object display name, folder path, hierarchy nesting | `queryPanelOutline` (`QueryPanelOutlineNode.name`, `.nodes`) | CONFIRMED (from evidence) |
| Business object stable identifier pattern (`CLS_*` class, `OBJ_*` object) | `queryPanelOutline` (`userData.b`) | CONFIRMED pattern; semantic meaning of numeric `objType`/`userData.c`/`userData.s` still unmapped |
| Related-identifier pattern (`BJ_*`) | `queryPanelOutline` (`userData.g`) | CONFIRMED pattern; purpose (e.g. link to a business-layer internal ID) unconfirmed |
| Free-text description/tooltip | `queryPanelOutline` (`help`, `userData.i`) | CONFIRMED to exist; not guaranteed to contain a physical mapping |
| Unverified `table.column` **lineage candidate** strings | Regex extraction over `help`/`userData.i` (`extract_lineage_candidates()`) | CANDIDATE ONLY — not verified against any schema |
| Universe-level prompts (question text, parameter id) | `queryPanelInitialization` (`unvParameterArr`) | CONFIRMED (from evidence) |
| Universe identity/listing (cuid, name, type, path, revision) | `getUniverseList` | CONFIRMED (from evidence) |

**None of the above confirms**: the real SELECT/WHERE expression, aggregation function,
associated dimension, list of values, join graph, context, or the physical table/column/schema
an object actually resolves to at query time.

## 3. Metadata Requiring Business Layer (.blx) / Data Foundation (.dfx)

A published `.unx` universe is a package (documented Information Design Tool concept) containing
at minimum a **Business Layer** (`.blx`) and a **Data Foundation** (`.dfx`), plus connection
resources. Each carries metadata Query Panel does not expose:

| Metadata | Required Artifact | Why Query Panel Can't Provide It |
|---|---|---|
| Business object **SELECT expression** (the actual formula, e.g. `@Select(...)` or SQL) | Business Layer (`.blx`) | Query Panel exposes only display name + tooltip, not the formula |
| Business object **WHERE clause** / object-level filter | Business Layer (`.blx`) | Not exposed via outline/init/listing |
| **Aggregation function** and **projection function** for measures | Business Layer (`.blx`) | Not exposed |
| **Associated dimension** for attributes, **list of values** binding | Business Layer (`.blx`) | Not exposed |
| **Predefined filters**, filter expressions | Business Layer (`.blx`) | Not exposed |
| Business Layer → Data Foundation object mapping (which DF table/column a business object's expression references) | Business Layer (`.blx`) referencing Data Foundation (`.dfx`) | This mapping only exists inside the Business Layer's expression definitions |
| **Data Foundation tables** (physical table/view names, connection/schema) | Data Foundation (`.dfx`) | Not exposed by Query Panel at all |
| **Joins** between Data Foundation tables (join expression, cardinality) | Data Foundation (`.dfx`) | Not exposed |
| **Contexts** (join-path disambiguation for multi-fact scenarios) | Data Foundation (`.dfx`) | Not exposed |
| **Derived tables** in the Data Foundation (custom SQL) | Data Foundation (`.dfx`) | Not exposed |

## 4. Metadata Requiring the SAP Semantic Layer Java SDK / Information Design Tool (IDT)

The Business Layer and Data Foundation resources above are only reliably readable through one
of:

- **SAP BI Semantic Layer Java SDK** (design-time API for `.blx`/`.dfx` resources), used
  programmatically without opening IDT interactively, or
- **Information Design Tool (IDT)**, used interactively by a universe designer to export or
  inspect the resources.

Neither is invoked by this document. Confirmed reasons this tier is required:

- The officially documented BI Platform RESTful Web Service API surface (targeted by
  `RestSemanticLayerClient`) is confirmed to have a guide
  (`docs/businessobjects_api_requirements.md` §2) but its exact universe-object-detail
  endpoint/payload shape is still `REQUIRED_INPUT` — until confirmed, expression-level and
  join-level metadata should be assumed to require the Java SDK/IDT path, per the skill's
  documented source-priority order (REST first, Java SDK only for metadata REST cannot expose).
- Business Layer/Data Foundation resources are binary/XML-packaged design-time artifacts; there
  is no evidence in this project that the Query Panel or WebI REST surfaces expose their full
  expression graph.

| Metadata | Required Tool | Retrieval Mode |
|---|---|---|
| Full Business Layer object graph (all folders/objects/expressions/aggregations) | Semantic Layer Java SDK or IDT | Programmatic (SDK) or interactive export (IDT) |
| Full Data Foundation graph (tables/joins/contexts/derived tables) | Semantic Layer Java SDK or IDT | Programmatic (SDK) or interactive export (IDT) |
| Connection resource detail (`.cnx`/`.cns`) needed to resolve which physical database a Data Foundation table belongs to | Semantic Layer Java SDK or IDT (or, once confirmed, a BI Platform REST connection-metadata endpoint — still `REQUIRED_INPUT`) | Programmatic or interactive |

## 5. Metadata Requiring SAP HANA Metadata

Once a Data Foundation table/column reference is known (from §3–4), it must still be **verified**
against the real physical catalog before it is trusted as lineage — a Data Foundation can
reference a HANA calculation view, a physical table, or a schema-qualified view, and naming in
the universe does not guarantee an exact catalog match.

| Metadata | Source | Purpose |
|---|---|---|
| Schema/table/view existence and column list | HANA `SYS.TABLES`, `SYS.VIEWS`, `SYS.TABLE_COLUMNS` (or an approved read-only metadata tool) | Confirm a Data Foundation table/column reference resolves to a real object |
| Calculation view structure (if the Data Foundation points at a calc view rather than a base table) | HANA `SYS.CALC_VIEW_DEFINITIONS` / calc-view catalog metadata (or an approved read-only metadata tool) | Distinguish a direct table reference from a semantic calc-view layer |
| Column data type / nullability (optional, for validation findings) | `SYS.TABLE_COLUMNS` | Cross-check Business Layer `data_type` claims |

Per the skill's rules, this stage is **read-only**, **optional**, and must never execute
extracted SQL to "discover" lineage — it only verifies candidates already identified from §2–4.

## 6. Per-Artifact Acquisition Requirements

| Artifact | Retrieval Method | Permissions Required | Evidence Quality | Verification Status |
|---|---|---|---|---|
| Query Panel outline (`queryPanelOutline`) | Internal Query Panel service call (already evidenced; endpoint path still not formally documented) | Authenticated BI Platform session with read access to the universe | Confirmed structure; lineage-candidate content only | CONFIRMED (structure) / CANDIDATE (lineage content) |
| Query Panel initialization (`queryPanelInitialization`) | Internal Query Panel service call (already evidenced) | Same as above | Confirmed structure | CONFIRMED (structure) |
| Universe listing (`getUniverseList`) | Internal Query Panel service call (already evidenced) | Same as above | Confirmed structure | CONFIRMED (structure) |
| Business Layer (`.blx`) | Semantic Layer Java SDK read API, or IDT "Export" of the universe resources, or (if/when confirmed) a BI Platform REST universe-detail endpoint | Universe read/view right in CMC; for IDT export, designer-level access to the universe in a local/shared project | High — authoritative source of business-object expressions | REQUIRED_INPUT (no sample acquired yet) |
| Data Foundation (`.dfx`) | Semantic Layer Java SDK read API, or IDT export, packaged alongside the Business Layer inside the `.unx` | Same as Business Layer | High — authoritative source of tables/joins/contexts | REQUIRED_INPUT (no sample acquired yet) |
| Connection resource (`.cnx`/`.cns`) | Semantic Layer Java SDK, IDT, or CMC connection properties (secrets excluded) | Connection "View" right in CMC | Medium — confirms target database/schema, not credentials | REQUIRED_INPUT |
| HANA catalog metadata (`SYS.*`) | Read-only SQL against an approved HANA metadata role, or an approved read-only metadata MCP/tool | A HANA database user with `SELECT` on `SYS` catalog views only (no data-table access required for structure-only verification) | Highest — ground truth for physical existence | REQUIRED_INPUT (HANA connection/role not yet confirmed for this environment) |

## 7. Lineage Evidence Matrix

This is the authoritative chain this pipeline must eventually reconstruct and verify, and the
artifact tier each link depends on:

```text
Business Object
     │  (display name, folder path — CONFIRMED via Query Panel outline)
     ▼
Expression
     │  (SELECT/WHERE/aggregation formula — REQUIRES Business Layer .blx)
     ▼
Data Foundation Object
     │  (physical table/column the expression references — REQUIRES Data Foundation .dfx)
     ▼
Join
     │  (join expression/cardinality connecting Data Foundation tables — REQUIRES Data Foundation .dfx)
     ▼
Calculation View or Table
     │  (the actual HANA object the Data Foundation table maps to — REQUIRES Data Foundation .dfx
     │   connection metadata + HANA catalog cross-reference)
     ▼
HANA Column
     (verified physical column — REQUIRES SAP HANA SYS.* metadata)
```

| Link in the chain | Source tier | Status for `DM_Invoice_Data_Mart.unx` |
|---|---|---|
| Business Object | Query Panel | CONFIRMED (outline parser implemented) |
| → Expression | Business Layer (.blx) | REQUIRED_INPUT |
| → Data Foundation Object | Data Foundation (.dfx) | REQUIRED_INPUT |
| → Join | Data Foundation (.dfx) | REQUIRED_INPUT |
| → Calculation View or Table | Data Foundation (.dfx) + connection metadata | REQUIRED_INPUT |
| → HANA Column | SAP HANA `SYS.*` metadata | REQUIRED_INPUT (`LineageVerificationStatus.VERIFIED` not yet reachable for any object) |

Every object currently produced by the Query Panel outline parser
(`QueryPanelOutlineRecord.lineage_candidates`) sits at the **top** of this chain only — a
candidate string extracted from a tooltip is not evidence of any link below "Business Object."
The existing `LineageVerificationStatus` enum (`VERIFIED` / `PARSED_UNVERIFIED` / `UNKNOWN`,
`src/bo_semantic_extractor/models/common.py`) already models exactly this distinction; every
current lineage candidate must be treated as `PARSED_UNVERIFIED` until it passes through §3–5.

## 8. Clear Separation of Metadata Sources

To prevent conflating confirmed structure with unverified content, every extracted record must
be traceable to exactly one of these four sources, and this document (plus
`docs/businessobjects_api_requirements.md` and `docs/businessobjects_payload_contracts.md`)
must keep them visually and structurally distinct:

1. **Query Panel metadata** — `source_system="BO_QUERY_PANEL_INTERNAL"`. Presentation-layer
   only. Already implemented (`normalization/query_panel_outline.py`). Never a source of
   verified expressions, joins, or physical columns.
2. **Business Layer metadata** — would use a new `source_system` value (e.g.
   `"BO_SEMANTIC_LAYER_BUSINESS_LAYER"`) once a retrieval method is confirmed. Authoritative for
   business-object expressions and aggregation/projection functions. Not yet implemented.
3. **Data Foundation metadata** — would use a new `source_system` value (e.g.
   `"BO_SEMANTIC_LAYER_DATA_FOUNDATION"`) once a retrieval method is confirmed. Authoritative
   for physical tables, joins, and contexts. Not yet implemented.
4. **HANA metadata** — would use `source_system="SAP_HANA_CATALOG"` (or similar) once a
   read-only connection is confirmed for this environment. Authoritative for physical
   existence/verification only; never used to *discover* lineage by executing extracted SQL.
   Corresponds to the pipeline's existing (currently unimplemented) ENRICH stage.

## 9. Non-Goals of This Document

- No Java code, SDK calls, IDT automation, or HANA queries are implemented here.
- No endpoint path or SDK API method signature is asserted as confirmed; where retrieval method
  is stated above as "Semantic Layer Java SDK or IDT," that reflects the skill's documented
  source-priority order, not a verified API call.
- This document does not resolve any `REQUIRED_INPUT` row in
  [businessobjects_missing_inputs.md](businessobjects_missing_inputs.md) — it organizes *which*
  artifact resolves *which* future row, so acquisition work can be sequenced correctly.

## 10. Suggested Next Step (Planning Only)

Before any Business Layer/Data Foundation code is written, obtain **one** sanitized `.blx`/`.dfx`
export (or Java SDK read-API sample output) for `DM_Invoice_Data_Mart.unx`, covering at least one
business object's full expression and one join, and run it through the same manual validation
procedure already defined in
[integration_readiness_plan.md](integration_readiness_plan.md#5-manual-validation-procedures)
before modeling it.
