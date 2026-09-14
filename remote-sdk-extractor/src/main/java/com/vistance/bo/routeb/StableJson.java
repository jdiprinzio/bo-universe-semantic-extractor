package com.vistance.bo.routeb;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

/** Minimal deterministic JSON writer for the skeleton's dependency-free runtime. */
public final class StableJson {
    private StableJson() {
    }

    public static String object(Map<String, ?> values) {
        return mapValue(values);
    }

    private static String mapValue(Map<String, ?> values) {
        StringBuilder json = new StringBuilder("{");
        Iterator<? extends Map.Entry<String, ?>> iterator = values.entrySet().iterator();
        while (iterator.hasNext()) {
            Map.Entry<String, ?> entry = iterator.next();
            json.append(string(entry.getKey())).append(":").append(value(entry.getValue()));
            if (iterator.hasNext()) {
                json.append(",");
            }
        }
        return json.append("}").toString();
    }

    public static String string(String value) {
        if (value == null) {
            return "null";
        }
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"")
            .replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + "\"";
    }

    private static String value(Object value) {
        if (value == null) {
            return "null";
        }
        if (value instanceof Number || value instanceof Boolean) {
            return value.toString();
        }
        if (value instanceof Map<?, ?>) {
            @SuppressWarnings("unchecked")
            Map<String, ?> map = (Map<String, ?>) value;
            return mapValue(map);
        }
        if (value instanceof List<?>) {
            StringBuilder json = new StringBuilder("[");
            Iterator<?> iterator = ((List<?>) value).iterator();
            while (iterator.hasNext()) {
                json.append(value(iterator.next()));
                if (iterator.hasNext()) {
                    json.append(",");
                }
            }
            return json.append("]").toString();
        }
        return string(SecretRedactor.redact(value.toString()));
    }
}
