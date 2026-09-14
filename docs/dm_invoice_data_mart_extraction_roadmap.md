# DM_Invoice_Data_Mart.unx — Extraction Roadmap

**Status:** Planning document only. No extraction code is added or changed by this document. It
defines *how* the confirmed design inventory in
[dm_invoice_data_mart_design_inventory.md](dm_invoice_data_mart_design_inventory.md) will
eventually be turned into the six catalog files below, and in what order, given what evidence
already exists vs. what still requires IDT, the Semantic Layer Java SDK, or SAP HANA metadata.
It builds directly on
[universe_lineage_acquisition_strategy.md](universe_lineage_acquisition_strategy.md).

## 0. Confirmed Starting Inventory

The following counts are CONFIRMED (see the design inventory report) and are the baseline this
roadmap plans against:

| Item | Count |
|---|---|
| Classes (folders) | 204 |
| Dimensions | 925 |
| Attributes | 179 |
| Measures | 785 |
| Filters (declared) | 83 (61 printed with a `Where expression`; 22 undetailed) |
| Select expressions | 1,904 |
| Tables | 38 |
| Joins | 34 |
| Derived tables | 3 |
| Alias tables (declared) | 11 (0 individually identified in the PDF text) |

## 1. Extracting Business Layer Metadata From the BLX Design

Two distinct routes exist; this roadmap uses both, in sequence, never conflating their evidence
quality:

### 1.1 Route A — PDF design report (already used for the inventory)

The Apache FOP-generated `.blx` "print" report
(`docs/evidence/DM_Invoice_Data_Mart_blx.pdf`) is a **rendered derivative** of the real `.blx`
resource, not the resource itself. It is useful because it already contains, as extractable
text: every folder/dimension/attribute/measure/filter name, `Cuid`, `Path`, `Data Type`, `Select`
expression, `Where expression` (filters only), and `Projection Function` (measures only). It
does **not** contain join type, cardinality, alias/standard table identity, or physical
HANA-verified column mappings (those are icons/graphics in the PDF, not text).

Route A extraction steps (planning-level, no code):

1. Re-run the same text-extraction method used for the design inventory (a PDF-to-text tool)
   against the BLX PDF, treated as a versioned, re-derivable artifact — never hand-edited.
2. Parse the repeating per-object block pattern already identified: heading line
   (`Folder:` / `Dimension:` / `Attribute:` / `Measure:` / `Filter:`) followed by labeled
   fields (`Name`, `Description`, `Cuid`, `Translation ID`, `Path`, `State`, `Data Type`,
   `SQL Definition` → `Select`, `Where expression` for filters, `Projection Function` for
   measures, `Aggregatable` for some attributes).
3. Preserve every raw field exactly (mirroring the Query Panel raw-model approach already used
   in `src/bo_semantic_extractor/models/query_panel_outline_raw.py` — extend that pattern here
   rather than inventing a new preservation convention).
4. Treat the four Cuid identifier patterns already confirmed (`CLS_*`, `OBJ_*`, `FIL_*`, and the
   32 legacy GUID-style identifiers) as **patterns to classify**, not types to assign — consistent
   with the "never coerce an unknown type" rule already applied to Query Panel `objType`.

### 1.2 Route B — Authoritative `.blx` resource (not yet available)

Only Route B can eventually confirm what Route A cannot: the true internal Business Layer
object graph, including any structural metadata rendered as icons in the PDF (e.g. exact
qualification enum, list-of-values source binding, per-parameter definitions, per-LOV
definitions — none of which were found as text in Route A; see design inventory §1.6). Route B
requires the Semantic Layer Java SDK or IDT — see §6.

## 2. Extracting Data Foundation Metadata From the DFX Design

Same two-route structure as §1:

### 2.1 Route A — PDF design report

`docs/evidence/DM_Invoice_Data_Mart_dfx.pdf` yields, as extractable text: the 38 table names, the
3 derived table names, the 1 view name (`Master`), the connection name/path/server (`HOCTST`,
`//HOCTST.cnx`, `@BODRNC`), and all 34 join expressions verbatim (including the two joins with
compound `and` conditions and the one join with an embedded non-join predicate). It does **not**
yield: which 11 of the 38 tables are aliases, which 24 are "standard," the 3 derived tables'
underlying SQL, join type, join cardinality, or driver/database type as a structured field.

