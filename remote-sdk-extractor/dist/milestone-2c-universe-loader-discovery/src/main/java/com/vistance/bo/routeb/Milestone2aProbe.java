package com.vistance.bo.routeb;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Reflection-only probe. It never creates a CMS session or loads a universe resource. */
public final class Milestone2aProbe {
    private Milestone2aProbe() {
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            throw new IllegalArgumentException("Usage: Milestone2aProbe <confirmed_classes.txt> <output.json>");
        }
        Path capabilityPath = Paths.get(args[0]);
        List<String> capabilities = readConfirmedClasses(capabilityPath);
        List<String> loaded = new ArrayList<>();
        Map<String, String> missing = new LinkedHashMap<>();
        for (String className : capabilities) {
            try {
                Class.forName(className, false, Milestone2aProbe.class.getClassLoader());
                loaded.add(className);
            } catch (ClassNotFoundException | LinkageError error) {
                missing.putIfAbsent(className, error.getClass().getSimpleName() + ", expected jar: UNKNOWN");
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("status", missing.isEmpty() ? "CONFIRMED" : "MISSING_CONFIRMED_CLASSES");
        result.put("cms_connection_attempted", false);
        result.put("reflection_only", true);
        result.put("loaded_classes", loaded);
        List<String> missingDetails = new ArrayList<>();
        for (Map.Entry<String, String> entry : missing.entrySet()) {
            missingDetails.add(entry.getKey() + " (" + entry.getValue() + ")");
        }
        result.put("missing_classes", missingDetails);
        writeJson(Paths.get(args[1]), result);
        if (!missing.isEmpty()) {
            throw new RequiredInputException("MISSING_CONFIRMED_CLASSES: " + String.join(", ", missingDetails));
        }
    }

    static List<String> readConfirmedClasses(Path path) throws IOException {
        List<String> classes = new ArrayList<>();
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            String className = line.trim();
            if (className.length() > 0 && !className.startsWith("#")) classes.add(className);
        }
        if (classes.isEmpty()) {
            throw new IOException("CAPABILITY_HANDOFF_FAILURE: no confirmed classes");
        }
        return classes;
    }


    private static void writeJson(Path path, Map<String, Object> result) throws IOException {
        StringBuilder json = new StringBuilder("{");
        json.append("\"status\":").append(StableJson.string(result.get("status").toString()));
        json.append(",\"cms_connection_attempted\":false");
        json.append(",\"reflection_only\":true");
        appendArray(json, "loaded_classes", (List<String>) result.get("loaded_classes"));
        appendArray(json, "missing_classes", (List<String>) result.get("missing_classes"));
        json.append("}\n");
        Files.createDirectories(path.getParent());
        Files.write(path, json.toString().getBytes(StandardCharsets.UTF_8));
    }

    private static void appendArray(StringBuilder json, String key, List<String> values) {
        json.append(",").append(StableJson.string(key)).append(":");
        json.append("[");
        for (int i = 0; i < values.size(); i++) {
            if (i > 0) json.append(",");
            json.append(StableJson.string(values.get(i)));
        }
        json.append("]");
    }
}
