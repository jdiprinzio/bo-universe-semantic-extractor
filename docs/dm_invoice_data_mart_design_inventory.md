# DM_Invoice_Data_Mart.unx — Design Artifact Inventory

**Status:** Analysis report only. No code is added or changed by this document. Every item
below is classified `CONFIRMED`, `PARSED_UNVERIFIED`, or `UNKNOWN` based strictly on what is
present in the two supplied PDFs — nothing is inferred beyond their text content.

## 0. Evidence and Extraction Method

Source documents:

- `docs/evidence/DM_Invoice_Data_Mart_blx.pdf` — Business Layer design report (711 pages).
- `docs/evidence/DM_Invoice_Data_Mart_dfx.pdf` — Data Foundation design report (71 pages).

Both are Apache FOP-generated IDT "print universe/business layer/data foundation" reports (text
+ some graphical/icon elements). Text was extracted with `pypdf` for analysis; **graphical
elements (icons indicating join type, cardinality, alias vs. standard table, connection driver
logo, etc.) are not recoverable as text** and are marked `UNKNOWN` below rather than guessed.
This extraction method itself is out of scope for the pipeline (no code was added) — it was used
only to read the PDFs for this report.

## 1. Business Layer Inventory

The Business Layer's own "General Information → Statistics" block states:

| Declared (Statistics block) | Count | Status |
|---|---|---|
| Folders | 204 | CONFIRMED |
| Business Layer Views | 0 | CONFIRMED |
| Dimensions | 925 | CONFIRMED |
| Attributes | 179 | CONFIRMED |
| Measures | 785 | CONFIRMED |
| Filters | 83 | CONFIRMED (as a *declared* statistic — see discrepancy below) |
| Queries | 0 | CONFIRMED |
| Lists of Values | 21 | CONFIRMED (declared count only — no per-LOV detail found; see §1.6) |
| Parameters | 13 | CONFIRMED (declared count only — no per-parameter detail found; see §1.6) |
| Navigation Paths | 15 | CONFIRMED (declared count; 17 literal "Navigation Path" text occurrences found — see discrepancy below) |

Cross-checking the declared statistics against the actual number of detailed object blocks
printed in the report body:

| Object type | Detailed blocks found in body | Matches declared statistic? |
|---|---|---|
| Folders (`Folder:` heading) | 204 | Yes — exact match |
| Dimensions (`Dimension:` heading) | 925 | Yes — exact match |
| Attributes (`Attribute:` heading) | 179 | Yes — exact match |
| Measures (`Measure:` heading) | 785 | Yes — exact match |
| Filters (`Filter:` heading) | 61 | **No — 22 fewer than the declared 83** |

**Discrepancy (CONFIRMED to exist, cause UNKNOWN):** the Statistics block declares 83 filters,
but only 61 `Filter:` detail blocks are printed in the report body. The report does not state
why (e.g. hidden/inactive filters excluded from the printed body is a plausible but **unverified**
explanation — not asserted here as fact).

### 1.1 Classes (Folders)

204 `Folder:` blocks, each with `Name`, `Cuid` (`CLS_*` pattern in 203 of 204 cases — see §1.7),
`Translation ID`, `Path`, `State` (`Active` / `Hidden` observed). CONFIRMED.

### 1.2 Dimensions

925 `Dimension:` blocks, each with `Name`, `Description`, `Cuid` (`OBJ_*` pattern in most cases),
`Translation ID`, `Path`, `State`, `Data Type` (`String` / `Numeric` / `DateTime` observed),
`SQL Definition` → `Select <expression>`, and an `Advanced` block (`Minimum Object Level
Security`, `Data Sensitivity Category`, `List of Values` usage mode, `Can be used in...`).
CONFIRMED.

### 1.3 Attributes

