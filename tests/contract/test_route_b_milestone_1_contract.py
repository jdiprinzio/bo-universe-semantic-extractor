"""Local contract tests for ROUTE_B_SDK Milestone 1.

These tests intentionally do not require SAP JARs, a Java runtime, or CMS connectivity. They
validate repository-owned schemas, configuration, source-level safety markers, and the explicit
REQUIRED_INPUT boundary for the remote exporter.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "config" / "schemas" / "route_b"
JAVA_DIR = REPO_ROOT / "remote-sdk-extractor" / "src" / "main" / "java" / "com" / "vistance" / "bo" / "routeb"

EXPECTED_SCHEMAS = {
    "business_layer.schema.json",
    "common.schema.json",
    "connection_metadata.schema.json",
    "context_metadata.schema.json",
    "data_foundation.schema.json",
    "join_metadata.schema.json",
    "lineage_edges.schema.json",
}


def test_route_b_schema_inventory_is_complete_and_valid_json() -> None:
    assert {path.name for path in SCHEMA_DIR.glob("*.json")} == EXPECTED_SCHEMAS
    for path in SCHEMA_DIR.glob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert document["$id"].endswith(path.name)


def test_route_b_contracts_require_common_evidence_fields() -> None:
    for path in SCHEMA_DIR.glob("*.schema.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        if path.name == "common.schema.json":
            assert set(document["required"]) >= {
                "source_system",
                "extraction_method",
                "evidence_level",
                "verification_status",
            }
        else:
            assert {"$ref": "common.schema.json"} in document["allOf"]


def test_lineage_contract_forbids_fabricated_hana_values() -> None:
    document = json.loads((SCHEMA_DIR / "lineage_edges.schema.json").read_text(encoding="utf-8"))
    properties = document["properties"]["items"]["items"]["properties"]
    assert properties["physical_hana_object"]["const"] == "UNKNOWN"
    assert properties["physical_hana_column"]["const"] == "UNKNOWN"


def test_universe_config_is_shared_and_non_secret() -> None:
    profile = yaml.safe_load(
        (REPO_ROOT / "config" / "universes" / "dm_invoice_data_mart.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert profile["universe"]["slug"] == "dm_invoice_data_mart"
    assert profile["route_b"]["enabled"] is True
    assert profile["route_b"]["save_for_all_users"] is False
    assert "password" not in json.dumps(profile).lower()


def test_java_skeleton_has_read_only_and_required_input_boundaries() -> None:
    read_only = (JAVA_DIR / "ReadOnlyPolicy.java").read_text(encoding="utf-8")
    exporter = (JAVA_DIR / "RouteBExporter.java").read_text(encoding="utf-8")
    assert "publish" in read_only and "save" in read_only and "create" in read_only
    assert "RequiredInputException" in exporter
    assert "cms_connection_attempted" in exporter
    assert "CMS connection" in exporter


def test_java_skeleton_contains_no_live_cms_logon_or_write_calls() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in JAVA_DIR.glob("*.java"))
    assert "CrystalEnterprise.getSessionMgr().logon" not in source
    assert ".publish(" not in source
    assert ".save(" not in source
    assert ".create(" not in source
