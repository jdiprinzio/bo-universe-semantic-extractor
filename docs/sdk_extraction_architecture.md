# ROUTE_B_SDK — SDK Extraction Architecture

**Status:** Design package only. **No Java code is implemented.** This document defines the
architecture for extracting authoritative universe metadata directly from the `.unx` resource
for `DM_Invoice_Data_Mart.unx` using the **SAP BusinessObjects 4.3 (SDK 4.4) BI Semantic Layer
Java SDK** (`com.sap.sl.sdk.*`), instead of the PDF-export path (Route A, already validated).

## 0. Evidence Basis

**Post-Milestone-1 reconciliation:** the javap evidence supplied after Milestone 1 is authoritative
for the capabilities recorded in [sdk_javap_evidence_register.md](sdk_javap_evidence_register.md)
and `config/route_b/confirmed_sdk_capabilities.json`. Those capabilities are
`CONFIRMED_BY_JAVAP` and supersede earlier Javadoc-only `REQUIRED_INPUT` markers for the listed
getters, enum values, and core JARs. The remaining true blockers are listed in §9.

The runtime JVM is not fixed to Java 11 by this design. Milestone 2 must detect and report the
SAP-supported JVM version and architecture that match the installed BusinessObjects 4.3 client
runtime.

Every class, interface, package, method, and constant named in this design package was read
directly from the official Javadoc at
`https://help.sap.com/doc/4a2ba099c48c407883106dc4ff5bc243/4.4/en-US/` (SAP BI Semantic Layer
Java SDK API, version 4.4) during this session. Where a needed detail was **not** found on a
fetched page, it is explicitly marked `REQUIRED_INPUT` rather than guessed — per the skill's
"do not assume class names or APIs not explicitly available" rule.

Confirmed SDK packages:

| Package | Purpose (from Javadoc) |
|---|---|
| `com.sap.sl.sdk.framework` | Interfaces used to manage errors (`SlException`, `IStatus`, `SlContext`) |
| `com.sap.sl.sdk.framework.cms` | Sets/retrieves the CMS session (`CmsSessionService`) |
| `com.sap.sl.sdk.authoring.commons` | Root SDK resource type (`SlResource`), shared mixins (`Nameable`, `Identifiable`, `Customizable`) |
| `com.sap.sl.sdk.authoring.cms` | Publish/retrieve CMS resources (`CmsResourceService`), CMS security (`CmsSecurityService`) |
| `com.sap.sl.sdk.authoring.businesslayer` | Create/manage business layers and business layer objects |
| `com.sap.sl.sdk.authoring.datafoundation` | Create/manage data foundations and their objects |
| `com.sap.sl.sdk.authoring.connection` | Create/manage connections and shortcuts |
| `com.sap.sl.sdk.authoring.security` | Data/business security profiles |
| `com.sap.sl.sdk.authoring.checkintegrity` | Check-integrity process control |
| `com.sap.sl.sdk.authoring.local` | Local (non-CMS) resource operations |

## 1. CMS Authentication

**Confirmed** from the `CmsSessionService` Javadoc, which documents the following pattern
verbatim:

```java
String user = "";
String password = "";
String server = "myCms:6400";
String authentication = "secEnterprise";

IEnterpriseSession session =
    CrystalEnterprise.getSessionMgr().logon(user, password, server, authentication);
SlContext context = SlContext.create();
context.getService(CmsSessionService.class).setSession(session);

// ... perform SDK operations ...

context.close();
session.logoff();
```

Key confirmed facts:

- Authentication uses the classic BusinessObjects Enterprise SDK type
  `com.crystaldecisions.sdk.framework.IEnterpriseSession`, obtained via
  `CrystalEnterprise.getSessionMgr().logon(user, password, server, authentication)` —
  **not** a Semantic Layer SDK type. The Semantic Layer SDK only *consumes* an existing session.
- `SlContext.create()` creates the Semantic Layer SDK context; `context.getService(CmsSessionService.class).setSession(session)` attaches the enterprise session to it. `setSession` can only be
  called once per context (a second call throws).
- `context.close()` does **not** close the underlying session — the session must be logged off
  separately (`session.logoff()`).
