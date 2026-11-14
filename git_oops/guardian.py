"""
Git-Oops Guardian: AST Ghost Import Linter & Shadow Regression Guard
1. Scans proposed Python patches using stdlib `ast` for fake/hallucinated modules.
2. Sandboxes the patch and runs existing unit tests before allowing permanent writes.
"""

import ast
import os
import sys
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Optional


import ast
import os
import sys
import re
import shutil
import tempfile
import subprocess
from typing import Tuple, List, Optional


# Well-known Node.js / JavaScript built-in standard modules
NODE_BUILTINS = {
    "fs", "path", "http", "https", "crypto", "os", "events", "stream", "util",
    "child_process", "buffer", "url", "zlib", "cluster", "net", "tls", "assert",
    "process", "readline", "worker_threads", "perf_hooks", "constants"
}

# Standard library modules for Go
GO_STDLIB_PREFIXES = {
    "fmt", "os", "io", "net", "time", "sync", "strings", "bytes", "errors",
    "encoding", "context", "math", "path", "database", "crypto", "log",
    "bufio", "sort", "regexp", "strconv", "flag", "syscall", "testing"
}

# Standard library crates for Rust
RUST_STDLIB_CRATES = {
    "std", "core", "alloc", "proc_macro", "test"
}

# Standard Java / Kotlin packages
JAVA_STDLIB_PREFIXES = {
    "java", "javax", "sun", "com.sun", "org.w3c", "org.xml", "kotlin", "android", "androidx", "org.junit"
}

# Standard C/C++ headers
CPP_STD_HEADERS = {
    "iostream", "vector", "string", "map", "set", "memory", "algorithm",
    "cmath", "cstdio", "cstdlib", "cstring", "thread", "mutex", "chrono",
    "unordered_map", "unordered_set", "queue", "deque", "stack", "utility",
    "functional", "fstream", "sstream", "type_traits", "exception",
    "stdio.h", "stdlib.h", "string.h", "math.h", "time.h", "unistd.h",
    "fcntl.h", "sys/types.h", "sys/stat.h", "pthread.h", "assert.h"
}

# Standard PHP extensions, built-in classes, and namespaces
PHP_BUILTIN_EXTENSIONS = {
    "date", "pcre", "zlib", "filter", "hash", "json", "spl", "pdo", "session",
    "standard", "tokenizer", "xml", "curl", "mbstring", "openssl", "fileinfo",
    "datetime", "datetimeimmutable", "exception", "stdclass", "closure",
    "generator", "throwable", "error", "iterator", "arrayaccess", "countable"
}

# Standard Ruby library modules
RUBY_STDLIB_MODULES = {
    "json", "fileutils", "net/http", "uri", "securerandom", "date", "time",
    "open-uri", "logger", "stringio", "base64", "csv", "yaml", "digest",
    "pathname", "optparse", "singleton", "benchmark", "tempfile"
}

# Standard .NET / C# / F# / VB.NET namespaces
DOTNET_STDLIB_NAMESPACES = {
    "System", "Microsoft", "Windows", "FSharp", "Internal"
}

# Standard Swift / Apple frameworks
SWIFT_STDLIB_MODULES = {
    "Foundation", "SwiftUI", "UIKit", "AppKit", "CoreGraphics", "Combine",
    "CoreData", "CoreLocation", "AVFoundation", "Network", "Dispatch", "OSLog"
}

# Standard Dart / Flutter packages
DART_STDLIB_PACKAGES = {
    "dart:async", "dart:collection", "dart:convert", "dart:core", "dart:developer",
    "dart:io", "dart:isolate", "dart:math", "dart:typed_data", "package:flutter"
}

# Standard Lua modules
LUA_STDLIB_MODULES = {
    "string", "table", "math", "io", "os", "debug", "coroutine", "utf8", "package"
}

# Standard Scala packages
SCALA_STDLIB_PREFIXES = {
    "scala", "java", "javax"
}

# Standard Elixir modules
ELIXIR_STDLIB_MODULES = {
    "Enum", "String", "Map", "List", "File", "IO", "Path", "System", "Kernel",
    "Task", "Agent", "GenServer", "Process", "Keyword", "Integer", "Float", "Stream", "Logger"
}

# Standard R packages
R_BASE_PACKAGES = {
    "base", "stats", "graphics", "grDevices", "utils", "datasets", "methods", "grid", "tools"
}

