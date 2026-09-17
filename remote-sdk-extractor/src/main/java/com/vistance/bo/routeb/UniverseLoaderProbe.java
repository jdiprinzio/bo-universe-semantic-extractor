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
import java.lang.reflect.Parameter;

/**
 * Self-contained, read-only Universe-loader discovery reusing the Milestone 2B
 * architecture: Java owns discovery/filtering/reflection/logging; the classpath
 * resolves against every discovered JAR while inspection stays scoped to the
 * provider-family JAR subset. Reflection only; no CMS session, no instantiation.
 */
public final class UniverseLoaderProbe {
    private static final String UNIVERSE = "com.businessobjects.mds.universe.Universe";
    private static final String DATAFOUNDATION_FILE = "com.businessobjects.mds.repository.DataFoundationFile";
    private static final String UNIVERSE_HELPER = "com.businessobjects.mds.services.helpers.UniverseHelper";
    private static final String[] TARGET_VERIFICATION_CLASSES = {UNIVERSE, DATAFOUNDATION_FILE, UNIVERSE_HELPER};
    private static final String[] PROVIDER_JAR_PREFIXES = {"com.sap.sl.", "com.businessobjects.mds.", "com.businessobjects.dsl.", "com.businessobjects.sdk.", "com.businessobjects.boesdk"};
    private static final String[] KNOWN_JAR_NAMES = {"cesdk.jar", "cecore.jar", "celib.jar", "cesession.jar"};
    private static final String[] IRRELEVANT_JAR_TERMS = {"eclipse", "localization", "jetty", "batik", "lucene", "poi", "axis2", "visualization", "help", "language"};
    private static final long HEARTBEAT_INTERVAL_MILLIS = 30_000L;
    private static final int MAX_SAMPLE_FAILURES = 100;

    private static Path progressLog;

    private UniverseLoaderProbe() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("Usage: UniverseLoaderProbe <sap-install-root> <idt-plugin-directory> <output-directory>");
        Path sapInstallRoot = Paths.get(args[0]);
        Path idtPluginDirectory = Paths.get(args[1]);
        Path output = Paths.get(args[2]).resolve("universe_loader_discovery");
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
        int excludedCount = 0;
        for (Path jar : jars) {
            String lowerName = jar.getFileName().toString().toLowerCase(Locale.ROOT);
            if (isKnownName(lowerName) || startsWithProviderPrefix(lowerName)) included.add(jar); else excludedCount++;
        }
        if (included.size() >= jars.size()) throw new IllegalStateException("PROVIDER_SCAN_FILTER_FAILURE: filtering did not reduce the scan set");
        log("PROVIDER_SCAN FILTERED total=" + jars.size() + " included=" + included.size() + " excluded=" + excludedCount);

        URL[] classpathUrls = new URL[jars.size()];
        for (int i = 0; i < jars.size(); i++) classpathUrls[i] = jars.get(i).toUri().toURL();

        List<Map<String, Object>> universeProviders = new ArrayList<>();
        List<Map<String, Object>> fileBasedLoaders = new ArrayList<>();
        List<Map<String, Object>> datafoundationFileMethods = new ArrayList<>();
        List<Map<String, Object>> failures = new ArrayList<>();
        Map<String, Integer> byErrorType = new LinkedHashMap<>();
        Map<String, Integer> byJar = new LinkedHashMap<>();
        Map<String, Integer> byPackagePrefix = new LinkedHashMap<>();
        int classesEnumerated = 0;
        int classesLoaded = 0;
        int classesSkipped = 0;
        int methodsInspected = 0;