- `CmsSessionService.getSession()` returns the attached session (or `null` if none is attached).

**REQUIRED_INPUT:** the exact `authentication` string value(s) supported in this specific BI
Platform 4.3 environment (e.g. `secEnterprise`, `secLDAP`, `secWinAD`) — confirm with the BI
Platform administrator; do not assume `secEnterprise` is the only valid value for this
deployment (see `docs/businessobjects_missing_inputs.md` item 1, which already tracks this for
the REST path and applies equally here).

## 2. Universe Retrieval

**Confirmed** from `CmsResourceService` (package `com.sap.sl.sdk.authoring.cms`):

- `CmsResourceService.UNIVERSES_ROOT`, `CONNECTIONS_ROOT`, `SETS_ROOT` — CMS root path constants.
  A repository path is formatted as `<ROOT>/<subfolder>/<name>`, e.g.
  `/Universes/myCmsFolder/DM_Invoice_Data_Mart.unx`.
- `getResourceCuid(path)` / `getResourcePath(cuid)` — resolve between CMS path and CUID for
  `.unx`, `.unv`, and `.cnx` resources.
- `getUniverseRevisionNumber(unxIdentifier)` — returns the published revision number, accepting
  either the path or the CUID.
- **`retrieveUniverse(repositoryPath, targetFolder, saveForAllUsers)`** — the confirmed
  retrieval method. Creates local resources (`.blx`, `.cns`, and `.dfx` if applicable) in
  `targetFolder` from the published `.unx`. Returns the created business-layer file path,
  formatted `[targetFolder]/[temporary folder name]/[business layer name].blx`.
  - If `saveForAllUsers=false`: creates a **secured** local copy — a CMS session is required to
    open it.
  - If `saveForAllUsers=true`: creates a **non-encrypted** local copy — readable by anyone with
    filesystem access. **For a read-only extraction pipeline, `saveForAllUsers=false` is the
    correct choice** unless a specific, approved reason requires the unencrypted form.
- `getUniverseConnections(repositoryUniversePath)` — lists the secured connection paths attached
  to a published universe (needed before/instead of loading each connection individually).
- `close(SlResource)` — must be called on every retrieved resource to avoid a memory leak.

Retrieval flow for `DM_Invoice_Data_Mart.unx`:

```text
1. repositoryPath = "/Universes/<folder>/DM_Invoice_Data_Mart.unx"   (folder = REQUIRED_INPUT)
2. cuid = cmsResourceService.getResourceCuid(repositoryPath)          [evidence: confirmed CUID]
3. revision = cmsResourceService.getUniverseRevisionNumber(cuid)      [evidence: confirmed revision]
4. connectionPaths = cmsResourceService.getUniverseConnections(repositoryPath)
5. blxPath = cmsResourceService.retrieveUniverse(repositoryPath, workspaceDir, saveForAllUsers=false)
   -> creates {workspaceDir}/{tempFolder}/DM_Invoice_Data_Mart.blx (+ .dfx, .cns, as applicable)
```

**REQUIRED_INPUT:** the exact CMS folder path under `/Universes/` where
`DM_Invoice_Data_Mart.unx` is published in this environment — not guessed here.

## 3. Business Layer Extraction

Read-side access is confirmed to go through the retrieved `.blx` resource (loaded into a
`BusinessLayer`/`RelationalBusinessLayer` object) and its object graph — the `businesslayer`
package's authoring classes double as the read/write model. Confirmed classes and factory
methods relevant to each requested category:

