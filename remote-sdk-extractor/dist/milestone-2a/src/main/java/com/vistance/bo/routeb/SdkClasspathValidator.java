package com.vistance.bo.routeb;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Checks only SAP class names confirmed in repository SDK evidence/Javadocs.
 * It does not instantiate SDK classes or connect to CMS.
 */
public final class SdkClasspathValidator {
    public static final List<String> CONFIRMED_CLASSES = Collections.unmodifiableList(Arrays.asList(
        "com.crystaldecisions.sdk.framework.IEnterpriseSession",
        "com.crystaldecisions.sdk.framework.CrystalEnterprise",
        "com.sap.sl.sdk.framework.SlContext",
        "com.sap.sl.sdk.framework.cms.CmsSessionService",
        "com.sap.sl.sdk.authoring.cms.CmsResourceService",
        "com.sap.sl.sdk.authoring.businesslayer.BusinessLayer",
        "com.sap.sl.sdk.authoring.businesslayer.BusinessLayerFactory",
        "com.sap.sl.sdk.authoring.datafoundation.DataFoundation",
        "com.sap.sl.sdk.authoring.datafoundation.DataFoundationFactory",
        "com.sap.sl.sdk.authoring.datafoundation.Join",
        "com.sap.sl.sdk.authoring.datafoundation.SQLJoin",
        "com.sap.sl.sdk.authoring.datafoundation.Cardinality",
        "com.sap.sl.sdk.authoring.datafoundation.Context",
        "com.sap.sl.sdk.authoring.connection.DatabaseConnection"
    ));

    private SdkClasspathValidator() {
    }

    public static List<String> missingConfirmedClasses(ClassLoader loader) {
        List<String> missing = new ArrayList<>();
        for (String className : CONFIRMED_CLASSES) {
            try {
                Class.forName(className, false, loader);
            } catch (ClassNotFoundException | LinkageError error) {
                missing.add(className);
            }
        }
        return missing;
    }

    public static void requireConfirmedClasspath(ClassLoader loader) throws RequiredInputException {
        List<String> missing = missingConfirmedClasses(loader);
        if (!missing.isEmpty()) {
            throw new RequiredInputException(
                "SDK_CLASSPATH_REQUIRED: missing confirmed SAP classes: " + String.join(", ", missing)
            );
        }
    }
}
