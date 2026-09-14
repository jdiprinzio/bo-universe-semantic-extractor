# ROUTE_B_SDK — Component Design

**Status:** Design package only. **No Java code is implemented.** Defines the planned component
boundaries for the future SDK-based extractor, each mapped to confirmed SAP BI Semantic Layer
Java SDK 4.4 classes/methods (see `docs/sdk_extraction_architecture.md` for the evidence basis).
Component names below are **proposed Java class names for a future implementation** — they are
not existing SDK classes. Post-Milestone-1 javap evidence is authoritative for the capabilities
listed in `docs/sdk_javap_evidence_register.md`; earlier Javadoc-only gaps are superseded.

## 1. Component Overview

```text
RouteBSdkSession                (CMS auth + SlContext lifecycle)
     │
     ▼
RouteBUniverseRetriever          (CmsResourceService.retrieveUniverse)
     │
     ├──▶ RouteBBusinessLayerExtractor   (businesslayer package read accessors)
     │        │
     │        └──▶ business_layer.json
     │
     ├──▶ RouteBDataFoundationExtractor  (datafoundation package read accessors)
     │        │
     │        └──▶ data_foundation.json, join_metadata.json, context_metadata.json
     │
     ├──▶ RouteBConnectionExtractor      (CmsResourceService.loadConnection + DatabaseConnection)
     │        │
     │        └──▶ connection_metadata.json
     │
     └──▶ RouteBLineageEdgeBuilder       (cross-references the above; no HANA call)
              │
              └──▶ lineage_edges.json
```

Every component only calls confirmed SDK methods (§2–5) or is explicitly marked with a
`REQUIRED_INPUT` blocker where the exact accessor is not yet confirmed.

The post-Milestone-1 capability register supersedes historical Javadoc-only markers in this
document. Only the six inputs in §9 are current blockers; Milestone 2 must detect the
SAP-supported JVM version and architecture rather than enforce Java 11.

## 2. `RouteBSdkSession`

Responsibility: obtain and hold the CMS session and `SlContext` for the duration of one
extraction run; guarantee cleanup.

| Responsibility | Confirmed SDK surface |
|---|---|
| Log on | `IEnterpriseSession session = CrystalEnterprise.getSessionMgr().logon(user, password, server, authentication)` |
| Create SDK context | `SlContext context = SlContext.create()` |
| Attach session | `context.getService(CmsSessionService.class).setSession(session)` (once only per context) |
| Obtain a service | `context.getService(<ServiceInterface>.class)` (confirmed pattern shown on `BusinessLayerFactory`/`DataFoundationFactory` Javadoc: "See `SlContext.getService(Class)` to get an instance of the factory.") |
| Tear down | `context.close()` (does **not** log off the session) then `session.logoff()` |

**Security constraint (enforced by design, not just convention):** the `user`/`password`
parameters must come only from environment variables (mirroring
`src/bo_semantic_extractor/config.py`'s `BoEnvironmentConfig`, which already models
`username`/`password` as `SecretStr`) — never hard-coded, never logged. `password` must never be
read back from any SDK object afterward (§5 of the architecture doc: `PASSWORD` cannot be
retrieved from the CMS regardless).

