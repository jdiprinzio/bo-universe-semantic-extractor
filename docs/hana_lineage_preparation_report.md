# HANA Lineage Preparation Report — DM_Invoice_Data_Mart.unx

**Status:** Analysis report only. **No connection to SAP HANA was made or attempted.** Every
finding below is derived exclusively from the five catalogs already generated in
`output/DM_Invoice_Data_Mart/` (`object_catalog.csv`, `expression_catalog.csv`,
`table_catalog.csv`, `join_catalog.csv`, `lineage_catalog.csv`) — themselves derived only from
the BLX/DFX design PDFs. Nothing here is a verified HANA mapping.

## 1. Unique Table References Across Select/Where/Join Expressions

Every candidate reference was extracted using the pattern-detection technique already
implemented in `normalization/lineage_catalog.py` (`extract_table_column_candidates`),
applied separately to:

- `select_expression` values in `expression_catalog.csv` (1,950 rows)
- `where_expression` values in `expression_catalog.csv` (the 61 filter rows)
- `left_object` / `right_object` values in `join_catalog.csv` (34 rows)

| Source | Rows scanned | Unique table names contributing a reference |
|---|---|---|
| Select expressions | 1,950 | 41 |
| Where expressions | 61 | 6 |
| Join expressions | 34 | 33 |
| **Union (all sources)** | — | **45** |

**Known limitation (confirmed by direct inspection, not guessed):** the pattern detector only
matches an *unquoted* `TABLE.COLUMN` shape. At least two confirmed Data Foundation objects
(`DATE_PERCENTAGE`, a Derived Table, and the `Master` View) are referenced in expressions only
via a double-quoted form (`"DATE_PERCENTAGE"."PCT_COMP_MONTH"`), which this detector does not
match. Their `total_reference_count` of `0` in the inventory below therefore means "not detected
by this pattern," not "unused" — see §6.

## 2. Deduplicated Reference List — Schemas, Tables, Views, Calculation-View Candidates

### 2.1 Schemas

**None found.** No reference in any Select, Where, or join expression is schema-qualified
(zero references contain more than one `.`). The Data Foundation's Connection block
(`table_catalog.csv` source evidence) likewise carries no schema field — only a connection
name (`HOCTST`) and server name (`@BODRNC`). Schema is `UNKNOWN` for every object in this
report.

### 2.2 Tables (35 unique names)

Every name declared as a plain `Table:` entry in the Data Foundation (`table_catalog.csv`,
`table_type=UNKNOWN`) and confirmed to be referenced by at least the Data Foundation itself.
Full list in `catalogs/hana_object_inventory.csv` (`classification=CONFIRMED_TABLE`).

### 2.3 Views (1 unique name)

`Master` — the sole Data Foundation View. Zero direct pattern-matched references were found
(see the quoting limitation in §1); its existence is otherwise CONFIRMED.

### 2.4 Calculation-View Candidates (3 unique names)

The 3 Data Foundation Derived Tables (`DATE_PERCENTAGE`, `TODAY_COST (DIM_PROD_COST)`,
`WORK_DAYS`) are the only objects in this evidence set that *could* wrap a HANA calculation
view — IDT Derived Tables execute custom SQL, which may itself reference a calc view. This is a
**hypothesis**, not a confirmed fact: the design inventory already established that no Derived
Table's underlying SQL was extractable from the PDF text (rendered as a graphical SQL editor
snapshot). They are therefore classified `POSSIBLE_CALCULATION_VIEW`, never `CONFIRMED_VIEW`.

## 3. Classification

All 45 unique references, classified per the rules below (see full detail in
`catalogs/hana_object_inventory.csv`):

| Classification | Count | Rule |
|---|---|---|
| `CONFIRMED_TABLE` | 35 | Declared as a plain `Table:` entry in the Data Foundation |
| `CONFIRMED_VIEW` | 1 | Declared as a `View:` entry in the Data Foundation (`Master`) |
| `POSSIBLE_CALCULATION_VIEW` | 3 | Declared as a `Derived Table:` entry — underlying SQL unknown, could reference a calc view |
| `UNKNOWN` | 6 | Referenced in a Select/Where expression but **not** declared anywhere in the Data Foundation's Tables/Joins sections |

No reference was classified from name pattern alone (e.g. no assumption that `LKUP_*` implies
"lookup table" beyond reporting the literal name) — classification uses only the presence/type
recorded in `table_catalog.csv`.

## 4. HANA Metadata Acquisition Plan

This plan sequences read-only HANA catalog work; **no step here has been executed.**

1. **Confirm the target schema(s).** No schema name is present anywhere in the BLX/DFX
   evidence. Obtain this from whoever administers the `HOCTST` connection (CMC connection
   properties) or a HANA DBA — do not guess a schema name.
