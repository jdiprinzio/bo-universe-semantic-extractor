package com.vistance.bo.routeb;

import java.io.IOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/** Reflection-only provider discovery; never instantiates SDK classes or opens CMS. */
public final class ProviderDiscoveryProbe {
    private static final String DATASOURCE = "com.sap.sl.datasource.DataSource";
    private static final String DATAFOUNDATION = "com.businessobjects.mds.datafoundation.DataFoundation";
    private static final String[] RELATED_RETURN_TERMS = {"DataSource", "DataFoundation", "BusinessLayer", "Universe", "Workspace", "Repository"};

    private ProviderDiscoveryProbe() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("Usage: ProviderDiscoveryProbe <included_jars.txt> <output-dir> <confirmed_classes.txt>");
        List<JarInput> jars = readJars(Paths.get(args[0]));
        List<String> confirmedClasses = readLines(Paths.get(args[2]), "confirmed_classes.txt");
        Path output = Paths.get(args[1]);
        Files.createDirectories(output);
        List<Map<String, Object>> datasource = new ArrayList<>();
        List<Map<String, Object>> datafoundation = new ArrayList<>();
        List<Map<String, Object>> related = new ArrayList<>();
        List<Map<String, Object>> failures = new ArrayList<>();
        List<Map<String, Object>> identified = new ArrayList<>();
        List<String> classNames = new ArrayList<>();
        List<String> classJars = new ArrayList<>();
        int classesLoaded = 0;
        int classesSkipped = 0;
        int methodsInspected = 0;
        URL[] urls = new URL[jars.size()];
        for (int i = 0; i < jars.size(); i++) urls[i] = Paths.get(jars.get(i).path).toUri().toURL();
        URLClassLoader loader = new URLClassLoader(urls, ProviderDiscoveryProbe.class.getClassLoader());
        try {
            for (int jarIndex = 0; jarIndex < jars.size(); jarIndex++) {
                JarInput jar = jars.get(jarIndex);
                JarFile archive = new JarFile(jar.path);
                try {
                    Enumeration<JarEntry> entries = archive.entries();
                    while (entries.hasMoreElements()) {
                        JarEntry entry = entries.nextElement();
                        if (entry.isDirectory() || !entry.getName().endsWith(".class") || entry.getName().endsWith("module-info.class") || entry.getName().endsWith("package-info.class")) continue;
                        String className = entry.getName().substring(0, entry.getName().length() - 6).replace('/', '.');
                        classNames.add(className);
                        classJars.add(jar.path);
                    }
                } finally { archive.close(); }
                System.out.println("PROBE_SCOPE HEARTBEAT jar=" + (jarIndex + 1) + " of " + jars.size() + " classes=" + classNames.size());
            }
            int classesEnumerated = classNames.size();
            if (classesEnumerated < jars.size() * 10) {
                Map<String, Object> scopeFailure = new LinkedHashMap<>();
                scopeFailure.put("jars", jars.size());
                scopeFailure.put("classes_enumerated", classesEnumerated);
                scopeFailure.put("classes_loaded", 0);
                scopeFailure.put("classes_skipped", 0);
                scopeFailure.put("methods_inspected", 0);
                writeDocument(output.resolve("provider_discovery_findings.json"), failures, scopeFailure);
                throw new IllegalStateException("PROBE_SCOPE_MISMATCH: classes_enumerated=" + classesEnumerated + ", jars=" + jars.size());
            }
            for (int index = 0; index < classNames.size(); index++) {
                String className = classNames.get(index);
                try {
                    Class<?> type = Class.forName(className, false, loader);
                    classesLoaded++;
                    for (Method method : type.getDeclaredMethods()) {
                        methodsInspected++;
                        Class<?> returnType = method.getReturnType();
                        String target = targetType(returnType, loader);
                        Map<String, Object> record = methodRecord(className, classJars.get(index), method, returnType, target);
                        if (target != null) { identified.add(record); if (DATASOURCE.equals(target)) datasource.add(record); else datafoundation.add(record); }
                        if (containsRelatedTerm(returnType.getName())) related.add(record);
                    }
                } catch (ClassNotFoundException error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (NoClassDefFoundError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (ExceptionInInitializerError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error));
                } catch (UnsatisfiedLinkError error) { classesSkipped++; failures.add(failure(className, classJars.get(index), error)); }
            }
            Map<String, Object> scope = new LinkedHashMap<>();
            scope.put("jars", jars.size()); scope.put("classes_enumerated", classesEnumerated); scope.put("classes_loaded", classesLoaded); scope.put("classes_skipped", classesSkipped); scope.put("methods_inspected", methodsInspected);
            writeDocument(output.resolve("datasource_providers.json"), datasource, scope);
            writeDocument(output.resolve("datafoundation_providers.json"), datafoundation, scope);
            writeDocument(output.resolve("related_return_type_inventory.json"), related, scope);
            writeDocument(output.resolve("provider_discovery_findings.json"), failures, scope);
            writeDocument(output.resolve("local_resource_loader_candidates.json"), filterLoaders(datasource, datafoundation), scope);
            writeDocument(output.resolve("provider_candidates.json"), identified, scope);
        } finally { loader.close(); }
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
    private static Map<String, Object> failure(String name, String jar, Throwable error) { Map<String, Object> result = new LinkedHashMap<>(); result.put("candidate_class", name); result.put("jar", jar); result.put("status", "CLASS_LOAD_FAILED"); result.put("detail", error.getClass().getSimpleName()); return result; }
    private static List<String> parameterNames(Method method) { List<String> result = new ArrayList<>(); for (Class<?> parameter : method.getParameterTypes()) result.add(parameter.getName()); return result; }
    private static String readOnlyAssessment(Method method) { String name = method.getName().toLowerCase(); return name.contains("create") || name.contains("save") || name.contains("publish") || name.contains("delete") || name.contains("update") || name.contains("set") || name.contains("convert") ? "WRITE_CAPABLE_NAME_REJECTED" : "READ_ONLY_CANDIDATE"; }
    private static List<Map<String, Object>> filterLoaders(List<Map<String, Object>> first, List<Map<String, Object>> second) { List<Map<String, Object>> result = new ArrayList<>(); for (Map<String, Object> item : first) if (!"WRITE_CAPABLE_NAME_REJECTED".equals(item.get("read_only_assessment"))) result.add(item); for (Map<String, Object> item : second) if (!"WRITE_CAPABLE_NAME_REJECTED".equals(item.get("read_only_assessment"))) result.add(item); return result; }