Route A extraction steps:

1. Parse the `Joins (34)` section: each entry is a single line of the form
   `Join <left>.<col>=<right>.<col>[ and <left2>.<col2>=<right2>.<col2>][ and <extra predicate>]`.
   Split on the literal `Join` prefix, then on `=` for the primary pair; treat any additional
   `and`-joined clauses as either compound join conditions or non-join predicate qualifiers
   (join #19's `DIM_CRM_SALES_ORG.ACTIVE_IND = 'Y'` is a predicate, not a second join key — this
   distinction must be preserved, not discarded, since collapsing it would silently misrepresent
   the join).
2. Parse the `Tables (38)` section as a flat list of names; do **not** attempt to guess
   Alias-vs-Standard classification from naming convention alone in the catalog output — record
   the *hypothesis* (as done in the design inventory for the customer-table family) as a
   separate, clearly-labeled unverified column, never merged into a confirmed field.
3. Parse the `Derived Table: <name>` lines as names only; leave their SQL definition column
   `UNKNOWN` until Route B is available.
4. Parse the Connection block (`Name`, `Path`, `Server Name`, `Server Type`) as-is; do not infer
   a database engine — record it as `UNKNOWN` unless a Route B source confirms it.

### 2.2 Route B — Authoritative `.dfx` resource (not yet available)

Required to confirm: join type, cardinality, alias/standard/derived table classification (as a
structured field rather than a name list), derived-table SQL, and context definitions (though
§5 of the design inventory already confirms 0 contexts exist, which Route A alone was sufficient
to establish). Requires the Semantic Layer Java SDK or IDT — see §6.

## 3. Mapping Strategy

All six business/physical concepts map together through **shared, already-confirmed keys** —
no new identifier scheme is invented:

```text
Business Object (Cuid: CLS_*/OBJ_*/FIL_*/legacy-GUID)
      │  1:1 — every object has exactly one Select (or Where, for filters) expression
      ▼
Select / Where Expression (raw text, e.g. "SUM(FCTV_INVOICE.GL_DAR_GL_USD_AMT)")
      │  extracted via table.column pattern detection (same regex approach as
      │  `extract_lineage_candidates()` in normalization/query_panel_outline.py,
      │  reused here as a *candidate*-extraction technique, not a verified mapping)
      ▼
Alias Table reference (name only, e.g. "FCTV_INVOICE", "DIM_REC_TYPE")
      │  matched by exact name against the 38 confirmed Data Foundation table names
      ▼
Base Table or Derived Table (one of the 38 table names, or one of the 3 named derived tables)
      │  join participation confirmed via the 34-join list (e.g. FCTV_INVOICE participates
      │  in 27/34 joins)
      ▼
Join Definition (left source, right source, join expression — type/cardinality UNKNOWN)
      │  requires Route B + HANA cross-reference (per
      │  universe_lineage_acquisition_strategy.md §5) to become VERIFIED
      ▼
Physical HANA Column (not reachable from either PDF — UNKNOWN until HANA metadata is available)
```

Mapping rules to apply when this is eventually implemented:

- A Business Object maps to **one or more** table.column candidates (an expression may
  reference multiple tables, e.g. via `@Select(...)` cross-object references or multi-table
  `CASE WHEN` logic) — the mapping is one-to-many, not one-to-one.
- `@Select(FolderPath\ObjectName)` references inside an expression point to **another Business
  Object**, not directly to a table — resolve these recursively through the Business Object
  layer before reaching a table.column candidate, mirroring how the Query Panel outline parser
  already resolves `parent_object_path` via traversal rather than trusting a single field.
- A table.column candidate is only promoted from `PARSED_UNVERIFIED` to `CONFIRMED` physical
  lineage after HANA catalog cross-reference (§6); this roadmap does not skip that step.
