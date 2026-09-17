package com.vistance.bo.routeb;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Self-contained, read-only provider discovery: JAR walk, filtering, class enumeration,
 * reflection, progress logging, and diagnostics all run inside this single JVM process.
 * PowerShell only compiles and launches; it never serializes a handoff to this probe.
 * Never opens a CMS session, never instantiates SDK classes.
 */
public final class ProviderDiscoveryProbe {
    private static final String DATASOURCE = "com.sap.sl.datasource.DataSource";
    private static final String DATAFOUNDATION = "com.businessobjects.mds.datafoundation.DataFoundation";
    private static final String[] RELATED_RETURN_TERMS = {"DataSource", "DataFoundation", "BusinessLayer", "Universe", "Workspace", "Repository"};
    private static final String[] PROVIDER_JAR_PREFIXES = {"com.sap.sl.", "com.businessobjects.mds.", "com.businessobjects.dsl.", "com.businessobjects.sdk.", "com.businessobjects.boesdk"};
    private static final String[] KNOWN_JAR_NAMES = {"cesdk.jar", "cecore.jar", "celib.jar", "cesession.jar"};
    private static final String[] IRRELEVANT_JAR_TERMS = {"eclipse", "localization", "jetty", "batik", "lucene", "poi", "axis2", "visualization", "help", "language"};
    private static final long HEARTBEAT_INTERVAL_MILLIS = 30_000L;
    private static final int MAX_SAMPLE_FAILURES = 100;
    private static final String[] TARGET_VERIFICATION_CLASSES = {
        "com.sap.sl.datasource.DataSource",
        "com.sap.sl.datasource.DataSourceElement",
        "com.sap.sl.datasource.BusinessLayer",
        "com.businessobjects.mds.datafoundation.DataFoundation",
        "com.businessobjects.mds.datafoundation.Join",
        "com.sap.sl.repository.service.RepositoryService",
        "com.sap.sl.workspace.service.WorkspaceManagerService"
    };

    private static Path progressLog;