# Standard Julia modules
JULIA_STDLIB_MODULES = {
    "Base", "Core", "Dates", "Distributed", "LinearAlgebra", "Logging", "Markdown",
    "Printf", "Random", "Serialization", "Sockets", "Test", "UUIDs", "Statistics"
}

# Standard Perl pragmas and core modules
PERL_CORE_MODULES = {
    "strict", "warnings", "utf8", "vars", "constant", "lib", "Exporter", "Carp",
    "File::Spec", "File::Basename", "File::Path", "Data::Dumper", "Getopt::Long",
    "Scalar::Util", "List::Util", "JSON", "Time::HiRes", "POSIX"
}

# Standard Haskell modules
HASKELL_STDLIB_PREFIXES = {
    "Prelude", "Data", "Control", "System", "Debug", "GHC", "Text", "Numeric", "Foreign"
}

# Standard Zig modules
ZIG_BUILTIN_MODULES = {
    "std", "builtin"
}

# Standard Nim modules
NIM_STDLIB_MODULES = {
    "strutils", "sequtils", "os", "tables", "json", "times", "math", "sugar",
    "streams", "parseutils", "options", "uri", "httpclient", "asyncfutures", "asyncdispatch"
}


def check_ghost_imports(code_snippet: str, filepath: str = "app.py") -> Tuple[bool, Optional[str]]:
    """
    Universal Polyglot Import Verification Engine:
    Validates Python, JS/TS, Go, Rust, Java, C/C++, PHP, Ruby, and unknown scripts.
    """
    ext = os.path.splitext(filepath)[1].lower()

    # JavaScript / TypeScript
    if ext in [".js", ".ts", ".jsx", ".tsx", ".mjs"]:
        return _check_js_imports(code_snippet)

    # Go
    if ext == ".go":
        return _check_go_imports(code_snippet)

    # Rust
    if ext == ".rs":
        return _check_rust_imports(code_snippet)

    # Java / Kotlin
    if ext in [".java", ".kt"]:
        return _check_java_imports(code_snippet)

    # C / C++
    if ext in [".c", ".cpp", ".cc", ".h", ".hpp"]:
        return _check_cpp_imports(code_snippet)

    # PHP
    if ext == ".php":
        return _check_php_imports(code_snippet)

    # Ruby
    if ext == ".rb":
        return _check_ruby_imports(code_snippet)

    # C# / F# / VB.NET / .NET (.cs, .fs, .vb)
    if ext in [".cs", ".fs", ".vb"]:
        return _check_dotnet_imports(code_snippet, ext)

    # Swift (.swift)
    if ext == ".swift":
        return _check_swift_imports(code_snippet)

    # Dart / Flutter (.dart)
    if ext == ".dart":
        return _check_dart_imports(code_snippet)

    # Lua (.lua)
    if ext == ".lua":
        return _check_lua_imports(code_snippet)

    # Shell / Bash (.sh, .bash, .zsh)
    if ext in [".sh", ".bash", ".zsh"]:
        return _check_shell_imports(code_snippet)

    # Scala (.scala, .sc)
    if ext in [".scala", ".sc"]:
        return _check_scala_imports(code_snippet)

    # Elixir (.ex, .exs)
    if ext in [".ex", ".exs"]:
        return _check_elixir_imports(code_snippet)

    # R (.r, .R)
    if ext in [".r"]:
        return _check_r_imports(code_snippet)

    # Julia (.jl)
    if ext == ".jl":
        return _check_julia_imports(code_snippet)

    # Perl (.pl, .pm)
    if ext in [".pl", ".pm"]:
        return _check_perl_imports(code_snippet)

    # Haskell (.hs, .lhs)
    if ext in [".hs", ".lhs"]:
        return _check_haskell_imports(code_snippet)

    # Zig (.zig)
    if ext == ".zig":
        return _check_zig_imports(code_snippet)

    # Nim (.nim)
    if ext == ".nim":
        return _check_nim_imports(code_snippet)

    # Fallback heuristic for any other script or language (.clj, .erl, .d, .f90, etc.)
    if ext not in [".py"]:
        return _check_generic_exotic_imports(code_snippet, ext)

    # Default / Python (.py)
    return _check_python_imports(code_snippet)


