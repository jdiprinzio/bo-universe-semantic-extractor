# SAP BusinessObjects Missing Inputs — Consolidated

## ROUTE_B_SDK Reconciliation Addendum — 2026-09-14

The post-Milestone-1 javap evidence has resolved the earlier Semantic Layer SDK accessor gaps:
Business Layer collections, Data Foundation tables/joins/contexts, alias and derived-table
accessors, join endpoints/expression/cardinality, SQL join outer/operator/flags, and confirmed
Cardinality/Outer/JoinOperator values are recorded in
`docs/sdk_javap_evidence_register.md` and
`config/route_b/confirmed_sdk_capabilities.json` with status `CONFIRMED_BY_JAVAP`.

For ROUTE_B_SDK, the remaining required inputs are only:

1. Complete transitive SDK classpath.
2. Confirmed read-only loading path from local BLX/DFX or CMS retrieval.
3. Confirmed method or service returning `DataSource`.
4. Confirmed method or service returning `DataFoundation`.
5. CMS details and permissions only if CMS retrieval is selected.
6. Remote working and export directories.

This is the single, prioritized checklist of everything required before this pipeline can
connect to a real SAP BusinessObjects BI Platform instance. Each item names the exact
documentation, sample, or decision needed — never a guess. Update this file (don't just append)
as items are resolved; move resolved items to
[businessobjects_api_requirements.md](businessobjects_api_requirements.md) as CONFIRMED.

## Priority 1 — Blocks any real connection

1. **Authentication contract.** Exact logon endpoint path, HTTP method, request body/query
   shape, success response shape, and the token/cookie/header name used on subsequent calls.
   *Source needed:* "Authentication"/"Getting Started" chapter of the *Business Intelligence
   Platform RESTful Web Service Developer Guide* (confirmed to exist at
   `https://help.sap.com/docs/SAP_BUSINESSOBJECTS_BUSINESS_INTELLIGENCE_PLATFORM/db6a17c0d1214fd6971de66ea0122378`),
   retrieved as text/PDF, **or** a sanitized `curl`/Postman capture of a real logon
   request/response pair from this environment (credentials and tokens redacted by the provider
   before sharing).
2. **Base URL / context root confirmation.** Confirmation of the actual REST context root for
   this BI Platform version/deployment (e.g., whether it matches the pattern documented in the
   guide above for this specific version).
   *Source needed:* deployment configuration or CMC administration documentation for this
   specific BI Platform instance.
3. **Session management contract.** Token lifetime, renewal vs. re-authentication behavior, and
   any concurrent-session constraints relevant to a scheduled/unattended extraction job.
   *Source needed:* "Session Management" chapter of the same guide, or CMC session-timeout
   settings documentation.

## Priority 2 — Blocks universe discovery and metadata extraction

4. **Universe discovery/listing contract.** Endpoint and parameters to list or search published
   universes, and to resolve one by exact CUID or exact name.
   *Source needed:* "Semantic Layer" / "CMS Query Service" chapter of the RESTful Web Service
   Developer Guide, or a sanitized sample listing response.
5. **Universe metadata field shape.** Real field names for universe CUID, name, type,
   repository path, description, and connection references.
   *Source needed:* sanitized sample JSON for a `getUniverse`-equivalent response.
6. **Universe object field shape and enumeration.** Real field names/types for folders,
   dimensions, attributes, measures, filters, hierarchies, levels, parameters — including
   expression fields (`select`/`where`), aggregation/projection function, associated dimension,
   list of values, hidden/deprecated flags, and access level. Also whether/how this list is
   paginated.
   *Source needed:* sanitized sample JSON enumerating at least one object of each type, or the
   guide's "Universe Resources" reference section.
7. **Connection metadata field shape.** Which non-secret fields (data-source type, server,
   database) are actually returned, and confirmation that no secret material is ever present in
   this response.
   *Source needed:* "Connections" chapter of the guide, or a sanitized sample response with all
   secret fields already redacted by the person providing it.

## Priority 3 — Blocks Web Intelligence dependency extraction

8. **WebI document discovery contract.** Endpoint/filter mechanism to list documents dependent
   on a given universe CUID, and to fetch one document's metadata.
   *Source needed:* the Web Intelligence REST API reference section of the guide, or a sanitized
   sample response. (Any module name such as "raylight" seen in community material is
   **unconfirmed** and must not be used as fact until verified against an official source.)
9. **Data provider field shape.** Real field names for result objects, query filters, and
   prompts within a data provider.
   *Source needed:* sanitized sample WebI document-metadata response with at least one filter
   and one prompt.
10. **Report variable field shape.** Real field names for formula text, qualification, and
    dependency references.
    *Source needed:* sanitized sample WebI document-metadata response with at least one
    variable that has a formula.
11. **Merged dimension field shape.** Entirely unknown; no placeholder has been created to avoid
    inventing one.
    *Source needed:* sanitized sample WebI document-metadata response for a document with two or
    more data providers and a merged dimension.

## Priority 4 — Blocks security and lineage completeness

12. **Security rule extraction contract.** Whether/how row-level and object-level security can
    be read via REST vs. requiring the Java SDK or CMC-level APIs.
    *Source needed:* "Security" chapter of the RESTful Web Service Developer Guide or BI
    Semantic Layer Java SDK Developer Guide.
13. **HANA lineage enrichment scope.** Which HANA `SYS.*` catalog views/columns this
    environment's read-only service account is permitted to query, and connection details.
    *Source needed:* HANA DBA-provided read-only role/grant list and connection parameters
    (`HANA_ADDRESS`, `HANA_PORT`, `HANA_USER` are already modeled in `.env.example`; no schema
    access has been confirmed yet).

## How to Resolve an Item

For each item, provide **one** of:

- A link/PDF export of the exact, named section of an official SAP guide, or
- A sanitized (secrets/PII redacted) real request/response capture from this environment, or
- An explicit decision from the business/BI-platform owner (e.g., "UNV universes are out of
  scope for this project").

Once provided, update the corresponding section in
[businessobjects_api_requirements.md](businessobjects_api_requirements.md) from `REQUIRED_INPUT`
to `CONFIRMED` with a citation, update the placeholder shape in
[businessobjects_payload_contracts.md](businessobjects_payload_contracts.md) if it changes, and
only then implement the corresponding method body in
`src/bo_semantic_extractor/bo_client/rest_client.py`.

## Readiness Snapshot

| Priority | Items | Resolved |
|---|---|---|
| 1 — Authentication/session | 3 | 0 |
| 2 — Universe discovery/metadata | 4 | 0 |
| 3 — WebI dependencies | 4 | 0 |
| 4 — Security/lineage | 2 | 0 |
| **Total** | **13** | **0** |