- Alias identity (which of the 38 table names are Data-Foundation-level aliases of a shared base
  table) must be resolved from Route B, not guessed from naming similarity — the customer-table
  family hypothesis in the design inventory stays `PARSED_UNVERIFIED` until then.

## 4. Planned Catalog Files

None of these are implemented yet (no code in this change). Planned column sets:

### 4.1 `object_catalog.csv`

One row per Business Layer object (folder/dimension/attribute/measure/filter).

Columns: `cuid`, `object_type` (`class` / `dimension` / `attribute` / `measure` / `filter`, from
the BLX heading — **not** the same thing as the pipeline's existing `ObjectType` enum in
`models/common.py`, which is reserved for confirmed *semantic* typing; this column instead
records the *report heading* verbatim), `name`, `description`, `path`, `state`, `data_type`,
`projection_function` (measures only), `aggregatable` (attributes only, when present),
`filter_type` (filters only), `source_evidence_path`, `classification_status` (reusing the
`OutlineClassificationStatus`-style pattern already established for Cuid prefixes, extended with
a fourth value for the legacy GUID pattern).

### 4.2 `expression_catalog.csv`

One row per `Select` / `Where expression` found (1,904 Select + 61 Where, initially).

Columns: `cuid` (owning object), `expression_kind` (`select` / `where`), `raw_expression_text`,
`referenced_business_objects` (list of `@Select(...)` targets found, if any), `lineage_candidates`
(table.column-shaped substrings found via pattern detection — always `PARSED_UNVERIFIED`, never
promoted to `CONFIRMED` in this file), `source_evidence_path`.

### 4.3 `table_catalog.csv`

One row per Data Foundation table/derived table/view (38 + 3 + 1 = 42 initially).

Columns: `table_name`, `table_kind` (`standard` / `alias` / `derived` / `view` — `UNKNOWN` unless
Route B confirms it, **except** the 3 derived tables and 1 view, whose kind is already
CONFIRMED by name), `derived_table_sql` (`UNKNOWN` until Route B), `join_count` (computed from
§4.5, confirmed today), `source_evidence_path`.

### 4.4 `alias_catalog.csv`

One row per declared alias table (11 declared; 0 identified today).

Columns: `alias_table_name` (`UNKNOWN` until Route B for all 11 rows initially),
`aliased_base_table` (`UNKNOWN`), `evidence_status` (set to `UNKNOWN` for every row until Route
B is available — this file is expected to start **empty of confirmed rows**, not populated with
guesses).

### 4.5 `join_catalog.csv`

One row per join (34 confirmed).

