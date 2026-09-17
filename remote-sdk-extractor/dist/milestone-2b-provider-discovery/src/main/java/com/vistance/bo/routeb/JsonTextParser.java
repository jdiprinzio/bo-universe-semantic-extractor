package com.vistance.bo.routeb;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/** Small JSON reader for the known repository-owned array/object shapes. */
public final class JsonTextParser {
    private JsonTextParser() { }

    public static String read(Path path) throws IOException {
        return new String(Files.readAllBytes(path), StandardCharsets.UTF_8);
    }

    public static List<String> arrayObjects(String text, String arrayProperty) throws IOException {
        int key = findString(text, arrayProperty, 0);
        if (key < 0) throw new IOException("JSON_ARRAY_MISSING: " + arrayProperty);
        int colon = skipWhitespace(text, key);
        if (colon >= text.length() || text.charAt(colon) != ':') throw new IOException("JSON_ARRAY_MISSING: " + arrayProperty);
        int open = skipWhitespace(text, colon + 1);
        if (open >= text.length() || text.charAt(open) != '[') throw new IOException("JSON_ARRAY_MISSING: " + arrayProperty);
        return objectsInArray(text, open);
    }

    public static List<String> rootArrayObjects(String text) throws IOException {
        int open = skipWhitespace(text, 0);
        if (open >= text.length() || text.charAt(open) != '[') throw new IOException("JSON_ROOT_ARRAY_MISSING");
        return objectsInArray(text, open);
    }

    public static String stringProperty(String object, String property) {
        int key = findString(object, property, 0);
        if (key < 0) return null;
        int colon = skipWhitespace(object, key);
        if (colon >= object.length() || object.charAt(colon) != ':') return null;
        int value = skipWhitespace(object, colon + 1);
        if (value >= object.length() || object.charAt(value) != '"') return null;
        return readString(object, value);
    }

    public static String parseFailure(Path path, String property, String text) {
        int end = Math.min(200, text.length());
        return "INCLUDED_JARS_PARSE_FAILURE: file_size=" + text.length()
            + ", property=" + property + ", prefix=" + text.substring(0, end);
    }

    private static List<String> objectsInArray(String text, int open) throws IOException {
        List<String> objects = new ArrayList<>();
        int depth = 0;
        int objectStart = -1;
        boolean quoted = false;
        boolean escaped = false;
        for (int index = open + 1; index < text.length(); index++) {
            char current = text.charAt(index);
            if (quoted) {
                if (escaped) escaped = false;
                else if (current == '\\') escaped = true;
                else if (current == '"') quoted = false;
                continue;
            }
            if (current == '"') { quoted = true; continue; }
            if (current == '{') { if (depth == 0) objectStart = index; depth++; continue; }
            if (current == '}') {
                depth--;
                if (depth == 0 && objectStart >= 0) { objects.add(text.substring(objectStart, index + 1)); objectStart = -1; }
                continue;
            }
            if (current == ']' && depth == 0) return objects;
        }
        throw new IOException("JSON_ARRAY_UNTERMINATED");
    }

    private static int findString(String text, String expected, int start) {
        int index = start;
        while (index < text.length()) {
            int quote = text.indexOf('"', index);
            if (quote < 0) return -1;
            String value = readString(text, quote);
            if (expected.equals(value)) return skipWhitespace(text, quote + quotedLength(text, quote));
            index = quote + quotedLength(text, quote);
        }
        return -1;
    }

    private static String readString(String text, int quote) {
        StringBuilder value = new StringBuilder();
        boolean escaped = false;
        for (int index = quote + 1; index < text.length(); index++) {
            char current = text.charAt(index);
            if (escaped) {
                if (current == 'n') value.append('\n');
                else if (current == 'r') value.append('\r');
                else if (current == 't') value.append('\t');
                else value.append(current);
                escaped = false;
            } else if (current == '\\') escaped = true;
            else if (current == '"') return value.toString();
            else value.append(current);
        }
        return null;
    }

    private static int quotedLength(String text, int quote) {
        boolean escaped = false;
        for (int index = quote + 1; index < text.length(); index++) {
            char current = text.charAt(index);
            if (escaped) escaped = false;
            else if (current == '\\') escaped = true;
            else if (current == '"') return index - quote + 1;
        }
        return text.length() - quote;
    }

    private static int skipWhitespace(String text, int index) {
        while (index < text.length() && Character.isWhitespace(text.charAt(index))) index++;
        return index;
    }
}
