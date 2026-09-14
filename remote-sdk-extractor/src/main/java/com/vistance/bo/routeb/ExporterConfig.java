package com.vistance.bo.routeb;

import java.util.LinkedHashMap;
import java.util.Map;

/** Non-secret runtime settings; credentials are intentionally never modeled here. */
public final class ExporterConfig {
    private final String universeSlug;
    private final String outputDirectory;
    private final boolean cmsEnabled;

    private ExporterConfig(String universeSlug, String outputDirectory, boolean cmsEnabled) {
        this.universeSlug = universeSlug;
        this.outputDirectory = outputDirectory;
        this.cmsEnabled = cmsEnabled;
    }

    public static ExporterConfig fromEnvironment() {
        return new ExporterConfig(
            valueOrDefault("ROUTE_B_UNIVERSE_SLUG", "dm_invoice_data_mart"),
            valueOrDefault("ROUTE_B_OUTPUT_DIR", "route_b_export"),
            Boolean.parseBoolean(valueOrDefault("ROUTE_B_CMS_ENABLED", "false"))
        );
    }

    public String getUniverseSlug() {
        return universeSlug;
    }

    public String getOutputDirectory() {
        return outputDirectory;
    }

    public boolean isCmsEnabled() {
        return cmsEnabled;
    }

    public Map<String, Object> asPublicMap() {
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("universe_slug", universeSlug);
        values.put("output_directory", outputDirectory);
        values.put("cms_enabled", cmsEnabled);
        return values;
    }

    private static String valueOrDefault(String name, String fallback) {
        String value = System.getenv(name);
        return value == null || value.isEmpty() ? fallback : value;
    }
}