| Category | Confirmed SDK type(s) | Confirmed evidence |
|---|---|---|
| Classes (folders) | `Folder`, `RootFolder`, `BlContainer` | `BusinessLayer.getRootFolder()` confirmed via `BusinessLayerFactory.createBlItem` example: `RootFolder rootFolder = businessLayer.getRootFolder();` |
| Dimensions | `Dimension` | `BusinessLayerFactory.createBlItem(Dimension.class, name, parent)`; `dimension.setSelect("table.column")` confirms a `setSelect`/(implied) `getSelect` accessor exists on `Dimension` |
| Attributes | `Attribute` | Listed as a valid `createBlItem` type argument |
| Measures | `Measure` | Listed as a valid `createBlItem` type argument; `ProjectionFunction` class exists in the same package (see below) |
| Filters | `NativeRelationalFilter`, `BusinessFilter` | Both listed as valid `createBlItem` type arguments |
| Prompts | `Parameter` (package `datafoundation`, attachable to either a `BusinessLayer` or a `DataFoundation`) | `BusinessLayerFactory.createParameter(name, businessLayer)` / `createParameter(name, dataFoundation)`; confirmed `Parameter` properties from the factory's own example: `setUserPrompted(boolean)`, `setPromptText(String)`, `setDataType(LovParameterDataType)`, `setAssociatedLov(...)` |
| Object expressions | `Dimension.setSelect(String)` (confirmed); analogous accessors on `Measure`/`Attribute`/filter types | `REQUIRED_INPUT`: exact getter/setter names for `Measure`, `Attribute`, `NativeRelationalFilter`, `BusinessFilter` were not present on the fetched pages — do not assume `getSelect()`/`getWhere()` naming for these types until confirmed from their own Javadoc pages |
| Projection functions | `ProjectionFunction` (class exists in `businesslayer` package, per the "All Classes" index) | `REQUIRED_INPUT`: enum/class member values and the exact `Measure` accessor name were not fetched this session |
| Navigation paths | `NavigationPath` | `BusinessLayerFactory.createNavigationPath(name, businessLayer)`; example shows `navigationPath.getDimensions().add(dimension)` and a lookup helper `businessLayerService.getBlItem(businessLayer, "Dimperiod\\Date", true)` — confirming a `BusinessLayerService.getBlItem(BusinessLayer, String, boolean)` method exists |
| Lists of values | `StaticLov`, `SQLQueryLov`, `BusinessQueryLov`, `BusinessHierarchicalLov` (+ column/row types) | All confirmed via `BusinessLayerFactory.create*` methods |
| Formats | `PredefinedDateTimeFormat`, `CustomDateTimeFormat`, `PredefinedNumberFormat`, `CustomNumberFormat` | Confirmed via `BusinessLayerFactory.create*` methods |
| Aggregate incompatibilities | `AggregateIncompatibility` | Confirmed via `createAggregateIncompatibility(RelationalBusinessLayer)` |

**REQUIRED_INPUT (not yet confirmed this session):** the read-side getters for iterating an
existing Business Layer's full object tree (e.g. how to enumerate every `Dimension`/`Measure`
under a `Folder`, beyond the single `BusinessLayerService.getBlItem(...)` lookup-by-path
example seen). This requires fetching the `BlContainer`, `BusinessLayer`, and
`BusinessLayerService` Javadoc pages directly (not yet done in this session) before any
traversal code is written.

## 4. Data Foundation Extraction

Confirmed directly from the `DataFoundation` and `DataFoundationFactory` interface pages:

