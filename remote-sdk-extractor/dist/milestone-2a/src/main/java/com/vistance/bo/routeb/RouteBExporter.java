package com.vistance.bo.routeb;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;

/** Milestone 1 exporter boundary. It intentionally cannot connect or retrieve resources yet. */
public final class RouteBExporter {
    public static final String SCHEMA_VERSION = "route_b.sdk.v1";
    public static final String SOURCE_SYSTEM = "BO_SEMANTIC_LAYER_JAVA_SDK";

    public Map<String, Object> runtimeManifest(ExporterConfig config) {
        Map<String, Object> manifest = new LinkedHashMap<>();
        manifest.put("schema_version", SCHEMA_VERSION);
        manifest.put("run_id", "NOT_STARTED");
        manifest.put("source_system", SOURCE_SYSTEM);
        manifest.put("extraction_method", "MILESTONE_1_RUNTIME_VALIDATION_ONLY");
        manifest.put("evidence_level", "AUTHORITATIVE_SDK");
        manifest.put("verification_status", "UNKNOWN");
        manifest.put("extracted_at_utc", Instant.now().toString());
        manifest.put("cms_connection_attempted", false);
        manifest.put("config", config.asPublicMap());
        manifest.put("required_input", "SDK classpath and confirmed local resource loading API");
        return manifest;
    }

    public void export() throws RequiredInputException {
        ReadOnlyPolicy.requireReadOnly("route_b.milestone_1.export_skeleton");
        throw new RequiredInputException(
            "ROUTE_B_EXPORT_NOT_READY: CMS connection and UNX/local-resource loading are disabled "
                + "until the confirmed SDK runtime artifacts and retrieval/loading APIs are supplied."
        );
    }
}