        try (URLClassLoader loader = new URLClassLoader(classpathUrls, UniverseLoaderProbe.class.getClassLoader())) {
            verifyTargetClasses(loader, output);

            Class<?> universeType = Class.forName(UNIVERSE, false, loader);
            Class<?> dataFoundationFileType = Class.forName(DATAFOUNDATION_FILE, false, loader);

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
            classesEnumerated = classNames.size();

            for (int index = 0; index < classNames.size(); index++) {
                String className = classNames.get(index);
                String jarName = classJars.get(index);
                try {
                    Class<?> type = Class.forName(className, false, loader);
                    for (Method method : type.getDeclaredMethods()) {
                        methodsInspected++;
                        Class<?> returnType = method.getReturnType();
                        if (universeType.isAssignableFrom(returnType)) {
                            Map<String, Object> record = methodRecord(className, jarName, method, returnType);
                            String classification = classifySignature(method);
                            record.put("classification", classification);
                            universeProviders.add(record);
                            if ("FILE_BASED".equals(classification)) fileBasedLoaders.add(record);
                        }
                        if (dataFoundationFileType.isAssignableFrom(returnType) || acceptsType(method, dataFoundationFileType)) {
                            datafoundationFileMethods.add(methodRecord(className, jarName, method, returnType));
                        }
                    }
                    classesLoaded++;
                } catch (ClassNotFoundException error) { classesSkipped++; recordFailure(failures, byErrorType, byJar, byPackagePrefix, className, jarName, error);
                } catch (NoClassDefFoundError error) { classesSkipped++; recordFailure(failures, byErrorType, byJar, byPackagePrefix, className, jarName, error);
                } catch (ExceptionInInitializerError error) { classesSkipped++; recordFailure(failures, byErrorType, byJar, byPackagePrefix, className, jarName, error);
                } catch (UnsatisfiedLinkError error) { classesSkipped++; recordFailure(failures, byErrorType, byJar, byPackagePrefix, className, jarName, error); }
            }
        }

        writeList(output.resolve("universe_providers.json"), universeProviders);
        writeList(output.resolve("file_based_loaders.json"), fileBasedLoaders);
        writeList(output.resolve("datafoundation_file_methods.json"), datafoundationFileMethods);

        log("PROBE_SCOPE jars=" + included.size());
        log("PROBE_SCOPE classes_enumerated=" + classesEnumerated);
        log("PROBE_SCOPE classes_loaded=" + classesLoaded);
        log("PROBE_SCOPE classes_skipped=" + classesSkipped);
        log("PROBE_SCOPE methods_inspected=" + methodsInspected);

