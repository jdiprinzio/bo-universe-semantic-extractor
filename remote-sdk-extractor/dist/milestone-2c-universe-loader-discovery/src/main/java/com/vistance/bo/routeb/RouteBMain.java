package com.vistance.bo.routeb;

import java.util.Map;
import java.util.LinkedHashMap;

/** Local-only Milestone 1 command entrypoint; never opens a CMS session. */
public final class RouteBMain {
    private RouteBMain() {
    }

    public static void main(String[] args) throws Exception {
        String command = args.length == 0 ? "manifest" : args[0];
        ExporterConfig config = ExporterConfig.fromEnvironment();
        RouteBExporter exporter = new RouteBExporter();

        if ("manifest".equalsIgnoreCase(command)) {
            System.out.println(StableJson.object(exporter.runtimeManifest(config)));
            return;
        }
        if ("validate-classpath".equalsIgnoreCase(command)) {
            SdkClasspathValidator.requireConfirmedClasspath(RouteBMain.class.getClassLoader());
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("status", "CONFIRMED");
            result.put("cms_connection_attempted", false);
            System.out.println(StableJson.object(result));
            return;
        }
        if ("export".equalsIgnoreCase(command)) {
            exporter.export();
            return;
        }
        throw new IllegalArgumentException("Unknown local-only command: " + command);
    }
}