179 `Attribute:` blocks — same shape as Dimensions, plus an occasional `Aggregatable` boolean
field observed (e.g. `Attribute: Profit Center Desc - MM` → `Aggregatable True`). No
`Associated Dimension` field was found anywhere in the extracted text for any attribute — the
formal parent-dimension linkage for attributes is `UNKNOWN` (only the shared folder `Path`
groups an attribute near its dimension, which is a naming/organizational convention, not a
confirmed structural association field).

### 1.4 Measures

785 `Measure:` blocks, each with `Name`, `Description`, `Cuid` (`OBJ_*` pattern), `Translation
ID`, `Path`, `State`, `Data Type` (all `Numeric` in the sampled set), `Projection Function`,
`High Precision` (boolean), `SQL Definition` → `Select <expression>`, and the same `Advanced`
block as Dimensions. CONFIRMED.

### 1.5 Filters

61 `Filter:` blocks found in the body (declared statistic: 83 — see discrepancy above). Each
block has `Name`, `Description`, `Cuid` (`FIL_*` pattern), `Translation ID`, `Path`, `State`,
`Filter type` (only value observed: `NATIVE`, 61/61), and `Where expression <text>`. CONFIRMED
for the 61 printed filters; the remaining ~22 declared-but-not-printed filters are `UNKNOWN`.

### 1.6 Prompts / Parameters / Lists of Values

- A `Folder: Prompts` and `Folder: Forecast Prompts` exist and are referenced by name inside
  several filter/measure expressions (e.g. `@Select(Prompts\DerivedValues\Ending Week)`,
  `@Prompt(Enter Days)`, `@Prompt(BusinessSegment)`). CONFIRMED that prompts exist and are
  referenced by name.
- **No dedicated `Parameter:` detail heading was found anywhere in the extracted text**, despite
  the Statistics block declaring 13 Parameters. Individual parameter definitions (question text,
  data type, list of values source) are `UNKNOWN` from this document.
- **No dedicated List-of-Values detail heading was found.** The phrase `List of Values` appears
  only as a per-object property (e.g. `List of Values Editable`, `List of Values Allow user to
  search values in the database`), never as a named, standalone LOV definition. The 21 declared
  Lists of Values are `UNKNOWN` individually — only their existence as a declared count is
  CONFIRMED.