| Category | Confirmed accessor / factory method |
|---|---|
| Tables (all kinds) | `DataFoundation.getTables()` → `List<Table>` (contains standard, alias, and derived tables together — matches the PDF-report finding that "Tables (38)" already includes derived tables) |
| Aliases | `DataFoundationFactory.createAliasTable(name, aliasedTable, dataFoundation)` → `AliasTable`. `aliasedTable` must be a `DatabaseTable` or `DerivedTable` already owned by the data foundation. An alias table has **no columns of its own** (confirmed: "An alias table does not have any columns"). |
| Derived tables | `DataFoundationFactory.createDerivedTable(name, sql, dataFoundation)` → `DerivedTable` (mono-source); a database-specific overload exists for `MultiSourceDataFoundation`. **This is the confirmed way to obtain a Derived Table's SQL** (`DerivedTable.getSql()`-equivalent accessor is implied but its exact getter name is `REQUIRED_INPUT` — not fetched this session). |
| Views | `DataFoundation.getMasterView()` → `DataFoundationView` (the default view containing all tables; "cannot be created or deleted" — confirms the PDF's single `Master` view is this master view). `DataFoundation.getDataFoundationViews()` → any additional custom views. |
| Joins | `DataFoundation.getJoins()` → `List<Join>`. `DataFoundationFactory.createSqlJoin(expression, dataFoundation)` → `SQLJoin`, confirming joins are modeled as a raw SQL expression string — directly compatible with the `join_expression` field already produced by the Route A parser. |
| Cardinalities | `Cardinality` enum (package `datafoundation`), **confirmed exact values**: `CUNKNOWN`, `C1_1`, `C1_N`, `CN_1`, `CN_N`. `Cardinality.get(String)` / `.get(int)` / `.getByName(String)` / `.getValue()` / `.getName()` / `.getLiteral()` are confirmed utility accessors. |
| Join types (outer join kind) | `OuterType` class confirmed to exist in the `datafoundation` package (seen in the "All Classes" index). `REQUIRED_INPUT`: its enum values and the `Join`/`SQLJoin` accessor that returns it were not fetched this session — do not assume literal names (e.g. do not assume `LEFT`/`RIGHT`/`FULL`/`NONE`) until confirmed. |
| Contexts | `DataFoundation.getContexts()` → `List<Context>`. `DataFoundationFactory.createContext(name, dataFoundation)` → `Context`. (Matches the PDF finding of `Contexts (0)` for this Data Foundation — an empty list is expected here.) |
| Cartesian product / multi-SQL settings | `DataFoundation.isCartesianProductAllowed()`, `isMultipleSqlStatementsAllowed()` — directly correspond to the PDF's `Allow Cartesian Products: true` / `Multiple SQL statements for each context: true` properties. |

**REQUIRED_INPUT:** `Join`'s own method summary (beyond inherited `Identifiable`/`Inheritable`
methods) was not rendered on the fetched page — the accessor names for a join's left/right
table, its expression, its cardinality, and its outer type must be confirmed from the `Join` and
`SQLJoin` Javadoc pages (or `Context.getJoins()`-equivalent, if contexts reference joins by
object rather than name) before implementation.

## 5. Connection Extraction (Never Credentials)

Confirmed from `CmsResourceService.loadConnection(String)` → `DatabaseConnection`, and the
`DatabaseConnection` / `ConnectionFactory` interfaces:

| Category | Confirmed source |
|---|---|
| Connection name | `Connection.getName()` (inherited by `DatabaseConnection`) |
| Database type ("DBMS") | `DatabaseConnection.getParameter(DatabaseConnection.DBMS)` — confirmed constant; Javadoc example value: `"MS SQL Server 2008"` |
| Middleware / network layer type | `DatabaseConnection.getParameter(DatabaseConnection.NETWORK_LAYER)` — confirmed constant; Javadoc example value: `"JDBC Drivers"` |
| SAP HANA specifics (if applicable) | `SAP_HANA_SERVER_TYPE` (enumerated `DatabaseConnection.HANAServerType`), `SAP_HANA_HOST_NAME`, `SAP_HANA_INSTANCE_NUMBER`, `SAP_HANA_USE_SSL`, `SAP_HANA_AUTO_RECONNECT`, `SAP_HANA_FETCH_SIZE` — all confirmed constants |
| SAP-specific connections (if applicable) | `SAP_SERVER_TYPE` (enumerated `DatabaseConnection.SAPServerType`), `SAP_CLIENT_NUMBER`, `SAP_SYSTEM_ID`, `SAP_SYSTEM_NUMBER`, `SAP_APPLICATION_SERVER_NAME`, `SAP_MESSAGE_SERVER_NAME`, `SAP_GROUP_NAME` — all confirmed constants |
| Authentication mode | `AUTHENTICATION_MODE` (enumerated `DatabaseConnection.AuthenticationMode`) — the *mode* (e.g. which auth scheme is configured), never the credential value itself |

**Confirmed, structural guarantee against credential extraction:** the `PASSWORD` constant's own
Javadoc states explicitly: *"The password cannot be retrieved from the CMS."* This is an SDK-level
guarantee, not just a coding convention this project must self-enforce — reinforce it anyway by
never calling `getParameter(DatabaseConnection.PASSWORD)` and never logging the full
`getParameters()` list without filtering out `PASSWORD` and `USER_NAME` first (`USER_NAME` is
documented "Is private" but is a login identifier, not a secret — still exclude it from any
committed or logged output per this project's redaction rules in
`src/bo_semantic_extractor/logging_config.py`).