2. **Confirm read-only role/grants.** A HANA database user with `SELECT` on `SYS.TABLES`,
   `SYS.VIEWS`, `SYS.TABLE_COLUMNS`, and (if available) `SYS.CALC_VIEW_DEFINITIONS`-equivalent
   catalog views only — no access to underlying business data is required for this stage.
3. **Existence check (Priority 1).** For each of the 39 `CONFIRMED_TABLE`/`CONFIRMED_VIEW`
   names, confirm a matching object exists in the target schema. This resolves the
   `CONFIRMED_TABLE` vs. real "standard/alias" ambiguity only partially — alias identity still
   requires Data Foundation Route B (per `universe_lineage_acquisition_strategy.md`), not HANA.
4. **Calculation-view check (Priority 2).** For each of the 3 `POSSIBLE_CALCULATION_VIEW`
   names, check whether a same/similar-named calculation view exists; if not, check whether the
   name matches a column-view or plain table instead.
5. **Orphan resolution (Priority 3).** For each of the 5 genuine orphan names (§6), search the
   target schema(s) for an exact or near-name match. If none is found, escalate to the business
   owner — these may belong to a different connection/schema entirely (e.g. a separate
   "Forecast" data source not captured in this Data Foundation export).
6. **Column-level verification (Priority 4, only after 3–5).** For each `(table, column)` pair
   in `lineage_catalog.csv`, confirm the column exists on the now-verified table, using
   `SYS.TABLE_COLUMNS`. Only then may a `lineage_catalog.csv` row move from
   `PARSED_UNVERIFIED`/`UNKNOWN` to `VERIFIED` (per the existing `LineageVerificationStatus`
   enum in `src/bo_semantic_extractor/models/common.py`).

## 5. `catalogs/hana_object_inventory.csv`

Generated alongside this report. Columns: `reference_name`, `classification`,
`declared_in_data_foundation` (`YES`/`NO`), `select_reference_count`, `where_reference_count`,
`join_reference_count`, `total_reference_count`, `notes`. 45 rows, sorted by
`total_reference_count` descending.

## 6. Highest-Referenced Objects, Orphans, and Unresolved Aliases

### 6.1 Highest-referenced tables (by total reference count)

| Rank | Table | Total | Select | Where | Join |
|---|---|---|---|---|---|
| 1 | `FCTV_INVOICE` | 1,224 | 1,178 | 18 | 28 |
| 2 | `DIM_SALES_ORDER` | 404 | 397 | 4 | 3 |
| 3 | `DIM_PROD_COST` | 221 | 220 | 0 | 1 |
| 4 | `DIM_REC_TYPE` | 106 | 60 | 45 | 1 |
| 5 | `DIM_PROD_MASTER` | 91 | 87 | 0 | 4 |

`FCTV_INVOICE` is confirmed (independently of this ranking) as the central fact table — it also
participates in 28 of the 34 confirmed joins.

### 6.2 Highest-referenced views

**None with a detected reference.** `Master` (the only declared view) shows a
`total_reference_count` of `0` due to the quoted-identifier detection limitation in §1 — this is
a tooling gap, not evidence that the view is unused.

### 6.3 Orphan references (5)

Referenced directly in a Select expression but **not declared anywhere** in the Data
Foundation's Tables/Joins sections:

| Reference | Context (first observed use) |
|---|---|
| `DIM_DIVISION` | Dimension "Div Id": `DIM_DIVISION.DIV_ID` |
| `LKUP_FORECAST_TOTAL` | Measure "MTD-Forecast-Total": `...LKUP_FORECAST_TOTAL.FORECAST_AMT...` |
| `LKUP_FORECAST_DIV` | Measure "MTD-Forecast-ByDivGrp": `...LKUP_FORECAST_DIV.FORECAST_AMT...` |
| `LKUP_FORECAST_PROD` | Measure "MTD-Forecast-ByProdLineGrp": `...LKUP_FORECAST_PROD.FORECAST_AMT...` |
| `STAGE_FORECAST_PROD` | Measure "Forecast Amt-By Prod Line Grp Code": `STAGE_FORECAST_PROD.FORECAST_AMT` |

All five follow a plausible naming convention (`DIM_*`, `LKUP_*`, `STAGE_*`) consistent with the
rest of this Data Foundation, but none appear in the 39 declared table/view/derived-table
entries. **Hypothesis only (not confirmed):** these may belong to a separate Forecast-specific
data source not captured in `DM_Invoice_Data_Mart.dfx`, or the DFX export may be incomplete.
Resolving this requires IDT inspection or HANA existence checks (§4, step 5) — not a guess.