- Navigation Paths: 15 declared; `Navigation Path:` text appears 17 times in the body (each
  navigation path prints a name, a `\`-delimited path, and a short description). The 2-occurrence
  gap is `UNKNOWN` in cause; the printed navigation paths themselves are CONFIRMED.

### 1.7 Identifier Pattern Note (Business Layer)

Cuid values across all Business Layer objects fall into these patterns:

| Prefix pattern | Count | Object types observed |
|---|---|---|
| `CLS_*` | 203 | Folders (Classes) |
| `OBJ_*` | 1,862 | Dimensions, Attributes, Measures |
| `FIL_*` | 59 | Filters |
| Non-underscore, GUID-like (e.g. `_oJoHABahEfCdaK68k8v0jw`) | 32 | Observed on at least one Folder, one Dimension, and one Attribute in sampled contexts |

CONFIRMED that a fourth, GUID-style identifier pattern exists for at least 32 objects, in
addition to the `CLS_*` / `OBJ_*` / `FIL_*` patterns already established from the Query Panel
outline evidence (`docs/businessobjects_api_requirements.md`). This is a **new, confirmed**
finding not previously documented: not every Business Layer object uses the `CLS_*`/`OBJ_*`
naming convention — a legacy/internal GUID form also exists. The two ID schemes' exact
relationship (e.g. whether the GUID is a pre-migration `.unv` artifact) is `UNKNOWN`.

## 2. Business Layer Expressions

### 2.1 Select Expressions

1,904 `Select <expression>` occurrences found (one per Dimension/Attribute/Measure, and
additional ones embedded inside Filter `Where expression` text via `@Select(...)` references).
CONFIRMED. Expressions range from a bare column reference (`DIM_DATE.CLNDR_DT`) to complex
conditional aggregates, e.g.:

```text
SUM(Case When @Select(Date Dimension\FinanceYear) = @Select(Prompts\DerivedValues\Ending Year)
     and @Select(Date Dimension\Order Input Date)<=@Select(Prompts\Ending Date)
     Then FCTV_INVOICE.NET_PRICE_LC_AMT - FCTV_INVOICE.SHIP_CUR_CONTR_COST_LC_AMT Else 0 End)
```

`@Select(...)` cross-references to other business objects (by folder path) are CONFIRMED to be
a widely used pattern (dozens of occurrences) — these are business-layer-internal references,
not physical table/column references, and must not be conflated with them.

### 2.2 Where Expressions

**Only Filters carry an explicit, separately labeled `Where expression` field** (61 confirmed
instances, one per printed filter — see §1.5 for the full list of filter name → where-expression
pairs). No Dimension, Attribute, or Measure in this report has a distinct "Where" field; any
conditional logic for those object types is embedded inline inside their own `Select` expression
(via `CASE WHEN ... THEN ... ELSE ... END`). This is a confirmed structural fact worth encoding
into the pipeline's normalization logic later: `where_expression` should be populated only for
filter-classified objects, never invented for dimensions/attributes/measures.

### 2.3 Projection Metadata

Every Measure has a `Projection Function` field (785/785). Observed distinct values:

| Value | Count |
|---|---|
| `Sum` | 737 |
| `None` | 26 |
| `Max` | 22 |

CONFIRMED. No `Min`, `Average`, or `Count` projection function was observed in this document
(their absence here does not mean they cannot occur elsewhere — only that they were not found in
this specific universe's export).

### 2.4 Aggregation Metadata

**The literal field label `Aggregate Function` does not appear anywhere in the Business Layer
report.** The IDT concept commonly referred to as "aggregation function" is represented in this
export exclusively via the `Projection Function` field on Measures (§2.3). Separately, a
boolean `Aggregatable` property was observed on at least one Attribute
(`Profit Center Desc - MM` → `Aggregatable True`), which is a different, attribute-level flag,
not a measure aggregation function. Both facts are CONFIRMED; do not assume a distinct
"Aggregate Function" field exists when modeling this data.

## 3. Data Foundation Inventory

From the Data Foundation's own "General Information → Statistics" block (all CONFIRMED,
declared values):

| Declared (Statistics block) | Count |
|---|---|
| Table | 38 |
| Alias Table | 11 |
| Derived Table | 3 |
| Standard Table | 24 |
| Join | 34 |
| Context | 0 |
| View | 0 (see discrepancy below) |
| List of Values | 0 |
| Parameter | 0 |

**Discrepancy (CONFIRMED to exist, cause UNKNOWN):** the Statistics block declares `View 0`, but
the report body later contains a `Views (1)` section listing `View: Master`. Both values are
verbatim from the document; the contradiction itself is CONFIRMED, its cause is `UNKNOWN`.

### 3.1 Tables

38 tables are listed under `Tables (38)`, each as `Table: <NAME>` (e.g. `DIM_ADDR`, `DIM_CUST`,
`FCTV_INVOICE`, `DIM_PROD_MASTER`, `ULTIMATE_CUSTOMER`, `PAYER_CUST`, `CHANNEL_CUSTOMER`,
`ENDUSER_CUSTOMER`, `VAR_CUSTOMER`, `DIM_BILL_TO_CUST`, and 28 others). CONFIRMED that these 38
names exist as Data Foundation tables.

**Which of the 38 are "Standard Table" (24 declared) vs. "Alias Table" (11 declared) is
`UNKNOWN`** — the extracted text lists every table under one flat `Tables (38)` heading with no
per-table type label (the Standard/Alias distinction is rendered as an icon in the original PDF,
not as text). Based on naming *pattern only* (not a confirmed field), `ULTIMATE_CUSTOMER`,
`PAYER_CUST`, `CHANNEL_CUSTOMER`, `ENDUSER_CUSTOMER`, `VAR_CUSTOMER`, and `DIM_BILL_TO_CUST` are
plausible aliases of a shared customer table (`DIM_CUST` / `DIM_SHIP_CUST` families appear
separately) — this is explicitly a **PARSED_UNVERIFIED** hypothesis, not a confirmed alias
mapping.

### 3.2 Views

Statistics block says 0; body lists exactly one: `View: Master`. Existence of a view named
`Master` is CONFIRMED (it is printed); its column list / underlying definition is `UNKNOWN` (not
present in the extracted text).

### 3.3 Calculation Views

**No table, alias, or view name in either document is explicitly labeled "Calculation View."**
Whether any of the 38 tables (or the `Master` view) is backed by a HANA calculation view rather
than a base table is `UNKNOWN` from these PDFs alone — per
`docs/universe_lineage_acquisition_strategy.md` §5, this requires SAP HANA catalog
cross-reference, not the Data Foundation report.

### 3.4 Aliases

11 Alias Tables are declared in Statistics. **Zero are individually identified as aliases in the
extracted text** (see §3.1) — count is CONFIRMED, individual identity is `UNKNOWN`.

### 3.5 Derived Tables

3 Derived Tables are declared and named in the body: `TODAY_COST (DIM_PROD_COST)`,
`DATE_PERCENTAGE`, `WORK_DAYS`. CONFIRMED that these three exist and are labeled "Derived
Table." **Their underlying custom SQL definitions were not present in the extracted text**
(likely rendered as a graphical SQL-editor snapshot in the PDF) — `UNKNOWN`.

## 4. Join Inventory

34 joins declared and printed, each as a single expression line, e.g.:

```text
Join DIM_PROD_LINE.PROD_LINE_KEY=FCTV_INVOICE.PROD_LINE_KEY
Join DIM_DATE.DT_KEY=FCTV_INVOICE.GL_DT_KEY and DIM_DATE.CLNDR_YEAR_QTR_NBR=FCTV_INVOICE.CLNDR_YEAR_QTR_NBR
Join FCTV_INVOICE.CRM_SALES_ORG_KEY=DIM_CRM_SALES_ORG.CRM_SALES_ORG_KEY and DIM_CRM_SALES_ORG.ACTIVE_IND = 'Y'
```

| Field | Status | Notes |
|---|---|---|
| Left source | CONFIRMED | The table/alias name on the left of `=` (or first clause) is readable for all 34 joins. |
| Right source | CONFIRMED | Same, right side of `=`. |
| Join expression | CONFIRMED | Full expression text captured for all 34, including two joins with compound (`and`) conditions and one (#19) with an additional non-join filter clause (`DIM_CRM_SALES_ORG.ACTIVE_IND = 'Y'`). |
| Join type | `UNKNOWN` | Inner/outer/left/right join type is rendered as an icon in the PDF, not text. Not one of the 34 join lines states a type in words. |
| Cardinality | `UNKNOWN` | Cardinality (e.g. 1-1, 1-n, n-n) is rendered graphically; no cardinality text was found anywhere in the Data Foundation extracted text. |

All 34 joins are listed in the appendix table below for completeness (left source / right source
/ full expression only — type and cardinality omitted as `UNKNOWN` for every row):

| # | Left source | Right source | Join expression |
|---|---|---|---|
| 1 | DIM_PROD_LINE | FCTV_INVOICE | `DIM_PROD_LINE.PROD_LINE_KEY=FCTV_INVOICE.PROD_LINE_KEY` |
| 2 | FCTV_INVOICE | DIM_PROD_MASTER | `FCTV_INVOICE.PROD_MASTER_KEY=DIM_PROD_MASTER.PROD_MASTER_KEY` |
| 3 | FCTV_INVOICE | DIM_SALES_ORG | `FCTV_INVOICE.SALES_ORG_KEY=DIM_SALES_ORG.SALES_ORG_KEY` |
| 4 | DIM_SOURCE_PLANT | FCTV_INVOICE | `DIM_SOURCE_PLANT.SRC_PLANT_KEY=FCTV_INVOICE.SRC_PLANT_KEY` |
| 5 | FCTV_INVOICE | DIM_REGION_COUNTRY | `FCTV_INVOICE.REGION_COUNTRY_KEY=DIM_REGION_COUNTRY.REGION_COUNTRY_KEY` |
| 6 | FCTV_INVOICE | DIM_DISTR_CHANNEL | `FCTV_INVOICE.DISTR_CHANNEL_KEY=DIM_DISTR_CHANNEL.DISTR_CHANNEL_KEY` |
| 7 | FCTV_INVOICE | DIM_INVOICE | `FCTV_INVOICE.INV_KEY=DIM_INVOICE.INV_KEY` |
| 8 | DIM_SALES_ORDER | FCTV_INVOICE | `DIM_SALES_ORDER.SALES_ORD_KEY=FCTV_INVOICE.SALES_ORD_KEY` |
| 9 | FCTV_INVOICE | DIM_CUR_RATE | `FCTV_INVOICE.CUR_RATE_KEY=DIM_CUR_RATE.CUR_RATE_KEY` |
| 10 | FCTV_INVOICE | DIM_CUST | `FCTV_INVOICE.SOLD_CUST_KEY=DIM_CUST.CUST_KEY` |
| 11 | FCTV_INVOICE | DIM_ADDR | `FCTV_INVOICE.SHIP_ADDR_KEY=DIM_ADDR.ADDR_KEY` |
| 12 | DIM_REC_TYPE | FCTV_INVOICE | `DIM_REC_TYPE.REC_TYPE_KEY=FCTV_INVOICE.REC_TYPE_KEY` |
| 13 | FCTV_INVOICE | DIM_SHIP_CUST | `FCTV_INVOICE.SHIP_CUST_KEY=DIM_SHIP_CUST.CUST_KEY` |
| 14 | DIM_PROD_MASTER | "TODAY_COST (DIM_PROD_COST)" | `DIM_PROD_MASTER.PROD_MASTER_KEY="TODAY_COST (DIM_PROD_COST)".PROD_MASTER_KEY` |
| 15 | DIM_DATE | FCTV_INVOICE | `DIM_DATE.DT_KEY=FCTV_INVOICE.GL_DT_KEY and DIM_DATE.CLNDR_YEAR_QTR_NBR=FCTV_INVOICE.CLNDR_YEAR_QTR_NBR` |
| 16 | DIM_REGION_COUNTRY_SALES | DIM_SALES_ORDER | `DIM_REGION_COUNTRY_SALES.COUNTRY_ID=DIM_SALES_ORDER.FINAL_DEST_COUNTRY_CODE` |
| 17 | DIM_INVOICE | DIM_REGION_COUNTRY_INV | `DIM_INVOICE.FINAL_DEST_COUNTRY_CODE=DIM_REGION_COUNTRY_INV.COUNTRY_ID` |
| 18 | FCTV_INVOICE | DIM_PROD_COST | `FCTV_INVOICE.PROD_COST_KEY=DIM_PROD_COST.PROD_MASTER_COST_KEY` |
| 19 | FCTV_INVOICE | DIM_CRM_SALES_ORG | `FCTV_INVOICE.CRM_SALES_ORG_KEY=DIM_CRM_SALES_ORG.CRM_SALES_ORG_KEY and DIM_CRM_SALES_ORG.ACTIVE_IND = 'Y'` |
| 20 | FCTV_INVOICE | DIM_CRM_PARTNER | `FCTV_INVOICE.PARTNER_KEY=DIM_CRM_PARTNER.PARTNER_KEY` |
| 21 | FCTV_INVOICE | ULTIMATE_CUSTOMER | `FCTV_INVOICE.ULTIMATE_CUSTOMER_KEY=ULTIMATE_CUSTOMER.CUST_KEY` |
| 22 | FCTV_INVOICE | PAYER_CUST | `FCTV_INVOICE.PAYER_CUST_KEY=PAYER_CUST.CUST_KEY` |
| 23 | IA_VBAP_FEATURE | FCTV_INVOICE | `IA_VBAP_FEATURE.SALES_ORD_LKUP_ID=FCTV_INVOICE.SALES_ORD_LKUP_ID` |
| 24 | DIM_PROGRAM_MANAGER | DIM_SALES_ORDER | `DIM_PROGRAM_MANAGER.EMPLOYEE=DIM_SALES_ORDER.PROGRAM_MGR_ID` |
| 25 | FCTV_INVOICE | DIM_PO | `FCTV_INVOICE.PO_KEY=DIM_PO.PO_KEY` |
| 26 | FCTV_INVOICE | DIM_GL_ENTRY_NONBILL | `FCTV_INVOICE.GL_ENTRY_KEY=DIM_GL_ENTRY_NONBILL.GL_ENTRY_KEY` |
| 27 | FCTV_INVOICE | DIM_COMPANY | `FCTV_INVOICE.CO_KEY=DIM_COMPANY.CO_KEY` |
| 28 | FCTV_INVOICE | CHANNEL_CUSTOMER | `FCTV_INVOICE.CHANNEL_CUST_KEY=CHANNEL_CUSTOMER.CUST_KEY` |
| 29 | FCTV_INVOICE | ENDUSER_CUSTOMER | `FCTV_INVOICE.EU_PARTNER_KEY=ENDUSER_CUSTOMER.CUST_KEY` |
| 30 | FCTV_INVOICE | VAR_CUSTOMER | `FCTV_INVOICE.VAR_PARTNER_KEY=VAR_CUSTOMER.CUST_KEY` |
| 31 | DIM_BILL_TO_CUST | FCTV_INVOICE | `DIM_BILL_TO_CUST.CUST_KEY=FCTV_INVOICE.BILL_TO_CUST_KEY` |
| 32 | DIM_PROD_MASTER | DIM_PROD_COST_TODAY | `DIM_PROD_MASTER.PROD_MASTER_KEY=DIM_PROD_COST_TODAY.PROD_MASTER_KEY` |
| 33 | FCTV_INVOICE | DIM_OPPORTUNITY | `FCTV_INVOICE.OPPTY_KEY=DIM_OPPORTUNITY.OPPTY_KEY` |
| 34 | "IA_OPERATIONS_CHARACTERISTICS" | DIM_PROD_MASTER | `"IA_OPERATIONS_CHARACTERISTICS".PROD_LONG_ID=DIM_PROD_MASTER.PROD_LONG_ID` |

`FCTV_INVOICE` (the fact table) participates in 27 of the 34 joins, confirming it is the central
fact table for this Data Foundation — CONFIRMED from join-participation counting, not asserted
elsewhere in the document.

## 5. Context Inventory

The Data Foundation Statistics block states `Context 0`, and the body's `Contexts (0)` section is
empty. **CONFIRMED: this Data Foundation defines zero contexts.** There is therefore no
join-path disambiguation mechanism for multi-fact scenarios in this universe as currently
designed (or, if one is needed, it is not implemented via IDT Contexts).

## 6. Connection Inventory

| Field | Value | Status |
|---|---|---|
| Connection name | `HOCTST` | CONFIRMED (`Name HOCTST`) |
| Connection path | `//HOCTST.cnx` | CONFIRMED |
| Server name | `@BODRNC` | CONFIRMED |
| Server type | `Cms` | CONFIRMED (this labels the connection as CMS-secured/published; it is **not** a database driver or engine name) |
| Driver type | — | `UNKNOWN` — no driver name/version field was found in the extracted Data Foundation text |
| Database type | "Hana" (implied) | **PARSED_UNVERIFIED** — not present in the Data Foundation's Connection block at all; the only textual evidence is a narrative change-log entry in the Business Layer document ("...Convert .unv universe(connect to Oracle DB) to .unx (connect to Hana DB)..."), which is a historical comment, not a structured connection-metadata field |

## 7. First Lineage Graph

Two concrete, fully-sourced example chains (both grounded only in text confirmed present in the
two PDFs):

### 7.1 Example: Filter → Fact Table Column

```text
Business Object            Filter "ExternalSales" (FIL_1)                      CONFIRMED
      │
      ▼
Business Layer Expression   Where expression: DIM_REC_TYPE.GROSS_SALE_IND = 'Y' CONFIRMED
      │
      ▼
Data Foundation Alias       "DIM_REC_TYPE" (Data Foundation table name;         PARSED_UNVERIFIED
                            Alias vs. Standard status not labeled in text)      (existence CONFIRMED,
                                                                                  alias/standard UNKNOWN)
      │
      ▼
Physical Source Object      Column GROSS_SALE_IND on DIM_REC_TYPE               UNKNOWN
                            (physical schema/table/HANA object not present      (requires HANA
                             in either document)                                 catalog cross-reference)
```

### 7.2 Example: Measure → Fact Table Column

```text
Business Object            Measure "DAR GL-USD - DO-NOT-USE" (OBJ_4710)        CONFIRMED
      │
      ▼
Business Layer Expression  Select: SUM(FCTV_INVOICE.GL_DAR_GL_USD_AMT)         CONFIRMED
                           Projection Function: Sum                            CONFIRMED
      │
      ▼
Data Foundation Alias      "FCTV_INVOICE" (Data Foundation table name;         PARSED_UNVERIFIED
                           participates in 27/34 joins as the fact table;      (existence + join
                           Alias vs. Standard status not labeled in text)       participation CONFIRMED;
                                                                                 alias/standard UNKNOWN)
      │
      ▼
Physical Source Object     Column GL_DAR_GL_USD_AMT on FCTV_INVOICE            UNKNOWN
                           (physical schema/table/HANA object not present
                            in either document)
```

Both examples terminate at `UNKNOWN` for the final "Physical Source Object" link — per
`docs/universe_lineage_acquisition_strategy.md` §5, that link can only become `VERIFIED` (using
the existing `LineageVerificationStatus` enum in `src/bo_semantic_extractor/models/common.py`)
after cross-referencing SAP HANA `SYS.*` catalog metadata, which is out of scope for this
document.

## 8. Summary of Classification Counts

| Status | Approximate count of distinct facts classified this way in this report |
|---|---|
| CONFIRMED | ~2,200+ (204 folders, 925 dimensions, 179 attributes, 785 measures, 61 filters with where-expressions, 34 joins with expressions, 38 table names, 3 derived table names, 1 view name, 0 contexts, connection name/path/server) |
| PARSED_UNVERIFIED | 3 explicitly called out (database type "Hana"; alias-vs-standard status of `DIM_REC_TYPE`/`FCTV_INVOICE`/customer-family tables; the customer-alias-family hypothesis in §3.1) |
| UNKNOWN | Join type (34/34), cardinality (34/34), alias identity for all 11 declared alias tables, derived-table SQL for all 3, calculation-view identification, driver type, physical HANA schema/table/column for every object, per-parameter/per-LOV detail, associated-dimension linkage for attributes |

## 9. Non-Goals of This Document

No code, models, or parsers were implemented or modified. This report only inventories what the
two supplied PDFs confirm, do not confirm, or leave entirely unstated, to inform (not perform)
future Business Layer/Data Foundation parser design per
`docs/universe_lineage_acquisition_strategy.md`.