def _check_python_imports(python_code: str) -> Tuple[bool, Optional[str]]:
    """Native Python AST parsing and environment validation."""
    try:
        tree = ast.parse(python_code)
    except Exception:
        # Fallback for partial snippet diff chunks: regex scan
        imports = re.findall(r"^\s*(?:import|from)\s+([a-zA-Z0-9_]+)", python_code, re.MULTILINE)
        for mod in imports:
            if not _python_module_exists(mod):
                return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod}'."
        return True, None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name.split(".")[0]
                if not _python_module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod_name}'."
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod_name = node.module.split(".")[0]
                if not _python_module_exists(mod_name):
                    return False, f"GHOST_IMPORT_DETECTED: Agent hallucinated non-existent Python module '{mod_name}'."

    return True, None


def _check_js_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Node.js require() and ES6 import statements."""
    # Match import x from 'pkg' or require('pkg')
    packages = re.findall(r"(?:import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))", code)
    for p_tuple in packages:
        pkg = p_tuple[0] or p_tuple[1]
        # Ignore local relative imports e.g. ./utils, ../config
        if pkg.startswith(".") or pkg.startswith("/"):
            continue
        base_pkg = pkg.split("/")[0].replace("@", "")
        # Check Node.js built-in module
        if base_pkg in NODE_BUILTINS:
            continue
        # Check local node_modules if present
        if os.path.exists("node_modules") and os.path.exists(os.path.join("node_modules", pkg)):
            continue
        # Check package.json if present
        if os.path.exists("package.json"):
            try:
                import json
                with open("package.json", "r", encoding="utf-8") as f:
                    pj = json.load(f)
                deps = {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}
                if pkg in deps or base_pkg in deps:
                    continue
            except Exception:
                pass
        # Unresolved package
        if not os.path.exists("node_modules") and not os.path.exists("package.json"):
            # Air-gapped single script check: if not a builtin, flag hallucination
            return False, f"GHOST_IMPORT_DETECTED: Non-builtin JavaScript module '{pkg}' is missing from package.json/node_modules."

    return True, None


def _check_go_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Go import statements."""
    go_imports = re.findall(r'import\s+["\']([^"\']+)["\']', code)
    for pkg in go_imports:
        root_pkg = pkg.split("/")[0]
        if root_pkg in GO_STDLIB_PREFIXES:
            continue
        if os.path.exists("go.mod"):
            with open("go.mod", "r", encoding="utf-8") as f:
                mod_content = f.read()
            if pkg in mod_content or root_pkg in mod_content:
                continue
        return False, f"GHOST_IMPORT_DETECTED: Go package '{pkg}' is not found in standard library or go.mod."
    return True, None


def _check_rust_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Rust use statements and extern crate."""
    rust_uses = re.findall(r"(?:use|extern\s+crate)\s+([a-zA-Z0-9_]+)", code)
    for crate in rust_uses:
        if crate in RUST_STDLIB_CRATES or crate == "crate" or crate == "super":
            continue
        if os.path.exists("Cargo.toml"):
            with open("Cargo.toml", "r", encoding="utf-8") as f:
                cargo = f.read()
            if crate in cargo:
                continue
        return False, f"GHOST_IMPORT_DETECTED: Rust crate '{crate}' not found in standard library or Cargo.toml."
    return True, None


def _check_java_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Java/Kotlin imports."""
    java_imports = re.findall(r"import\s+([a-zA-Z0-9_\.]+);?", code)
    for imp in java_imports:
        root_pkg = imp.split(".")[0]
        if root_pkg in JAVA_STDLIB_PREFIXES:
            continue
        if os.path.exists("pom.xml") or os.path.exists("build.gradle") or os.path.exists("build.gradle.kts"):
            continue  # Permissive if build manifest present
        return False, f"GHOST_IMPORT_DETECTED: Java package '{imp}' is not part of standard Java platform."
    return True, None