### 6.4 Unresolved aliases (1)

| Alias | Resolves to (evidence) | Context |
|---|---|---|
| `D` | `DIM_DATE1` (a `CONFIRMED_TABLE`) | Appears only inside a correlated subquery: `(SELECT MAX(D.CLNDR_DT) FROM DIM_DATE1 D WHERE D.SRC_SYS_ID='JDEDOM' AND D.ORD_INPUT_DT=@Select(Prompts\Ending Date))` — `D` is a local SQL alias for `DIM_DATE1`, not a separate physical object. |

This is the only local SQL alias detected by inspection of the underlying expressions; it is
listed separately from the 5 genuine orphans in §6.3 because its target table is already
confirmed, unlike the orphans.

## 7. SQL Templates for Future SYS Catalog Discovery (Not Executed)

The following are **templates only** — every placeholder (`<SCHEMA_NAME>`) must be filled in
after §4 step 1 is complete. **None of these have been run against any HANA system.**

```sql
-- Template 1: Confirm existence of every CONFIRMED_TABLE / CONFIRMED_VIEW name.
-- Populate the IN (...) list from catalogs/hana_object_inventory.csv
-- where classification IN ('CONFIRMED_TABLE', 'CONFIRMED_VIEW').
SELECT SCHEMA_NAME, TABLE_NAME, TABLE_TYPE
FROM SYS.TABLES
WHERE SCHEMA_NAME = '<SCHEMA_NAME>'
  AND TABLE_NAME IN (
    'FCTV_INVOICE', 'DIM_SALES_ORDER', 'DIM_PROD_COST', 'DIM_REC_TYPE', 'DIM_PROD_MASTER'
    -- ... remaining CONFIRMED_TABLE names from catalogs/hana_object_inventory.csv
  );

SELECT SCHEMA_NAME, VIEW_NAME
FROM SYS.VIEWS
WHERE SCHEMA_NAME = '<SCHEMA_NAME>'
  AND VIEW_NAME IN ('Master');

-- Template 2: Check whether POSSIBLE_CALCULATION_VIEW names exist as calculation views,
-- plain views, or tables (do not assume which; check all three).
SELECT SCHEMA_NAME, VIEW_NAME
FROM SYS.VIEWS
WHERE SCHEMA_NAME = '<SCHEMA_NAME>'
  AND VIEW_NAME IN ('DATE_PERCENTAGE', 'TODAY_COST (DIM_PROD_COST)', 'WORK_DAYS');

SELECT SCHEMA_NAME, TABLE_NAME
FROM SYS.TABLES
WHERE SCHEMA_NAME = '<SCHEMA_NAME>'
  AND TABLE_NAME IN ('DATE_PERCENTAGE', 'TODAY_COST (DIM_PROD_COST)', 'WORK_DAYS');

-- Template 3: Search for the 5 orphan references across all accessible schemas
-- (do not assume <SCHEMA_NAME> from Template 1 is the only candidate schema).
SELECT SCHEMA_NAME, TABLE_NAME, 'TABLE' AS OBJECT_KIND
FROM SYS.TABLES
WHERE TABLE_NAME IN (
    'DIM_DIVISION', 'LKUP_FORECAST_DIV', 'LKUP_FORECAST_PROD',
    'LKUP_FORECAST_TOTAL', 'STAGE_FORECAST_PROD'
)
UNION ALL
SELECT SCHEMA_NAME, VIEW_NAME, 'VIEW' AS OBJECT_KIND
FROM SYS.VIEWS
WHERE VIEW_NAME IN (
    'DIM_DIVISION', 'LKUP_FORECAST_DIV', 'LKUP_FORECAST_PROD',
    'LKUP_FORECAST_TOTAL', 'STAGE_FORECAST_PROD'
);

-- Template 4: Column-level verification, only after Templates 1-3 confirm a table exists.
-- Populate TABLE_NAME/COLUMN_NAME pairs from lineage_catalog.csv one table at a time.
SELECT SCHEMA_NAME, TABLE_NAME, COLUMN_NAME, DATA_TYPE_NAME, IS_NULLABLE
FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME = '<SCHEMA_NAME>'
  AND TABLE_NAME = '<CONFIRMED_TABLE_NAME>'
  AND COLUMN_NAME IN ('<COLUMN_1>', '<COLUMN_2>');
```

## 8. Non-Goals of This Document

No HANA connection was opened; no SQL above was executed; no HANA mapping was fabricated for
any of the 45 references. `catalogs/hana_object_inventory.csv` and this report only reorganize
facts already present in the five existing catalogs, plus explicit, evidence-quoted hypotheses
clearly labeled as such.