    private static List<JarInput> readJars(Path path) throws IOException {
        List<JarInput> result = new ArrayList<>();
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            String location = line.trim();
            if (location.length() > 0 && !location.startsWith("#")) {
                Path jarPath = Paths.get(location);
                result.add(new JarInput(jarPath.getFileName().toString(), location));
            }
        }
        if (result.isEmpty()) throw new IOException("INCLUDED_JARS_PARSE_FAILURE: file_size=" + Files.size(path) + ", property=absolute_path, prefix=" + preview(path));
        return result;
    }
    private static String preview(Path path) throws IOException {
        String text = new String(Files.readAllBytes(path), StandardCharsets.UTF_8);
        return text.substring(0, Math.min(200, text.length())).replace("\r", "\\r").replace("\n", "\\n");
    }
    private static List<String> readLines(Path path, String label) throws IOException {
        List<String> values = new ArrayList<>();
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) { String value = line.trim(); if (value.length() > 0 && !value.startsWith("#")) values.add(value); }
        if (values.isEmpty()) throw new IOException("HANDOFF_PREFLIGHT_FAILURE: " + label + " is empty");
        return values;
    }
    private static void writeDocument(Path path, Object items, Map<String, Object> scope) throws IOException { Map<String, Object> document = new LinkedHashMap<>(); document.put("status", "REFLECTION_ONLY"); document.put("scope", scope); document.put("items", items); Files.write(path, (StableJson.jsonValue(document) + "\n").getBytes(StandardCharsets.UTF_8)); }
    private static final class JarInput { private final String name; private final String path; private JarInput(String name, String path) { this.name = name; this.path = path; } }
}