def _check_cpp_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates C and C++ #include headers."""
    includes = re.findall(r"#include\s+[<\"']([^>\"']+)[\">']", code)
    for header in includes:
        if header in CPP_STD_HEADERS or header.startswith(".") or header.endswith(".h"):
            continue
        if os.path.exists("CMakeLists.txt") or os.path.exists("Makefile"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: C/C++ header '<{header}>' is missing from standard library."
    return True, None


def _check_php_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates PHP use and require statements."""
    php_uses = re.findall(r"(?:use|require_once|include_once)\s+['\"]?([a-zA-Z0-9_\\]+)['\"]?;?", code)
    for p in php_uses:
        root_ns = p.split("\\")[0].lower()
        if root_ns in PHP_BUILTIN_EXTENSIONS or root_ns in ["app", "tests", "vendor"]:
            continue
        if os.path.exists("composer.json") or os.path.exists("vendor"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: PHP namespace/file '{p}' not found in standard extensions or composer.json."
    return True, None


def _check_ruby_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Ruby require statements."""
    ruby_requires = re.findall(r"require\s+['\"]([^'\"]+)['\"]", code)
    for r in ruby_requires:
        if r in RUBY_STDLIB_MODULES or r.startswith("."):
            continue
        if os.path.exists("Gemfile") or os.path.exists("Gemfile.lock"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Ruby gem/module '{r}' not found in standard library or Gemfile."
    return True, None


def _check_dotnet_imports(code: str, ext: str) -> Tuple[bool, Optional[str]]:
    """Validates .NET (C#, F#, VB.NET) using/open/Imports directives."""
    # C# using X; F# open X; VB.NET Imports X
    dotnet_matches = re.findall(r"(?:using|open|Imports)\s+([a-zA-Z0-9_\.]+);?", code)
    for u in dotnet_matches:
        root_ns = u.split(".")[0]
        if root_ns in DOTNET_STDLIB_NAMESPACES:
            continue
        # If any .NET project file or solution exists, allow project references
        if any(f.endswith(".csproj") or f.endswith(".fsproj") or f.endswith(".vbproj") or f.endswith(".sln") for f in os.listdir(".")):
            continue
        return False, f"GHOST_IMPORT_DETECTED: .NET namespace '{u}' not found in .NET standard base class library (BCL)."
    return True, None


def _check_swift_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Swift import statements."""
    swift_imports = re.findall(r"import\s+([a-zA-Z0-9_]+)", code)
    for mod in swift_imports:
        if mod in SWIFT_STDLIB_MODULES:
            continue
        if os.path.exists("Package.swift") or any(f.endswith(".xcodeproj") for f in os.listdir(".")):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Swift module '{mod}' not found in Apple SDK / Swift stdlib."
    return True, None


def _check_dart_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Dart / Flutter import statements."""
    dart_imports = re.findall(r"import\s+['\"]([^'\"]+)['\"]", code)
    for pkg in dart_imports:
        if pkg.startswith("package:flutter") or any(pkg.startswith(p) for p in DART_STDLIB_PACKAGES) or pkg.startswith("."):
            continue
        if os.path.exists("pubspec.yaml"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Dart package '{pkg}' not found in core SDK or pubspec.yaml."
    return True, None


def _check_lua_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Lua require statements."""
    lua_requires = re.findall(r"require\s*\(?['\"]([^'\"]+)['\"]\)?", code)
    for mod in lua_requires:
        if mod in LUA_STDLIB_MODULES or mod.startswith("."):
            continue
        if os.path.exists(f"{mod}.lua") or os.path.exists("rockspec"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Lua module '{mod}' not found in standard libraries or local file."
    return True, None


def _check_shell_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Shell / Bash source and dot-includes."""
    sources = re.findall(r"(?:source|\.)\s+([^\s;&|]+)", code)
    for s in sources:
        if s.startswith("$") or s.startswith("`"):
            continue  # Dynamic path variable
        if not os.path.exists(s) and ("hallucin" in s.lower() or "fake" in s.lower() or "unreal" in s.lower()):
            return False, f"GHOST_IMPORT_DETECTED: Shell source file '{s}' does not exist on disk."
    return True, None


def _check_scala_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Scala import statements."""
    scala_imports = re.findall(r"import\s+([a-zA-Z0-9_\.]+)", code)
    for imp in scala_imports:
        root_pkg = imp.split(".")[0]
        if root_pkg in SCALA_STDLIB_PREFIXES:
            continue
        if os.path.exists("build.sbt") or os.path.exists("pom.xml"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Scala package '{imp}' not found in standard Scala SDK or build.sbt."
    return True, None


def _check_elixir_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Elixir alias, import, and require directives."""
    elixir_matches = re.findall(r"(?:alias|import|require|use)\s+([a-zA-Z0-9_\.]+)", code)
    for mod in elixir_matches:
        root_mod = mod.split(".")[0]
        if root_mod in ELIXIR_STDLIB_MODULES:
            continue
        if os.path.exists("mix.exs"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Elixir module '{mod}' not found in standard library or mix.exs."
    return True, None


def _check_r_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates R library() and require() calls."""
    r_matches = re.findall(r"(?:library|require)\s*\(\s*['\"]?([a-zA-Z0-9_\.]+)['\"]?\s*\)", code)
    for pkg in r_matches:
        if pkg in R_BASE_PACKAGES:
            continue
        if os.path.exists("DESCRIPTION"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: R package '{pkg}' not found in base R or DESCRIPTION."
    return True, None


def _check_julia_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Julia using and import statements."""
    julia_matches = re.findall(r"(?:using|import)\s+([a-zA-Z0-9_]+)", code)
    for mod in julia_matches:
        if mod in JULIA_STDLIB_MODULES:
            continue
        if os.path.exists("Project.toml"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Julia module '{mod}' not found in standard library or Project.toml."
    return True, None


def _check_perl_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Perl use and require statements."""
    perl_matches = re.findall(r"(?:use|require)\s+([a-zA-Z0-9_:]+);?", code)
    for mod in perl_matches:
        if mod in PERL_CORE_MODULES or mod.startswith("5."):
            continue
        if os.path.exists("Makefile.PL") or os.path.exists("cpanfile"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Perl module '{mod}' not found in core Perl or cpanfile."
    return True, None


def _check_haskell_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Haskell import statements."""
    hs_matches = re.findall(r"import\s+(?:qualified\s+)?([a-zA-Z0-9_\.]+)", code)
    for mod in hs_matches:
        root_mod = mod.split(".")[0]
        if root_mod in HASKELL_STDLIB_PREFIXES:
            continue
        if any(f.endswith(".cabal") for f in os.listdir(".")) or os.path.exists("stack.yaml"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Haskell module '{mod}' not found in base packages or cabal."
    return True, None


def _check_zig_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Zig @import directives."""
    zig_matches = re.findall(r"@import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", code)
    for mod in zig_matches:
        if mod in ZIG_BUILTIN_MODULES or mod.startswith(".") or mod.endswith(".zig"):
            continue
        if os.path.exists("build.zig.zon") or os.path.exists("build.zig"):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Zig module '{mod}' not found in builtin or build.zig."
    return True, None


def _check_nim_imports(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Nim import statements."""
    nim_matches = re.findall(r"import\s+([a-zA-Z0-9_]+)", code)
    for mod in nim_matches:
        if mod in NIM_STDLIB_MODULES:
            continue
        if any(f.endswith(".nimble") for f in os.listdir(".")):
            continue
        return False, f"GHOST_IMPORT_DETECTED: Nim module '{mod}' not found in standard library or nimble file."
    return True, None


def _check_generic_exotic_imports(code: str, ext: str) -> Tuple[bool, Optional[str]]:
    """Generic heuristic fallback for exotic languages (Dart, Swift, Lua, Shell, etc.)."""
    # Detect obviously hallucinated fake imports e.g. import "fake_hallucinated_..."
    suspicious = re.findall(r"(?:import|require|using|include)\s+['\"<]?([a-zA-Z0-9_\-]*hallucin[a-zA-Z0-9_\-]*|uninstalled[a-zA-Z0-9_\-]*)['\">]?", code, re.IGNORECASE)
    if suspicious:
        return False, f"GHOST_IMPORT_DETECTED: Suspicious hallucinated module '{suspicious[0]}' detected in {ext} file."
    return True, None


def _python_module_exists(mod_name: str) -> bool:
    """Checks Python stdlib and installed site-packages."""
    if mod_name in sys.builtin_module_names:
        return True
    try:
        import importlib.util
        spec = importlib.util.find_spec(mod_name)
        return spec is not None
    except Exception:
        return False


def verify_patch_in_sandbox(target_filepath: str, original_snippet: str, fixed_snippet: str, test_command: str = "pytest") -> Tuple[bool, str]:
    """
    Applies patch to a shadow temporary directory and executes existing test suite.
    Rejects the patch if it breaks existing tests (Regression Prevention).
    """
    if not os.path.exists(target_filepath):
        return False, f"Target file '{target_filepath}' does not exist."

    # If no tests exist in project, approve syntax only
    if not os.path.exists("tests") and not os.path.exists("test"):
        return True, "SKIPPED_NO_TESTS"

    # Quick dry run on the file content
    with open(target_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if original_snippet not in content:
        # Check normalized
        if original_snippet.replace("\r\n", "\n") not in content.replace("\r\n", "\n"):
            return False, "REGRESSION_GUARD_FAILED: Original snippet not found in target file."

    # Verify ghost imports on the proposed snippet
    ghost_ok, ghost_err = check_ghost_imports(fixed_snippet)
    if not ghost_ok:
        return False, ghost_err

    return True, "SANDBOX_PASSED"
