"""Static Java import validator.

Parses each .java source, collects referenced simple type names that are used in
positions requiring an imported/declared/java.lang type, and verifies each name is
either imported, declared in the same file, in the same package, or in java.lang.
This intentionally does not invoke javac; it is a fast local approximation used to
catch missing-import defects (like a missing `java.nio.charset.StandardCharsets`
import) before a run reaches the remote BusinessObjects machine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)(\.\*)?\s*;", re.MULTILINE)
_DECLARED_TYPE_RE = re.compile(r"\b(?:class|interface|enum)\s+(\w+)")
_STRING_OR_COMMENT_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/', re.DOTALL
)
# Types referenced as java.nio.charset.StandardCharsets.UTF_8, new Foo(...), Foo.bar(),
# or as a declared variable/parameter/return type: Foo x, List<Foo>, (Foo) cast, etc.
_TYPE_USAGE_RE = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")

# Common java.lang members that are frequently referenced without ambiguity.
_JAVA_LANG_TYPES = {
    "String", "Object", "Integer", "Long", "Boolean", "Double", "Float", "Short",
    "Byte", "Character", "Class", "Exception", "RuntimeException", "Throwable",
    "Error", "System", "Thread", "Runnable", "Iterable", "Comparable", "Number",
    "StringBuilder", "StringBuffer", "Math", "Void", "IllegalArgumentException",
    "IllegalStateException", "NullPointerException", "UnsupportedOperationException",
    "ClassNotFoundException", "NoClassDefFoundError", "ExceptionInInitializerError",
    "UnsatisfiedLinkError", "LinkageError", "AutoCloseable", "Override", "Deprecated",
    "SuppressWarnings", "FunctionalInterface", "SafeVarargs",
}


@dataclass(frozen=True)
class MissingImport:
    file: Path
    line: int
    type_name: str


def _strip_strings_and_comments(source: str) -> str:
    return _STRING_OR_COMMENT_RE.sub(lambda match: " " * len(match.group(0)), source)


def _line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def find_missing_imports(path: Path, same_package_types: set[str] | None = None) -> list[MissingImport]:
    source = path.read_text(encoding="utf-8")
    stripped = _strip_strings_and_comments(source)

    package_match = _PACKAGE_RE.search(stripped)
    package_name = package_match.group(1) if package_match else ""

    imported_simple_names: set[str] = set()
    wildcard_packages: set[str] = set()
    for match in _IMPORT_RE.finditer(stripped):
        target, is_wildcard = match.group(1), match.group(2)
        if is_wildcard:
            wildcard_packages.add(target)
        else:
            imported_simple_names.add(target.rsplit(".", 1)[-1])

    declared_types = set(_DECLARED_TYPE_RE.findall(stripped))

    known_names = imported_simple_names | declared_types | _JAVA_LANG_TYPES | (same_package_types or set())

    missing: dict[str, int] = {}
    for match in _TYPE_USAGE_RE.finditer(stripped):
        name = match.group(1)
        if name in known_names or wildcard_packages:
            continue
        if name.isupper():
            # SCREAMING_SNAKE_CASE identifiers are constant fields, not type names.
            continue
        if name in missing:
            continue
        # Only flag names that look like a fully-qualified reference was intended,
        # i.e. they appear immediately after a '.' that starts a java.* / com.* chain,
        # or as a bare capitalized identifier with no import/declaration/java.lang match
        # AND the source elsewhere spells out a partial qualified prefix ending before it
        # (e.g. `java.nio.charset.StandardCharsets`) with no corresponding import.
        preceding = stripped[max(0, match.start() - 40):match.start()]
        if re.search(r"[\w.]+\.$", preceding):
            qualifier_match = re.search(r"([\w.]+)\.$", preceding)
            qualifier = qualifier_match.group(1) if qualifier_match else ""
            full_reference = f"{qualifier}.{name}"
            if "." in qualifier and not full_reference.startswith(package_name + "."):
                # A fully-qualified usage like java.nio.charset.StandardCharsets.UTF_8
                # does not require an import; skip.
                continue
        missing[name] = _line_of(stripped, match.start())

    # Only report names that are used as a *bare* qualifier immediately before a
    # member access without any qualifying package prefix, e.g. `StandardCharsets.UTF_8`.
    confirmed_missing: list[MissingImport] = []
    for name, line in missing.items():
        bare_usage = re.search(rf"(?<![\w.]){name}\s*\.\s*[A-Za-z_]", stripped)
        if bare_usage:
            confirmed_missing.append(MissingImport(file=path, line=line, type_name=name))
    return confirmed_missing


def validate_directory(directory: Path) -> list[MissingImport]:
    paths = sorted(directory.rglob("*.java"))
    same_package_types: set[str] = set()
    for path in paths:
        same_package_types.update(_DECLARED_TYPE_RE.findall(_strip_strings_and_comments(path.read_text(encoding="utf-8"))))
    findings: list[MissingImport] = []
    for path in paths:
        findings.extend(find_missing_imports(path, same_package_types))
    return findings


def format_failure(findings: list[MissingImport]) -> str:
    details = "; ".join(f"{item.file.name}:{item.line} missing {item.type_name}" for item in findings)
    return f"JAVA_IMPORT_VALIDATION_FAILURE: {details}"