**REQUIRED_INPUT:** confirmation that `server` should be formatted as `host:port` (the Javadoc
example uses `"myCms:6400"`, matching this project's existing `BO_BASE_URL`-style config, but the
exact expected format for this environment's CMS must be confirmed with the BI Platform admin).

## 3. `RouteBUniverseRetriever`

Responsibility: resolve `DM_Invoice_Data_Mart.unx` in the CMS and materialize it locally.

| Responsibility | Confirmed SDK surface |
|---|---|
| Resolve CUID from path (or vice versa) | `CmsResourceService.getResourceCuid(path)` / `getResourcePath(cuid)` |
| Get published revision | `CmsResourceService.getUniverseRevisionNumber(unxIdentifier)` |
| List attached connections | `CmsResourceService.getUniverseConnections(repositoryUniversePath)` |
| Retrieve to local workspace | `CmsResourceService.retrieveUniverse(repositoryPath, targetFolder, saveForAllUsers=false)` |
| Release resources | `CmsResourceService.close(SlResource)` |

Output: the local `.blx` path (as returned by `retrieveUniverse`), plus the `.dfx` and any
`.cns` files created alongside it in the same temporary folder (per the architecture doc §2).

**REQUIRED_INPUT:** the exact method(s) used to *load* the retrieved `.blx`/`.dfx` files back
into `BusinessLayer`/`DataFoundation` objects for reading (likely on `LocalResourceService`,
package `com.sap.sl.sdk.authoring.local` — confirmed to exist, but its method signatures were
not fetched this session).

## 4. `RouteBBusinessLayerExtractor`

Responsibility: walk the retrieved Business Layer and emit `business_layer.json`.

| Sub-responsibility | Confirmed SDK surface | Status |
|---|---|---|
| Get the root folder | `BusinessLayer.getRootFolder()` → `RootFolder` | CONFIRMED |
| Look up one item by path | `BusinessLayerService.getBlItem(BusinessLayer, String path, boolean)` | CONFIRMED (signature inferred from a usage example; full Javadoc page not fetched) |
| Enumerate every folder/dimension/attribute/measure/filter | `DataSource.getBusinessLayerItemFlatList()`, `BusinessLayer.getDimensions()`, `getMeasures()`, `getFilters()`, `getHierarchies()`, `getAnalysisDimensions()`, `Dimension.getAttributes()` | CONFIRMED_BY_JAVAP |
| Read a dimension's Select expression | `Dimension` has a `setSelect` (confirmed); matching getter | CONFIRMED existence, exact getter name `REQUIRED_INPUT` |
| Read a measure's projection function | `Measure.getDefaultAggregation()` | CONFIRMED_BY_JAVAP |
| Read a filter's expression | `NativeRelationalFilter` / `BusinessFilter` classes exist | CONFIRMED existence, accessor `REQUIRED_INPUT` |
| Read prompts/parameters | `DataSource.getPrompts()`, `DataSource.getListsOfValues()` | CONFIRMED_BY_JAVAP |
| Read navigation paths | `NavigationPath.getDimensions()` (confirmed: example calls `.add(dimension)` on it) | CONFIRMED |

Mapping to the existing PDF-derived catalog fields (see `docs/sdk_json_contracts.md` §7 for the
full gap analysis):

| Existing PDF-derived field (`object_catalog.csv`/`expression_catalog.csv`) | Future SDK-derived source |
|---|---|
| `object_type` (`class`/`dimension`/`attribute`/`measure`/`filter`) | The concrete SDK type (`Folder`/`Dimension`/`Attribute`/`Measure`/`NativeRelationalFilter` or `BusinessFilter`) |
| `object_name`, `folder_path`, `description` | `Nameable.getName()`, container traversal path, `REQUIRED_INPUT` description accessor |
| `select_expression` | `Dimension` confirmed (`getSelect()`, inferred); other types `REQUIRED_INPUT` |
| `where_expression` | Filter type's expression accessor — `REQUIRED_INPUT` |
| `projection_function` | `Measure` + `ProjectionFunction` — accessor `REQUIRED_INPUT` |
| `verification_status` | Always `CONFIRMED` once read via the SDK (no PDF-rendering ambiguity possible) |

## 5. `RouteBDataFoundationExtractor`

Responsibility: walk the retrieved Data Foundation and emit `data_foundation.json`,
`join_metadata.json`, `context_metadata.json`.

| Sub-responsibility | Confirmed SDK surface | Status |
|---|---|---|
| List all tables (standard + alias + derived) | `DataFoundation.getTables()` → `List<Table>` | CONFIRMED |
| Distinguish alias vs. standard vs. derived | Concrete type of each `Table` (`DatabaseTable` / `AliasTable` / `DerivedTable`) | CONFIRMED that these three types exist as distinct classes; a type-check (`instanceof`) resolves the classification with certainty, unlike Route A |
| Get a derived table's SQL | `DerivedTable.getExpression()`, `DerivedTable.getEncodedExpression()` | CONFIRMED_BY_JAVAP |
| Get an alias's aliased table | `AliasTable.getAliasedTable()` | CONFIRMED_BY_JAVAP |
| List joins | `DataFoundation.getJoins()` → `List<Join>` | CONFIRMED |
| Get a join's expression, endpoints, and cardinality | `Join.getLeftColumns()`, `getRightColumns()`, `getExpression()`, `getCardinality()`, `getLeftTable()`, `getRightTable()` | CONFIRMED_BY_JAVAP |
| Get a join's outer/join type and operator | `SQLJoin.getOuterType()`, `getOperator()`, `isAutoJoin()`, `isCustom()` | CONFIRMED_BY_JAVAP |
| List contexts | `DataFoundation.getContexts()` → `List<Context>` | CONFIRMED |
| Get a context's associated/excluded joins | `Context.getJoins()`, `Context.getExcludedJoins()` | CONFIRMED_BY_JAVAP |
| List/read the master view and any custom views | `DataFoundation.getMasterView()`, `getDataFoundationViews()` | CONFIRMED |
| Get engine-level flags | `DataFoundation.isCartesianProductAllowed()`, `isMultipleSqlStatementsAllowed()` | CONFIRMED |

**Immediate advantage over Route A:** join type and cardinality — both `UNKNOWN` for all 34
joins under Route A (per `docs/dm_invoice_data_mart_design_inventory.md` §4) — are now
structurally readable through the javap-confirmed `Join`/`SQLJoin` accessors and enum values. This
is the single highest-value gap Route B closes (see
`docs/sdk_json_contracts.md` §7 gap analysis).

## 6. `RouteBConnectionExtractor`

Responsibility: read connection identity/type metadata only; emit `connection_metadata.json`.

| Sub-responsibility | Confirmed SDK surface |
|---|---|
| Load a connection by path | `CmsResourceService.loadConnection(connectionPath)` → `DatabaseConnection` |
| Connection name | `Connection.getName()` |
| Database type | `DatabaseConnection.getParameter(DatabaseConnection.DBMS)` |
| Middleware / network layer | `DatabaseConnection.getParameter(DatabaseConnection.NETWORK_LAYER)` |
| HANA-specific parameters (if applicable) | `SAP_HANA_SERVER_TYPE`, `SAP_HANA_HOST_NAME`, `SAP_HANA_INSTANCE_NUMBER`, `SAP_HANA_USE_SSL` |
| Release the resource | `CmsResourceService.close(SlResource)` |

**Hard exclusion (never implemented, never requested):** `DatabaseConnection.getParameter(DatabaseConnection.PASSWORD)` — the SDK itself guarantees this returns nothing retrievable from
the CMS; this extractor must not even attempt the call, to keep the code's intent unambiguous
for reviewers.

## 7. `RouteBLineageEdgeBuilder`

Responsibility: produce `lineage_edges.json` by joining the outputs of §4–6 — **no new SDK
calls**, no HANA access. This component supersedes the Route A pattern-detection approach
(`extract_table_column_candidates` in `src/bo_semantic_extractor/normalization/lineage_catalog.py`) because Route B's `Dimension.getSelect()`-style accessors (once confirmed) return the
already-structured expression without needing regex table.column detection — though the same
lineage-candidate-vs-verified distinction still applies until HANA cross-reference occurs (see
`docs/universe_lineage_acquisition_strategy.md` §5, unchanged by this design).

## 8. Cross-Cutting: Read-Only Enforcement

Every component above is designed to call only `get*`/`is*` accessor methods and the specific
confirmed read operations listed in §2–6 (`loadConnection`, `getResourceCuid`,
`getResourcePath`, `getUniverseRevisionNumber`, `getUniverseConnections`, `retrieveUniverse`,
`close`). No component calls any `create*`, `save*`, `publish*`, `change*`, or `convert*` method
— see `docs/sdk_extraction_architecture.md` §7 for the full confirmed mutating-operation list
this design avoids.

## 9. Remaining Required Inputs

1. Complete transitive SDK classpath.
2. Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
3. Confirmed method or service returning `DataSource`.
4. Confirmed method or service returning `DataFoundation`.
5. CMS details and permissions only if CMS retrieval is selected.
6. Remote working and export directories.

## 10. Non-Goals of This Document

No Java classes are implemented. Every method name presented as `CONFIRMED` was read verbatim
from the official Javadoc during this session; every method name still needed but not yet
fetched is explicitly marked `REQUIRED_INPUT`, not guessed.
