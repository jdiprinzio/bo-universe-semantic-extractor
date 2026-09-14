# ROUTE_B_SDK — Required Artifacts, Permissions, and Blockers

**Status:** Design package only. **No Java code is implemented; nothing below has been
provisioned or verified against a live environment.**

**Post-Milestone-1 reconciliation:** the post-run javap evidence is authoritative for the
capabilities in `docs/sdk_javap_evidence_register.md` and
`config/route_b/confirmed_sdk_capabilities.json`. Those methods, enum values, and core JARs are
`CONFIRMED_BY_JAVAP`; earlier Javadoc-only gaps are superseded.

## 1. Required SDK Files

Confirmed (from the fetched Javadoc) to be part of the **SAP BI Semantic Layer Java SDK**,
version 4.4, packages actually used by this design:

- `com.sap.sl.sdk.framework` / `com.sap.sl.sdk.framework.cms`
- `com.sap.sl.sdk.authoring.commons`
- `com.sap.sl.sdk.authoring.cms`
- `com.sap.sl.sdk.authoring.businesslayer`
- `com.sap.sl.sdk.authoring.datafoundation`
- `com.sap.sl.sdk.authoring.connection`

Also confirmed as a dependency (not part of the Semantic Layer SDK itself, but required by the
`CmsSessionService` logon pattern): the classic **BusinessObjects Enterprise Java SDK** type
`com.crystaldecisions.sdk.framework.IEnterpriseSession` and `CrystalEnterprise.getSessionMgr()`.

**Confirmed core SDK files:**

- `com.sap.sl.sdk.jar`
- `com.sap.sl.edp.relational.jar`
- `com.sap.sl.edp.hana.jar`
- `com.businessobjects.mds.datafoundation.jar`
- SAP-supported JVM matching the installed BusinessObjects 4.3 client runtime; version and architecture must be detected at runtime.

## 2. Required JARs

**Confirmed core JAR set; transitive completion remains REQUIRED_INPUT:**

- The four core JARs listed above provide the confirmed SDK surfaces recorded by javap.
- A JAR (or set of JARs) providing `com.crystaldecisions.sdk.framework.*`
  (`IEnterpriseSession`, `CrystalEnterprise`) — this is the classic BI Platform Enterprise Java
  SDK, historically distributed separately from the Semantic Layer SDK.
- Standard transitive dependencies of a BI Platform Java client (e.g. CORBA/IIOP stubs used by
  the classic Enterprise SDK) — exact list `REQUIRED_INPUT`.

Do not assume that these four files are the complete transitive classpath; the complete remote
classpath remains REQUIRED_INPUT.

## 3. Required Permissions (Operating System / Filesystem)

- Write access to a local temporary workspace directory for `CmsResourceService.retrieveUniverse(...)` output (confirmed requirement — the method requires a `targetFolder`).
- Read access to that same workspace to subsequently load the retrieved `.blx`/`.dfx` (exact
  loading API `REQUIRED_INPUT`, see `docs/sdk_component_design.md` §3).
- No elevated OS privileges are implied by anything confirmed in the Javadoc.

## 4. Required CMS Access

Confirmed from the Javadoc:

- A valid CMS logon (`CrystalEnterprise.getSessionMgr().logon(...)`) against the target BI
  Platform 4.3 CMS.
- **View** right on the universe resource
  `/Universes/<folder>/DM_Invoice_Data_Mart.unx` (folder `REQUIRED_INPUT` — see
  `docs/sdk_extraction_architecture.md` §2), sufficient for `retrieveUniverse` to succeed. The
  exact CMC right name (e.g. "View" vs. "View On Demand") is `REQUIRED_INPUT` — not enumerated in
  the fetched Javadoc, which describes SDK behavior, not CMC rights terminology.
- **View** right on every connection returned by `getUniverseConnections(...)`, sufficient for
  `loadConnection(...)` to succeed (`CmsResourceService.changeUniverseConnection`'s Javadoc
  explicitly lists *"the view right for this connection is denied"* as a possible exception
  condition — confirming a view-level CMS right gates connection access).
- **No** publish, edit, or security-administration rights are required or requested — every
  operation in this design is read-only (§7 of `docs/sdk_extraction_architecture.md`).

## 5. Required BO Role / Permissions (Business Objects Security Model)

**REQUIRED_INPUT overall** — the fetched Javadoc describes SDK method behavior and the
*existence* of view-right checks, but not this environment's actual CMC role/group model. Before
implementation, obtain from the BI Platform administrator:

- Confirmation of which CMC user/group this extraction process will run as.
- Confirmation that the account has **View** (read-only) rights on:
  - The `/Universes/...` folder containing `DM_Invoice_Data_Mart.unx`.
  - The `/Connections/...` folder containing its attached connection(s).
- Explicit confirmation that the account does **not** have — or that this process will never
  exercise — Edit/Publish/Modify/Security-Administration rights on any of the above, consistent
  with this project's read-only design.

## 6. Blockers Before Implementation

In priority order — each blocks the corresponding component in
`docs/sdk_component_design.md`:

1. **CMS environment details** (blocks §2 of the architecture doc): target CMS host:port, the
   `authentication` mode string(s) valid for this environment, and the exact `/Universes/...`
   folder path for `DM_Invoice_Data_Mart.unx`.
2. **JAR/library provisioning** (blocks all components): exact JAR filenames/versions and
   installation source for both the Semantic Layer SDK and the classic Enterprise Java SDK
   (§1–2).
3. **Confirmed method or service returning `DataSource`** (blocks Business Layer extraction).
4. **Confirmed method or service returning `DataFoundation`** (blocks Data Foundation extraction).
5. **CMC role/rights confirmation** (blocks any live CMS test): sign-off from the BI Platform
   administrator per §5 above.
6. **Remote working and export directories** (blocks remote packaging).
7. **A non-production test universe or a sanctioned read-only test window** against
   `DM_Invoice_Data_Mart.unx` (or an equivalent test universe) before running any SDK code
   against this environment, per this project's manual-validation discipline already documented
   in `docs/integration_readiness_plan.md` §5.

The join, alias, derived-table, Business Layer collection, cardinality, outer-type, and operator
items previously listed as blockers are resolved by `CONFIRMED_BY_JAVAP` evidence. The remaining
blockers are the explicit prerequisites
gathered from confirmed Javadoc facts and stated as `REQUIRED_INPUT` throughout
`docs/sdk_extraction_architecture.md`, `docs/sdk_component_design.md`, and
`docs/sdk_json_contracts.md`.
