package com.vistance.bo.routeb;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.List;

/** Dependency-free Java contract tests, run by scripts/validate-route-b.ps1. */
public final class RouteBContractTest {
    private RouteBContractTest() {
    }

    public static void main(String[] args) throws Exception {
        testSecretRedaction();
        testReadOnlyPolicy();
        testStableJson();
        testExporterFailsClosedWithoutCms();
        testManifestDoesNotContainSecrets();
        testCapabilitySchemaParsingAndClassLoading();
        testEmptyCapabilityArrayFailsClearly();
        testMalformedCapabilitySchemaFailsClearly();
        System.out.println("ROUTE_B_CONTRACT_TESTS_PASSED");
    }

    private static void testSecretRedaction() {
        String redacted = SecretRedactor.redact("password=hunter2 token=abc123 Authorization: Bearer xyz");
        require(!redacted.contains("hunter2"), "password leaked");
        require(!redacted.contains("abc123"), "token leaked");
        require(!redacted.contains("xyz"), "authorization value leaked");
    }

    private static void testReadOnlyPolicy() throws Exception {
        ReadOnlyPolicy.requireReadOnly("route_b.export_skeleton");
        expectRequiredInput(() -> ReadOnlyPolicy.requireReadOnly("CmsResourceService.publish"));
        expectRequiredInput(() -> ReadOnlyPolicy.requireReadOnly("DatabaseConnection.save"));
    }

    private static void testStableJson() {
        Map<String, Object> values = new LinkedHashMap<>();
        values.put("schema_version", "route_b.sdk.v1");
        values.put("status", "SKELETON_ONLY");
        require(
            StableJson.object(values).equals("{\"schema_version\":\"route_b.sdk.v1\",\"status\":\"SKELETON_ONLY\"}"),
            "JSON field order is not stable"
        );
    }

    private static void testExporterFailsClosedWithoutCms() throws Exception {
        RouteBExporter exporter = new RouteBExporter();
        try {
            exporter.export();
            throw new AssertionError("export unexpectedly proceeded");
        } catch (RequiredInputException expected) {
            require(expected.getMessage().contains("CMS connection"), "failure is not actionable");
        }
    }

    private static void testManifestDoesNotContainSecrets() {
        String json = StableJson.object(new RouteBExporter().runtimeManifest(ExporterConfig.fromEnvironment()));
        require(!json.toLowerCase().contains("password"), "manifest contains password field");
        require(!json.toLowerCase().contains("token"), "manifest contains token field");
        require(json.contains("cms_connection_attempted"), "manifest lacks CMS safety field");
    }

    private static void testCapabilitySchemaParsingAndClassLoading() throws Exception {
        Path file = Files.createTempFile("route-b-capabilities-", ".json");
        try {
            Files.write(file, "{\"capabilities\": [{\"class\": \"java.lang.String\"}, { \"class\" : \"java.lang.Integer\" }]}".getBytes(StandardCharsets.UTF_8));
            List<String> classes = Milestone2aProbe.readConfirmedClasses(file);
            require(classes.size() == 2, "capability class count mismatch");
            for (String name : classes) {
                Class.forName(name, false, RouteBContractTest.class.getClassLoader());
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void testEmptyCapabilityArrayFailsClearly() throws Exception {
        Path file = Files.createTempFile("route-b-empty-", ".json");
        try {
            Files.write(file, "{\"capabilities\": []}".getBytes(StandardCharsets.UTF_8));
            try {
                Milestone2aProbe.readConfirmedClasses(file);
                throw new AssertionError("empty capabilities array was accepted");
            } catch (java.io.IOException expected) {
                require(expected.getMessage().contains("no confirmed classes"), "empty array failure is not actionable");
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void testMalformedCapabilitySchemaFailsClearly() throws Exception {
        Path file = Files.createTempFile("route-b-malformed-", ".json");
        try {
            Files.write(file, "{\"items\": [{\"class\": \"java.lang.String\"}]}".getBytes(StandardCharsets.UTF_8));
            try {
                Milestone2aProbe.readConfirmedClasses(file);
                throw new AssertionError("malformed capabilities schema was accepted");
            } catch (java.io.IOException expected) {
                require(expected.getMessage().contains("capabilities array is missing"), "malformed failure is not actionable");
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    private static void expectRequiredInput(CheckedAction action) throws Exception {
        try {
            action.run();
            throw new AssertionError("operation unexpectedly permitted");
        } catch (RequiredInputException expected) {
            require(expected.getMessage().contains("READ_ONLY_POLICY"), "failure lacks policy code");
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    @FunctionalInterface
    private interface CheckedAction {
        void run() throws Exception;
    }
}
