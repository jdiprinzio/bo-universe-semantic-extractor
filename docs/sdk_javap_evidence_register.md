# ROUTE_B_SDK — javap Evidence Register

## Runtime Namespace Reconciliation — Patch Release 11

The installed BusinessObjects 4.3 runtime does not expose the documented
`com.sap.sl.sdk.authoring.*` namespaces used by earlier evidence documents. Runtime javap
evidence is authoritative for this machine and uses:

- `com.sap.sl.datasource.*` from `com.sap.sl.sdk.jar` for the Business Layer model.
- `com.businessobjects.mds.datafoundation.*` from `com.businessobjects.mds.datafoundation.jar`
	for the Data Foundation model.

This is a namespace correction only, not a deprecation or invalidation of the previously
confirmed method evidence. The machine-readable source of truth is
`config/route_b/confirmed_sdk_capabilities.json`; its status remains `CONFIRMED_BY_JAVAP`.

**Evidence status:** `CONFIRMED_BY_JAVAP`

**Evidence source:** Post-Milestone-1 javap output supplied for the SDK prerequisite
reconciliation on 2026-09-14. The raw remote javap transcript is not present in this repository;
this register records only the classes, methods, enum values, and JAR names explicitly supplied
as authoritative evidence. No return types are inferred where the evidence supplied only the
method signature name.

**Shared verification fields:** every row below has `evidence_source=CONFIRMED_BY_JAVAP`,
`extraction_field` identifying the enabled output field, and `verification_status=CONFIRMED`.

## Business Layer

| Fully qualified class | JAR | Method signature | Extraction field | Status |
|---|---|---|---|---|
| `com.sap.sl.sdk.authoring.businesslayer.DataSourceElement` | `com.sap.sl.sdk.jar` | `getName()` | `name` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSourceElement` | `com.sap.sl.sdk.jar` | `getDescription()` | `description` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSourceElement` | `com.sap.sl.sdk.jar` | `getIdentifier()` | `identifier` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayerItem` | `com.sap.sl.sdk.jar` | `getPath()` | `path` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayerItem` | `com.sap.sl.sdk.jar` | `getFullPath()` | `full_path` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSource` | `com.sap.sl.sdk.jar` | `getBusinessLayer()` | `business_layer` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSource` | `com.sap.sl.sdk.jar` | `getPrompts()` | `prompts` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSource` | `com.sap.sl.sdk.jar` | `getListsOfValues()` | `lists_of_values` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSource` | `com.sap.sl.sdk.jar` | `getContexts()` | `contexts` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.DataSource` | `com.sap.sl.sdk.jar` | `getBusinessLayerItemFlatList()` | `business_layer_item_flat_list` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayer` | `com.sap.sl.sdk.jar` | `getDimensions()` | `dimensions` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayer` | `com.sap.sl.sdk.jar` | `getMeasures()` | `measures` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayer` | `com.sap.sl.sdk.jar` | `getFilters()` | `filters` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayer` | `com.sap.sl.sdk.jar` | `getHierarchies()` | `hierarchies` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.BusinessLayer` | `com.sap.sl.sdk.jar` | `getAnalysisDimensions()` | `analysis_dimensions` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.Dimension` | `com.sap.sl.sdk.jar` | `getAttributes()` | `attributes` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.businesslayer.Measure` | `com.sap.sl.sdk.jar` | `getDefaultAggregation()` | `default_aggregation` | CONFIRMED_BY_JAVAP |

## Data Foundation

| Fully qualified class | JAR | Method signature | Extraction field | Status |
|---|---|---|---|---|
| `com.sap.sl.sdk.authoring.datafoundation.DataFoundation` | `com.sap.sl.sdk.jar` | `getTables()` | `tables` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.DataFoundation` | `com.sap.sl.sdk.jar` | `getJoins()` | `joins` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.DataFoundation` | `com.sap.sl.sdk.jar` | `getContexts()` | `contexts` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Table` | `com.sap.sl.sdk.jar` | `getColumns()` | `columns` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLTable` | `com.sap.sl.sdk.jar` | `getOwner()` | `owner` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLTable` | `com.sap.sl.sdk.jar` | `getQualifier()` | `qualifier` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLTable` | `com.sap.sl.sdk.jar` | `getType()` | `table_type` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.AliasTable` | `com.sap.sl.sdk.jar` | `getAliasedTable()` | `aliased_table` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.DerivedTable` | `com.sap.sl.sdk.jar` | `getExpression()` | `derived_expression` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.DerivedTable` | `com.sap.sl.sdk.jar` | `getEncodedExpression()` | `encoded_derived_expression` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getLeftColumns()` | `left_columns` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getRightColumns()` | `right_columns` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getExpression()` | `join_expression` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getCardinality()` | `cardinality` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getLeftTable()` | `left_table` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Join` | `com.sap.sl.sdk.jar` | `getRightTable()` | `right_table` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLJoin` | `com.sap.sl.sdk.jar` | `getOuterType()` | `outer_type` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLJoin` | `com.sap.sl.sdk.jar` | `getOperator()` | `operator` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLJoin` | `com.sap.sl.sdk.jar` | `isAutoJoin()` | `auto_join` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.SQLJoin` | `com.sap.sl.sdk.jar` | `isCustom()` | `custom` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Context` | `com.sap.sl.sdk.jar` | `getJoins()` | `joins` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.Context` | `com.sap.sl.sdk.jar` | `getExcludedJoins()` | `excluded_joins` | CONFIRMED_BY_JAVAP |

## Enum Values

| Fully qualified class | JAR | Confirmed values | Extraction field | Status |
|---|---|---|---|---|
| `com.sap.sl.sdk.authoring.datafoundation.Cardinality` | `com.sap.sl.sdk.jar` | `CUNKNOWN`, `C1_1`, `C1_N`, `CN_1`, `CN_N` | `cardinality` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.OuterType` | `com.sap.sl.sdk.jar` | `OUTER_NONE`, `OUTER_LEFT`, `OUTER_RIGHT`, `OUTER_FULL`, `OUTER_UNKNOWN` | `outer_type` | CONFIRMED_BY_JAVAP |
| `com.sap.sl.sdk.authoring.datafoundation.JoinOperator` | `com.sap.sl.sdk.jar` | `EQUAL`, `NOT_EQUAL`, `GREATER`, `GREATER_OR_EQUAL`, `LESS`, `LESS_OR_EQUAL`, `COMPLEX`, `UNKNOWN` | `operator` | CONFIRMED_BY_JAVAP |

## JAR Set

The post-Milestone-1 evidence confirms these core JARs are required/available on the remote
runtime: `com.sap.sl.sdk.jar`, `com.sap.sl.edp.relational.jar`, `com.sap.sl.edp.hana.jar`, and
`com.businessobjects.mds.datafoundation.jar`. The complete transitive classpath remains a true
required input; this register does not claim those four JARs are sufficient by themselves.