    private ProviderDiscoveryProbe() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("Usage: ProviderDiscoveryProbe <sap-install-root> <idt-plugin-directory> <output-directory>");
        Path sapInstallRoot = Paths.get(args[0]);
        Path idtPluginDirectory = Paths.get(args[1]);
        Path output = Paths.get(args[2]);
        Files.createDirectories(output);
        progressLog = output.resolve("discovery_progress.log");
        try {
            run(sapInstallRoot, idtPluginDirectory, output);
        } catch (Exception error) {
            log("FAILURE " + error.getMessage());
            throw error;
        }
    }

    private static void run(Path sapInstallRoot, Path idtPluginDirectory, Path output) throws Exception {
        log("START");
        List<Path> jars = findJars(sapInstallRoot, idtPluginDirectory);
        if (jars.isEmpty()) throw new IllegalStateException("MISSING_SDK_JARS: no SDK jars under " + sapInstallRoot + " or " + idtPluginDirectory);

        List<Path> included = new ArrayList<>();
        List<Map<String, Object>> exclusions = new ArrayList<>();
        for (Path jar : jars) {
            String lowerName = jar.getFileName().toString().toLowerCase(Locale.ROOT);
            boolean selected = isKnownName(lowerName) || startsWithProviderPrefix(lowerName);
            if (selected) {
                included.add(jar);
            } else {
                String reason = "jar name does not match a provider runtime family";
                String matched = matchIrrelevant(lowerName);
                if (matched != null) reason = "excluded irrelevant bundle family: " + matched;
                Map<String, Object> exclusion = new LinkedHashMap<>();
                exclusion.put("file_name", jar.getFileName().toString());
                exclusion.put("absolute_path", jar.toAbsolutePath().toString());
                exclusion.put("reason", reason);
                exclusions.add(exclusion);
            }
        }
        if (included.size() >= jars.size()) throw new IllegalStateException("PROVIDER_SCAN_FILTER_FAILURE: filtering did not reduce the scan set");
        log("PROVIDER_SCAN FILTERED total=" + jars.size() + " included=" + included.size() + " excluded=" + exclusions.size());
        writeDocument(output.resolve("provider_scan_exclusions.json"), exclusions, null);

        // The classpath resolves against every discovered JAR so transitive dependencies
        // (e.g. EMF types referenced by SAP semantic layer classes) are resolvable, even
        // though inspection below remains scoped to the smaller provider-family JAR set.
        URL[] classpathUrls = new URL[jars.size()];
        for (int i = 0; i < jars.size(); i++) classpathUrls[i] = jars.get(i).toUri().toURL();

        try (URLClassLoader loader = new URLClassLoader(classpathUrls, ProviderDiscoveryProbe.class.getClassLoader())) {
            verifyTargetClasses(loader, output);

            List<String> classNames = new ArrayList<>();
            List<String> classJars = new ArrayList<>();
            long lastHeartbeat = System.currentTimeMillis();
            for (int jarIndex = 0; jarIndex < included.size(); jarIndex++) {
                Path jar = included.get(jarIndex);
                try (JarFile archive = new JarFile(jar.toFile())) {
                    Enumeration<JarEntry> entries = archive.entries();
                    while (entries.hasMoreElements()) {
                        JarEntry entry = entries.nextElement();
                        if (entry.isDirectory() || !entry.getName().endsWith(".class") || entry.getName().endsWith("module-info.class") || entry.getName().endsWith("package-info.class")) continue;
                        classNames.add(entry.getName().substring(0, entry.getName().length() - 6).replace('/', '.'));
                        classJars.add(jar.toAbsolutePath().toString());
                    }
                }
                long now = System.currentTimeMillis();
                if (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MILLIS || jarIndex == included.size() - 1) {
                    log("PROBE_SCOPE HEARTBEAT jar=" + (jarIndex + 1) + " of " + included.size() + " classes=" + classNames.size());
                    lastHeartbeat = now;
                }
            }
            int classesEnumerated = classNames.size();
            if (classesEnumerated < included.size() * 10) {
                Map<String, Object> scopeFailure = scopeCounters(included.size(), classesEnumerated, 0, 0, 0);
                writeFindings(output, new ArrayList<Map<String, Object>>(), scopeFailure);
                throw new IllegalStateException("PROBE_SCOPE_MISMATCH: classes_enumerated=" + classesEnumerated + ", jars=" + included.size());
            }

            List<Map<String, Object>> datasource = new ArrayList<>();
            List<Map<String, Object>> datafoundation = new ArrayList<>();
            List<Map<String, Object>> related = new ArrayList<>();
            List<Map<String, Object>> failures = new ArrayList<>();
            List<Map<String, Object>> identified = new ArrayList<>();
            int classesLoaded = 0;
            int classesSkipped = 0;
            int methodsInspected = 0;

            for (int index = 0; index < classNames.size(); index++) {
                String className = classNames.get(index);
                try {
                    Class<?> type = Class.forName(className, false, loader);
                    for (Method method : type.getDeclaredMethods()) {
                        methodsInspected++;
                        Class<?> returnType = method.getReturnType();
                        String target = targetType(returnType, loader);
                        Map<String, Object> record = methodRecord(className, classJars.get(index), method, returnType, target);
                        if (target != null) { identified.add(record); if (DATASOURCE.equals(target)) datasource.add(record); else datafoundation.add(record); }
                        if (containsRelatedTerm(returnType.getName())) related.add(record);
                    }
                    // Only counted after the class AND its declared methods resolve cleanly;
                    // a lazy NoClassDefFoundError during getDeclaredMethods() must not also
                    // count as loaded, or classesLoaded + classesSkipped double-counts classes.
                    classesLoaded++;
                } catch (ClassNotFoundException error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (NoClassDefFoundError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (ExceptionInInitializerError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (UnsatisfiedLinkError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error)); }
            }

            Map<String, Object> scope = scopeCounters(included.size(), classesEnumerated, classesLoaded, classesSkipped, methodsInspected);
            writeDocument(output.resolve("datasource_providers.json"), datasource, scope);
            writeDocument(output.resolve("datafoundation_providers.json"), datafoundation, scope);
            writeDocument(output.resolve("related_return_type_inventory.json"), related, scope);
            writeFindings(output, failures, scope);
            writeDocument(output.resolve("local_resource_loader_candidates.json"), filterLoaders(datasource, datafoundation), scope);
            writeDocument(output.resolve("provider_candidates.json"), identified, scope);

            log("PROBE_SCOPE jars=" + scope.get("jars"));
            log("PROBE_SCOPE classes_enumerated=" + scope.get("classes_enumerated"));
            log("PROBE_SCOPE classes_loaded=" + scope.get("classes_loaded"));
            log("PROBE_SCOPE classes_skipped=" + scope.get("classes_skipped"));
            log("PROBE_SCOPE methods_inspected=" + scope.get("methods_inspected"));
        }

        writeHashes(output);
        String report = "# Milestone 2B Execution Report\n\n- Status: PROVIDER_DISCOVERY_COMPLETE\n- CMS connection attempted: false\n"
            + "- Provider scan total: " + jars.size() + "\n- Provider scan included: " + included.size() + "\n- Provider scan excluded: " + exclusions.size() + "\n"
            + "- Provider scan: in-process JAR walk and filtering; classpath resolves against all discovered JARs; inspection scoped to provider-family JARs\n";
        Files.write(output.resolve("execution_report.md"), report.getBytes(StandardCharsets.UTF_8));
        log("COMPLETE");
    }

    // Fails fast: a full sweep is pointless if the known target types cannot even resolve.
    private static void verifyTargetClasses(ClassLoader loader, Path output) throws IOException {
        List<Map<String, Object>> results = new ArrayList<>();
        List<String> failedClasses = new ArrayList<>();
        for (String className : TARGET_VERIFICATION_CLASSES) {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("class", className);
            try {
                Class.forName(className, false, loader);
                result.put("status", "LOADED");
            } catch (ClassNotFoundException | LinkageError error) {
                result.put("status", "FAILED");
                result.put("error_type", error.getClass().getSimpleName());
                result.put("error_message", error.getMessage());
                result.put("missing_dependency", missingDependencyName(error));
                failedClasses.add(className);
            }
            results.add(result);
        }
        writeDocument(output.resolve("target_class_load_verification.json"), results, null);
        if (!failedClasses.isEmpty()) {
            throw new IllegalStateException("TARGET_CLASSES_UNLOADABLE: " + String.join(", ", failedClasses));
        }
    }

    private static List<Path> findJars(Path... roots) throws IOException {
        List<Path> jars = new ArrayList<>();
        for (Path root : roots) {
            if (!Files.isDirectory(root)) continue;
            Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                    if (file.getFileName().toString().toLowerCase(Locale.ROOT).endsWith(".jar")) jars.add(file.toAbsolutePath());
                    return FileVisitResult.CONTINUE;
                }
            });
        }
        jars.sort(Comparator.comparing(Path::toString));
        List<Path> unique = new ArrayList<>();
        String previous = null;
        for (Path jar : jars) { String current = jar.toString(); if (!current.equals(previous)) unique.add(jar); previous = current; }
        return unique;
    }

    private static boolean isKnownName(String lowerName) { for (String known : KNOWN_JAR_NAMES) if (known.equals(lowerName)) return true; return false; }
    private static boolean startsWithProviderPrefix(String lowerName) { for (String prefix : PROVIDER_JAR_PREFIXES) if (lowerName.startsWith(prefix)) return true; return false; }
    private static String matchIrrelevant(String lowerName) { for (String term : IRRELEVANT_JAR_TERMS) if (lowerName.contains(term)) return term; return null; }

    private static Map<String, Object> scopeCounters(int jars, int classesEnumerated, int classesLoaded, int classesSkipped, int methodsInspected) {
        Map<String, Object> scope = new LinkedHashMap<>();
        scope.put("jars", jars); scope.put("classes_enumerated", classesEnumerated); scope.put("classes_loaded", classesLoaded); scope.put("classes_skipped", classesSkipped); scope.put("methods_inspected", methodsInspected);
        return scope;
    }

    private static String targetType(Class<?> returnType, ClassLoader loader) {
        try { Class<?> target = Class.forName(DATASOURCE, false, loader); if (target.isAssignableFrom(returnType)) return DATASOURCE; } catch (ClassNotFoundException ignored) { }
        try { Class<?> target = Class.forName(DATAFOUNDATION, false, loader); if (target.isAssignableFrom(returnType)) return DATAFOUNDATION; } catch (ClassNotFoundException ignored) { }
        return null;
    }

    private static Map<String, Object> methodRecord(String className, String jar, Method method, Class<?> returnType, String target) {
        Map<String, Object> record = new LinkedHashMap<>(); record.put("declaring_class", method.getDeclaringClass().getName()); record.put("candidate_class", className); record.put("jar", jar); record.put("method_name", method.getName()); record.put("signature", method.toGenericString()); record.put("parameter_types", parameterNames(method)); record.put("static", Modifier.isStatic(method.getModifiers())); record.put("return_type", returnType.getName()); if (target != null) record.put("provider_type", target); record.put("read_only_assessment", readOnlyAssessment(method)); return record;
    }

    private static boolean containsRelatedTerm(String name) { for (String term : RELATED_RETURN_TERMS) if (name.contains(term)) return true; return false; }

    private static Map<String, Object> failure(String name, String jar, Throwable error) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("candidate_class", name);
        result.put("jar", jar);
        result.put("status", "CLASS_LOAD_FAILED");
        result.put("detail", error.getClass().getSimpleName());
        String missing = missingDependencyName(error);
        if (missing != null) result.put("missing_dependency", missing);
        return result;
    }

    // NoClassDefFoundError messages are typically slash-separated binary names; report them
    // as dotted type names so the missing transitive dependency is immediately readable.
    private static String missingDependencyName(Throwable error) {
        if (!(error instanceof NoClassDefFoundError)) return null;
        String message = error.getMessage();
        if (message == null) return null;
        return message.replace('/', '.');
    }

    private static List<String> parameterNames(Method method) { List<String> result = new ArrayList<>(); for (Class<?> parameter : method.getParameterTypes()) result.add(parameter.getName()); return result; }
    private static String readOnlyAssessment(Method method) { String name = method.getName().toLowerCase(Locale.ROOT); return name.contains("create") || name.contains("save") || name.contains("publish") || name.contains("delete") || name.contains("update") || name.contains("set") || name.contains("convert") ? "WRITE_CAPABLE_NAME_REJECTED" : "READ_ONLY_CANDIDATE"; }
    private static List<Map<String, Object>> filterLoaders(List<Map<String, Object>> first, List<Map<String, Object>> second) { List<Map<String, Object>> result = new ArrayList<>(); for (Map<String, Object> item : first) if (!"WRITE_CAPABLE_NAME_REJECTED".equals(item.get("read_only_assessment"))) result.add(item); for (Map<String, Object> item : second) if (!"WRITE_CAPABLE_NAME_REJECTED".equals(item.get("read_only_assessment"))) result.add(item); return result; }

    // Caps individual records; aggregates carry the full picture without a multi-MB file.
    private static void writeFindings(Path output, List<Map<String, Object>> failures, Map<String, Object> scope) throws IOException {
        Map<String, Integer> byErrorType = new LinkedHashMap<>();
        Map<String, Integer> byJar = new LinkedHashMap<>();
        Map<String, Integer> byPackagePrefix = new LinkedHashMap<>();
        for (Map<String, Object> item : failures) {
            increment(byErrorType, String.valueOf(item.get("detail")));
            increment(byJar, Paths.get(String.valueOf(item.get("jar"))).getFileName().toString());
            increment(byPackagePrefix, packagePrefix(String.valueOf(item.get("candidate_class"))));
        }
        List<Map<String, Object>> sample = failures.size() > MAX_SAMPLE_FAILURES ? new ArrayList<>(failures.subList(0, MAX_SAMPLE_FAILURES)) : failures;
        Map<String, Object> document = new LinkedHashMap<>();
        document.put("status", "REFLECTION_ONLY");
        if (scope != null) document.put("scope", scope);
        document.put("total_failure_count", failures.size());
        Map<String, Object> aggregates = new LinkedHashMap<>();
        aggregates.put("by_error_type", byErrorType);
        aggregates.put("by_jar", byJar);
        aggregates.put("by_package_prefix", byPackagePrefix);
        document.put("aggregates", aggregates);
        document.put("items", sample);
        Files.write(output.resolve("provider_discovery_findings.json"), (StableJson.jsonValue(document) + "\n").getBytes(StandardCharsets.UTF_8));
    }

    private static void increment(Map<String, Integer> counts, String key) { counts.merge(key, 1, Integer::sum); }
    private static String packagePrefix(String className) { String[] parts = className.split("\\."); return parts.length >= 2 ? parts[0] + "." + parts[1] : className; }

    private static void writeDocument(Path path, Object items, Map<String, Object> scope) throws IOException {
        Map<String, Object> document = new LinkedHashMap<>();
        document.put("status", "REFLECTION_ONLY");
        if (scope != null) document.put("scope", scope);
        document.put("items", items);
        Files.write(path, (StableJson.jsonValue(document) + "\n").getBytes(StandardCharsets.UTF_8));
    }

    private static void writeHashes(Path output) throws Exception {
        List<String> lines = new ArrayList<>();
        List<Path> files = new ArrayList<>();
        try (java.util.stream.Stream<Path> stream = Files.list(output)) {
            stream.filter(Files::isRegularFile).filter(path -> !path.getFileName().toString().equals("hashes.sha256")).sorted().forEach(files::add);
        }
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        for (Path file : files) {
            digest.reset();
            byte[] hash = digest.digest(Files.readAllBytes(file));
            StringBuilder hex = new StringBuilder();
            for (byte b : hash) hex.append(String.format("%02X", b));
            lines.add(hex + "  " + file.getFileName());
        }
        Files.write(output.resolve("hashes.sha256"), String.join("\n", lines).getBytes(StandardCharsets.UTF_8));
    }

    // Single writer: this process alone appends to discovery_progress.log; stdout mirrors every line.
    private static void log(String message) {
        String line = Instant.now().toString() + " " + message;
        System.out.println(line);
        try {
            Files.write(progressLog, (line + "\n").getBytes(StandardCharsets.UTF_8),
                java.nio.file.StandardOpenOption.CREATE, java.nio.file.StandardOpenOption.APPEND);
        } catch (IOException ignored) { }
    }
}

