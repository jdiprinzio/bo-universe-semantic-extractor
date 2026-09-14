# SAP BusinessObjects API Requirements

**Status:** Research document. No endpoint paths in this document have been used in code.
The `RestSemanticLayerClient` implementation (`src/bo_semantic_extractor/bo_client/rest_client.py`)
continues to raise `SdkUnavailableError` for every operation until the `REQUIRED_INPUT` items
below are resolved and an endpoint is explicitly confirmed and configured.

## 1. Purpose and Scope

This document records what is currently known — and, more importantly, what is **not** yet
known — about the exact SAP BusinessObjects Semantic Layer REST API and Web Intelligence REST
API surface needed by this extraction pipeline. Per the `bo-universe-semantic-extractor` skill,
endpoint paths must never be fabricated. Every capability the pipeline needs is listed with:

- **CONFIRMED** — verified in this research session against an identifiable, citable source.
- **REQUIRED_INPUT** — not verified; the exact documentation section, Postman collection, or
  sanitized payload sample needed to confirm it is listed explicitly.

## 2. Research Method and Session Evidence

The following sources were consulted in this research session (2026-09-10):

| Source | Result |
|---|---|
| `https://help.sap.com/docs/SAP_BUSINESSOBJECTS_BUSINESS_INTELLIGENCE_PLATFORM/` | **Confirmed to exist.** Landing page enumerates the official guide catalog for BI Platform 2025 / 4.3. |
| `https://help.sap.com/docs/SAP_BUSINESSOBJECTS_BUSINESS_INTELLIGENCE_PLATFORM/db6a17c0d1214fd6971de66ea0122378` — *Business Intelligence Platform RESTful Web Service Developer Guide* | **Confirmed to exist** (title, URL, "Last updated for 4.3"). The fetched page only rendered the document-history/navigation shell; the endpoint reference content itself is served by a JavaScript single-page app and was **not retrievable** as plain text in this session. |
| `https://help.sap.com/docs/SAP_BUSINESSOBJECTS_BUSINESS_INTELLIGENCE_PLATFORM/4359a0ef221e4a1098bae432bdd982c1` — *BI Semantic Layer Java SDK Developer Guide* | **Confirmed to exist.** Relevant because the skill's source priority lists the Semantic Layer Java SDK as a fallback for design-time metadata not exposed via REST. |
| `https://help.sap.com/doc/4a2ba099c48c407883106dc4ff5bc243/4.4/en-US/index.html` — *SAP Business Intelligence Semantic Layer Java SDK API* (Javadoc) | **Confirmed to exist** (title only; Javadoc contents not fetched in this session). |
| SAP Community blog search for BI Platform RESTful Web Services usage examples | **No relevant, citable result retrieved** in this session (search returned an unrelated blog post). |
| `https://github.com/SAP/BI-platform-restful-webservices` | **404 — repository does not exist at this path.** No official SAP GitHub sample repository was located at this URL. |

**Conclusion of this research pass:** the existence and titles of the two governing guides are
confirmed, but the actual endpoint paths, request/response payload shapes, and header names
documented inside them were not retrievable as text in this session. Every endpoint below is
therefore `REQUIRED_INPUT` unless stated otherwise.

## 3. Authentication Methods

| Item | Status |
|---|---|
| Which auth method(s) this BI Platform deployment supports (`secEnterprise`, `secLDAP`, `secWinAD`, `secSAPR3`, OAuth/SAML via BI platform SSO) | REQUIRED_INPUT |
| Exact logon request path, HTTP method, and request body/query-parameter shape | REQUIRED_INPUT |
| Exact success response shape and the header/cookie/token name used for subsequent authenticated requests | REQUIRED_INPUT |
| Logoff/session-termination request path and method | REQUIRED_INPUT |

**REQUIRED_INPUT — exact source needed:** the "Getting Started" / "Authentication" chapter of the
*Business Intelligence Platform RESTful Web Service Developer Guide* (confirmed to exist, URL
above), retrieved as text or PDF, OR a sanitized `curl`/Postman capture of a real logon
request/response pair (with credentials and tokens redacted) from this environment's BI platform
instance.

`config.py` already models `BO_BASE_URL`, `BO_AUTH_TYPE`, `BO_USERNAME`, `BO_PASSWORD` generically
so no rework is needed once the exact logon contract is confirmed — only `rest_client.py` changes.

## 4. Session Management

| Item | Status |
|---|---|
| Session token lifetime / expiry behavior | REQUIRED_INPUT |
| Whether the client must proactively refresh/renew a session vs. re-authenticate on 401 | REQUIRED_INPUT |
| Concurrent-session limits relevant to a scheduled extraction job | REQUIRED_INPUT |

**REQUIRED_INPUT — exact source needed:** "Session Management" chapter of the RESTful Web Service
Developer Guide, or CMC session-timeout configuration documentation for this environment.

## 5. Semantic Layer Universe Discovery APIs

| Item | Status |
|---|---|
| Endpoint to list/search published universes (UNX) visible to the authenticated user | REQUIRED_INPUT |
| Endpoint/parameter to resolve a universe by exact name vs. CUID | REQUIRED_INPUT |
| Whether UNV (legacy) universes are discoverable through the same REST surface or require the Java SDK / IDT export path | REQUIRED_INPUT |

**Interface already defined (no endpoint invented):**
`SemanticLayerClient.list_universes() -> list[UniverseSummary]`
(`src/bo_semantic_extractor/bo_client/base.py`).

**REQUIRED_INPUT — exact source needed:** "Semantic Layer" or "CMS Query Service" chapter of the
RESTful Web Service Developer Guide describing how universes are enumerated/queried, or a
sanitized sample response listing one or more universes.