`ConnectionFactory.createRelationalConnection(name, dbms, networkLayer)` /
`createOlapConnection(...)` are **write/create** operations — out of scope for this read-only
extraction track; listed here only to confirm `dbms` and `networkLayer` are the correct
parameter *names* to read back via `getParameter(...)`.

## 6. Temporary Workspace Management

- `CmsResourceService.retrieveUniverse(...)` writes to a caller-supplied `targetFolder`, inside
  which the SDK creates its own `[temporary folder name]` subfolder — the exact business layer
  file path is returned by the call, so the pipeline must capture and use that return value
  rather than assuming a fixed path.
- Every retrieved `SlResource` (business layer, data foundation, connection) **must** be released
  via `close(SlResource)` (`CmsResourceService.close`, `ConnectionFactory.close`, or
  `LocalResourceService.close`, matching the service that produced it) to avoid a memory leak —
  this must happen even on the error path (i.e. in a `finally` block once Java code exists).
- If `saveForAllUsers=false` was used (recommended, §2), the local `.blx`/`.dfx`/`.cns` files are
  **secured** and require the same CMS session to reopen — the workspace is not portable to a
  process without that session.
- The workspace directory should be a per-run, uniquely named temporary directory (mirroring
  this project's existing `raw/{run_id}/` convention in
  `src/bo_semantic_extractor/extractors/archive.py`) and should be deleted after extraction
  completes, whether the run succeeds or fails — exact deletion timing/retention policy is a
  project decision, not an SDK requirement.

## 7. Read-Only Controls

This design deliberately avoids every SDK operation confirmed to mutate CMS or local state:

| Confirmed mutating operation (avoid) | Confirmed read-only equivalent (use) |
|---|---|
| `CmsResourceService.publish(...)` | *(none needed — extraction never publishes)* |
| `CmsResourceService.changeUniverseConnection(s)(...)` | *(none needed)* |
| `CmsResourceService.saveConnection(DatabaseConnection)` | `CmsResourceService.loadConnection(String)` (read) |
| `CmsResourceService.convertUniverse(...)` | *(none needed — no `.unv`→`.unx` conversion in this track)* |
| `ConnectionFactory.createRelationalConnection(...)` / `createOlapConnection(...)` | `CmsResourceService.loadConnection(String)` |
| `DataFoundationFactory.create*(...)` (any) | `DataFoundation.get*()` read accessors only |
| `BusinessLayerFactory.create*(...)` (any) | `BusinessLayerService.getBlItem(...)` / other confirmed-or-to-be-confirmed read accessors only |
| `retrieveUniverse(..., saveForAllUsers=true)` | `retrieveUniverse(..., saveForAllUsers=false)` (secured local copy) |

No SDK call in this design ever saves, publishes, or converts a resource. This mirrors the
skill's existing rule set already enforced for the REST path in
`src/bo_semantic_extractor/bo_client/rest_client.py`.

## 8. Deterministic JSON Output Contracts

Every extraction stage writes one deterministic JSON file per confirmed root object, sorted by
a stable identifier (never display name alone), matching the existing project convention in
`src/bo_semantic_extractor/documentation/design_catalog_writer.py`. Full schemas are defined in
`docs/sdk_json_contracts.md`. Every contract's envelope includes, at minimum:
`source_system`, `extraction_method`, `evidence_level`, `verification_status` — see that
document for the full field list and allowed values.

## 9. Remaining Required Inputs After javap Reconciliation

Only these items remain `REQUIRED_INPUT` before Milestone 2 implementation:

1. Complete transitive SDK classpath.
2. Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
3. Confirmed method or service returning `DataSource`.
4. Confirmed method or service returning `DataFoundation`.
5. CMS details and permissions only if CMS retrieval is selected.
6. Remote working and export directories.

The previously unresolved join accessors, alias/derived-table accessors, Business Layer
collection accessors, cardinality values, outer values, and join-operator values are now
`CONFIRMED_BY_JAVAP`; see the evidence register.

## 10. Non-Goals of This Document

No Java code, build scripts, or SDK calls are implemented here. No class, method, or constant
not confirmed via the official Javadoc during this session is presented as fact — every
unconfirmed detail is explicitly marked `REQUIRED_INPUT`.
