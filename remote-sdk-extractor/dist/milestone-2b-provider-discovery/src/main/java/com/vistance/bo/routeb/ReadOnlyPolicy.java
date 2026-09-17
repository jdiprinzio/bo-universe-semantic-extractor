package com.vistance.bo.routeb;

import java.util.Locale;

/** Rejects known SDK operation families that can mutate CMS or local resources. */
public final class ReadOnlyPolicy {
    private static final String[] FORBIDDEN = {
        "create", "update", "delete", "publish", "save", "change", "convert", "modify", "set"
    };

    private ReadOnlyPolicy() {
    }

    public static void requireReadOnly(String operation) throws RequiredInputException {
        String normalized = operation == null ? "" : operation.toLowerCase(Locale.ROOT);
        for (String forbidden : FORBIDDEN) {
            if (normalized.contains(forbidden)) {
                throw new RequiredInputException(
                    "READ_ONLY_POLICY: operation is not permitted in ROUTE_B_SDK: " + operation
                );
            }
        }
    }
}
