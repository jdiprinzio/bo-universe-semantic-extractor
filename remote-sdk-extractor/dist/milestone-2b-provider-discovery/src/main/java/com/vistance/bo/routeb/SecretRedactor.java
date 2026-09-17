package com.vistance.bo.routeb;

import java.util.Locale;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Redacts credentials and session material before values can reach JSON/log output. */
public final class SecretRedactor {
    public static final String REDACTED = "***REDACTED***";
    private static final Pattern KEY_VALUE = Pattern.compile(
        "(?i)(password|token|secret|authorization|cookie|set-cookie|client_secret|api[_-]?key)"
            + "\\s*[:=]\\s*([^\\s,;&\\\"']+)"
    );

    private SecretRedactor() {
    }

    public static String redact(String value) {
        if (value == null) {
            return null;
        }
        Matcher matcher = KEY_VALUE.matcher(value);
        StringBuffer result = new StringBuffer();
        while (matcher.find()) {
            matcher.appendReplacement(result, Matcher.quoteReplacement(matcher.group(1) + "=" + REDACTED));
        }
        matcher.appendTail(result);
        return result.toString();
    }

    public static Map<String, String> redactHeaders(Map<String, String> headers) {
        Map<String, String> redacted = new LinkedHashMap<>();
        for (Map.Entry<String, String> entry : headers.entrySet()) {
            String name = entry.getKey().toLowerCase(Locale.ROOT);
            if (name.equals("authorization") || name.equals("cookie") || name.equals("set-cookie")) {
                redacted.put(entry.getKey(), REDACTED);
            } else {
                redacted.put(entry.getKey(), redact(entry.getValue()));
            }
        }
        return redacted;
    }
}