        List<Map<String, Object>> sampleFailures = failures.size() > MAX_SAMPLE_FAILURES ? new ArrayList<>(failures.subList(0, MAX_SAMPLE_FAILURES)) : failures;
        StringBuilder report = new StringBuilder();
        report.append("# Milestone 2C Universe Loader Discovery Report\n\n");
        report.append("- Status: UNIVERSE_LOADER_DISCOVERY_COMPLETE\n- CMS connection attempted: false\n- SDK instantiation: false\n");
        report.append("- JARs total: ").append(jars.size()).append(", included: ").append(included.size()).append(", excluded: ").append(excludedCount).append("\n");
        report.append("- Universe providers found: ").append(universeProviders.size()).append("\n");
        report.append("- File-based loaders: ").append(fileBasedLoaders.size()).append("\n");
        report.append("- DataFoundationFile methods: ").append(datafoundationFileMethods.size()).append("\n");
        report.append("- classes_enumerated=").append(classesEnumerated).append(", classes_loaded=").append(classesLoaded).append(", classes_skipped=").append(classesSkipped).append(", methods_inspected=").append(methodsInspected).append("\n\n");
        report.append("## Class-load failure aggregates (total ").append(failures.size()).append(", sample capped at ").append(MAX_SAMPLE_FAILURES).append(")\n\n");
        report.append("- by_error_type: ").append(byErrorType).append("\n");
        report.append("- by_jar: ").append(byJar).append("\n");
        report.append("- by_package_prefix: ").append(byPackagePrefix).append("\n\n");
        report.append("## Sample failures\n\n");
        for (Map<String, Object> sample : sampleFailures) report.append("- ").append(sample.get("candidate_class")).append(" (").append(sample.get("detail")).append(")\n");
        Files.write(output.resolve("execution_report.md"), report.toString().getBytes(StandardCharsets.UTF_8));
        log("COMPLETE");
    }

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
                failedClasses.add(className);
            }
            results.add(result);
        }
        writeList(output.resolve("target_class_load_verification.json"), results);
        if (!failedClasses.isEmpty()) throw new IllegalStateException("TARGET_CLASSES_UNLOADABLE: " + String.join(", ", failedClasses));
    }

    private static String classifySignature(Method method) {
        Parameter[] parameters = method.getParameters();
        if (parameters.length == 0) return "FACTORY";
        boolean fileBased = false;
        boolean cmsBased = false;
        boolean workspaceBased = false;
        for (Parameter parameter : parameters) {
            String typeName = parameter.getType().getName().toLowerCase(Locale.ROOT);
            if (typeName.contains("file") || typeName.contains("path") || typeName.equals("java.lang.string") || typeName.contains("inputstream")) fileBased = true;
            if (typeName.contains("session") || typeName.contains("cuid") || typeName.contains("repositoryitem")) cmsBased = true;
            if (typeName.contains("workspace")) workspaceBased = true;
        }
        if (workspaceBased) return "WORKSPACE";
        if (cmsBased) return "CMS_BASED";
        if (fileBased) return "FILE_BASED";
        boolean allConfigLike = true;
        for (Parameter parameter : parameters) {
            String typeName = parameter.getType().getName();
            if (!typeName.startsWith("java.lang") && !parameter.getType().isPrimitive()) { allConfigLike = false; break; }
        }
        return allConfigLike ? "FACTORY" : "UNKNOWN";
    }

    private static boolean acceptsType(Method method, Class<?> type) {
        for (Class<?> parameter : method.getParameterTypes()) if (type.isAssignableFrom(parameter)) return true;
        return false;
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

    private static Map<String, Object> methodRecord(String className, String jar, Method method, Class<?> returnType) {
        Map<String, Object> record = new LinkedHashMap<>();
        record.put("declaring_class", method.getDeclaringClass().getName());
        record.put("candidate_class", className);
        record.put("jar", jar);
        record.put("method_name", method.getName());
        record.put("signature", method.toGenericString());
        List<String> parameterNames = new ArrayList<>();
        for (Class<?> parameter : method.getParameterTypes()) parameterNames.add(parameter.getName());
        record.put("parameter_types", parameterNames);
        record.put("static", Modifier.isStatic(method.getModifiers()));
        record.put("return_type", returnType.getName());
        record.put("read_only_assessment", readOnlyAssessment(method));
        return record;
    }

    private static String readOnlyAssessment(Method method) {
        String name = method.getName().toLowerCase(Locale.ROOT);
        return name.contains("create") || name.contains("save") || name.contains("publish") || name.contains("delete") || name.contains("update") || name.contains("set") || name.contains("convert") ? "WRITE_CAPABLE_NAME_REJECTED" : "READ_ONLY_CANDIDATE";
    }

    private static void recordFailure(List<Map<String, Object>> failures, Map<String, Integer> byErrorType, Map<String, Integer> byJar, Map<String, Integer> byPackagePrefix, String className, String jarName, Throwable error) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("candidate_class", className);
        result.put("jar", jarName);
        result.put("status", "CLASS_LOAD_FAILED");
        result.put("detail", error.getClass().getSimpleName());
        if (error instanceof NoClassDefFoundError && error.getMessage() != null) result.put("missing_dependency", error.getMessage().replace('/', '.'));
        failures.add(result);
        byErrorType.merge(error.getClass().getSimpleName(), 1, Integer::sum);
        byJar.merge(Paths.get(jarName).getFileName().toString(), 1, Integer::sum);
        String[] parts = className.split("\\.");
        byPackagePrefix.merge(parts.length >= 2 ? parts[0] + "." + parts[1] : className, 1, Integer::sum);
    }

    private static void writeList(Path path, Object items) throws IOException {
        Map<String, Object> document = new LinkedHashMap<>();
        document.put("status", "REFLECTION_ONLY");
        document.put("items", items);
        Files.write(path, (StableJson.jsonValue(document) + "\n").getBytes(StandardCharsets.UTF_8));
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