Columns: `join_id` (1–34, matching the PDF's own numbering), `left_source`, `right_source`,
`join_expression` (full raw text, including compound/predicate clauses), `join_type` (`UNKNOWN`
for all 34 rows initially), `cardinality` (`UNKNOWN` for all 34 rows initially),
`source_evidence_path`.

### 4.6 `lineage_catalog.csv`

One row per Business-Object-to-candidate-table.column pair (derived from `expression_catalog.csv`
lineage candidates joined against `table_catalog.csv` table names).

Columns: `cuid`, `full_object_path`, `candidate_table_name`, `candidate_column_name`,
`join_path_used` (which `join_id`s connect the candidate table to the fact table, when
determinable from §4.5), `verification_status` (using the existing
`LineageVerificationStatus` enum: `VERIFIED` / `PARSED_UNVERIFIED` / `UNKNOWN` — every row starts
as `PARSED_UNVERIFIED` at best until HANA cross-reference), `source_evidence_path`.

## 5. Metadata Extractable Immediately From the PDF Evidence

Everything needed to populate `object_catalog.csv`, `expression_catalog.csv`, and the
CONFIRMED portions of `table_catalog.csv` and `join_catalog.csv` is already available:

- All 204 classes, 925 dimensions, 179 attributes, 785 measures with full field sets (§1.1).
- All 1,904 Select expressions and the 61 available Where expressions (§1.1).
- All 38 table names, 3 derived table names, 1 view name (§2.1).
- All 34 join expressions with left/right source and full expression text (§2.1).
- Lineage *candidates* (unverified) extractable today by applying the same
  table.column pattern-detection technique already implemented for Query Panel evidence.

## 6. Metadata Requiring IDT / Semantic Layer Java SDK / SAP HANA Metadata

| Metadata | Requires |
|---|---|
| Join type (inner/outer/left/right) for all 34 joins | IDT inspection or Semantic Layer Java SDK read of the `.dfx` |
| Cardinality for all 34 joins | IDT inspection or Semantic Layer Java SDK read of the `.dfx` |
| Alias vs. standard vs. derived classification for each of the 38 tables | IDT inspection or Semantic Layer Java SDK read of the `.dfx` |
| Derived table SQL for the 3 named derived tables | IDT inspection or Semantic Layer Java SDK read of the `.dfx` |
| The 22 undetailed filters (83 declared − 61 printed) | IDT inspection or Semantic Layer Java SDK read of the `.blx` |
| Per-parameter definitions (13 declared, 0 detailed) | IDT inspection or Semantic Layer Java SDK read of the `.blx` |
| Per-list-of-values definitions (21 declared, 0 detailed) | IDT inspection or Semantic Layer Java SDK read of the `.blx` |
| `Associated Dimension` linkage for the 179 attributes | IDT inspection or Semantic Layer Java SDK read of the `.blx` |
| Connection driver type / database engine (only a change-log comment mentions "Hana") | IDT inspection, Semantic Layer Java SDK, or CMC connection properties |
| Whether any of the 38 tables/1 view is backed by a HANA calculation view | SAP HANA `SYS.*` catalog metadata |
| Verified physical schema/table/column for any lineage candidate | SAP HANA `SYS.*` catalog metadata (read-only; never executes extracted SQL to discover lineage, per the skill's rules) |
| Resolution of the `View 0` vs. `Views (1)` discrepancy | IDT inspection (open the `.dfx` directly) |

## 7. Prioritized Implementation Work (Once Code Is Authorized)

Ordered so each step only depends on evidence already confirmed by an earlier step:

| Order | Work Item | Blocked On |
|---|---|---|
| 1 | Build `object_catalog.csv` (all 204+925+179+785 objects + 61 detailed filters) | Nothing — evidence already confirmed |
| 2 | Build `expression_catalog.csv` (1,904 Select + 61 Where, with `@Select(...)` reference parsing) | Nothing — evidence already confirmed |
| 3 | Build `table_catalog.csv` CONFIRMED rows (38 tables + 3 derived + 1 view, `table_kind=UNKNOWN` except derived/view) | Nothing — evidence already confirmed |
| 4 | Build `join_catalog.csv` (34 joins, `join_type`/`cardinality=UNKNOWN`) | Nothing — evidence already confirmed |
| 5 | Build `lineage_catalog.csv` at `PARSED_UNVERIFIED` level only (candidate table.column pairs from expression parsing) | Steps 2–4 |
| 6 | Acquire one sanitized Route-B sample (`.blx`/`.dfx` export or Java SDK read) covering ≥1 object, ≥1 join, ≥1 alias table | Per `integration_readiness_plan.md` §5 manual validation procedure |
| 7 | Build `alias_catalog.csv` (currently 0 confirmed rows possible) | Step 6 |
| 8 | Backfill `join_type`/`cardinality` in `join_catalog.csv` | Step 6 |
| 9 | Resolve the 22-filter and `View 0`/`Views (1)` discrepancies | Step 6 (IDT inspection) |
| 10 | Verify `lineage_catalog.csv` candidates against SAP HANA `SYS.*` metadata, promoting rows from `PARSED_UNVERIFIED` to `VERIFIED` | Step 5 + a confirmed, read-only HANA connection (per `universe_lineage_acquisition_strategy.md` §5) |

## 8. Non-Goals of This Document

No extraction code, parsers, or catalog-generation scripts are implemented here. This roadmap
only sequences and specifies the work already made possible by
[dm_invoice_data_mart_design_inventory.md](dm_invoice_data_mart_design_inventory.md) and
[universe_lineage_acquisition_strategy.md](universe_lineage_acquisition_strategy.md).