## 6. Universe Metadata APIs

| Item | Status |
|---|---|
| Endpoint to fetch one universe's metadata by CUID (name, type, description, repository path, connections) | REQUIRED_INPUT |
| Field names actually returned (to confirm/replace the placeholder shape in `docs/businessobjects_payload_contracts.md`) | REQUIRED_INPUT |

**Interface already defined:** `SemanticLayerClient.get_universe(universe_cuid) -> RawArtifact`.

**REQUIRED_INPUT — exact source needed:** a sanitized sample JSON response for a single universe
metadata request, or the corresponding guide section.

## 7. Universe Object APIs

| Item | Status |
|---|---|
| Endpoint to list a universe's folders/dimensions/attributes/measures/filters/hierarchies/levels/parameters | REQUIRED_INPUT |
| Whether the response is a single page or requires explicit pagination, and the pagination contract | REQUIRED_INPUT |
| Field names for expressions (`select`/`where`), aggregation, projection function, associated dimension, list of values, hidden/deprecated flags, access level | REQUIRED_INPUT |

**Interface already defined:** `SemanticLayerClient.list_universe_objects(universe_cuid) -> list[RawArtifact]`.

**REQUIRED_INPUT — exact source needed:** a sanitized sample JSON response enumerating universe
objects across at least one of each allowed `ObjectType`, or the guide's "Universe Resources"
reference section.

## 8. Connection Metadata APIs

| Item | Status |
|---|---|
| Endpoint to fetch a universe's data-connection metadata (without secrets) | REQUIRED_INPUT |
| Which fields are safe to extract (data source type, server, database) vs. which must never be requested/logged (credentials) | REQUIRED_INPUT |

**Not yet modeled in code** (no `SemanticLayerClient` method exists for this yet — intentionally
deferred until the endpoint and safe-field list are confirmed).

**REQUIRED_INPUT — exact source needed:** "Connections" chapter of the RESTful Web Service
Developer Guide, or a sanitized sample response with all secret fields already redacted by the
person providing the sample.

## 9. Web Intelligence Document APIs

| Item | Status |
|---|---|
| Endpoint to list/search WebI documents dependent on a given universe CUID | REQUIRED_INPUT |
| Endpoint to fetch one WebI document's metadata (name, repository path, universe references, last-modified) | REQUIRED_INPUT |

**Interface already defined:**
`SemanticLayerClient.list_dependent_documents(universe_cuid) -> list[RawArtifact]`,
`SemanticLayerClient.get_document_metadata(document_cuid) -> RawArtifact`.

**REQUIRED_INPUT — exact source needed:** the Web Intelligence REST API reference (the module
commonly referred to in community material as "raylight" — **this name is unconfirmed in this
session and must not be used in code or documentation as fact until verified**), or a sanitized
sample response.

## 10. Data Provider APIs

| Item | Status |
|---|---|
| Endpoint/field path to enumerate a document's data providers (queries) | REQUIRED_INPUT |
| Field names for result objects, query filters, prompts, and query properties | REQUIRED_INPUT |

**REQUIRED_INPUT — exact source needed:** sanitized sample WebI document-metadata response
showing at least one data provider with a filter and a prompt.

## 11. Query APIs

| Item | Status |
|---|---|
| Whether/how a query definition (universe query panel state) can be read back via REST vs. only through the WebI document's stored data-provider metadata | REQUIRED_INPUT |
| Whether the Semantic Layer REST API supports *executing* a controlled query for reconciliation sampling, and its exact contract | REQUIRED_INPUT |

**REQUIRED_INPUT — exact source needed:** "Query Service" or equivalent chapter of the RESTful
Web Service Developer Guide.

## 12. Prompt APIs

| Item | Status |
|---|---|
| Field shape for prompts attached to a universe filter or a data provider (prompt text, type, default value, mandatory flag) | REQUIRED_INPUT |

**REQUIRED_INPUT — exact source needed:** sanitized sample response containing at least one
prompted filter.

## 13. Variable APIs

| Item | Status |
|---|---|
| Endpoint/field path to enumerate report-local variables in a WebI document | REQUIRED_INPUT |
| Field shape for formula text, qualification (dimension/measure/detail), and dependency references | REQUIRED_INPUT |

**Interface already defined:** normalized as `ReportVariable` (`models/webi.py`); no client method
exists yet for enumerating variables independently of `get_document_metadata`.

**REQUIRED_INPUT — exact source needed:** sanitized sample WebI document-metadata response
containing at least one report variable with a formula.

## 14. Merged Dimension APIs

| Item | Status |
|---|---|
| Field shape describing merged/synchronized dimensions across multiple data providers in one document | REQUIRED_INPUT |

**Not yet modeled in code** (no dedicated model or client method exists yet — deferred until the
field shape is confirmed).

**REQUIRED_INPUT — exact source needed:** sanitized sample WebI document-metadata response for a
document with two or more data providers and a merged dimension.

## 15. Summary Table

| Area | Interface Defined | Endpoint Confirmed | Payload Shape Confirmed |
|---|---|---|---|
| Authentication | N/A (config-level) | No | No |
| Session management | N/A | No | No |
| Universe discovery | Yes | No | No |
| Universe metadata | Yes | No | No |
| Universe objects | Yes | No | No |
| Connection metadata | No | No | No |
| WebI documents | Yes | No | No |
| Data providers | Yes (model only) | No | No |
| Query APIs | No | No | No |
| Prompts | Yes (model field only) | No | No |
| Variables | Yes (model only) | No | No |
| Merged dimensions | No | No | No |

See [businessobjects_missing_inputs.md](businessobjects_missing_inputs.md) for the consolidated,
prioritized list of everything required to move any row from "No" to "Yes".
