"""Scan Python source text for missing or imprecise type annotations without executing it."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from typing import Any

MAX_FILES = 500
MAX_CONTENT_CHARS = 500_000
MAX_FINDINGS = 1_000

_ALLOWED_TOP_LEVEL_FIELDS = frozenset({"files", "max_findings"})
_ALLOWED_FILE_FIELDS = frozenset({"path", "content"})

_BARE_IGNORE_PATTERN = r"#\s*type:\s*ignore(?!\s*\[)"


class InputError(ValueError):
    """Raised when the scanner receives malformed input."""


def _validate_payload(payload: Any) -> tuple[list[dict[str, str]], int]:
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    unknown = sorted(set(payload) - _ALLOWED_TOP_LEVEL_FIELDS)
    if unknown:
        raise InputError(f"unknown top-level field: {unknown[0]!r}")
    if "files" not in payload:
        raise InputError("files is required")
    if "max_findings" not in payload:
        raise InputError("max_findings is required")
    files = payload["files"]
    if not isinstance(files, list) or not files:
        raise InputError("files must be a non-empty list")
    if len(files) > MAX_FILES:
        raise InputError(f"files must contain at most {MAX_FILES} entries")
    max_findings = payload["max_findings"]
    if isinstance(max_findings, bool) or not isinstance(max_findings, int):
        raise InputError("max_findings must be an integer")
    if max_findings <= 0:
        raise InputError("max_findings must be a positive integer")
    if max_findings > MAX_FINDINGS:
        raise InputError(f"max_findings must not exceed {MAX_FINDINGS}")
    validated: list[dict[str, str]] = []
    for entry in files:
        if not isinstance(entry, dict):
            raise InputError("each file entry must be an object")
        unknown_fields = sorted(set(entry) - _ALLOWED_FILE_FIELDS)
        if unknown_fields:
            raise InputError(f"unknown file field: {unknown_fields[0]!r}")
        path = entry.get("path")
        content = entry.get("content")
        if not isinstance(path, str) or not path.strip():
            raise InputError("file path must be a non-empty string")
        if not isinstance(content, str):
            raise InputError("file content must be a string")
        if len(content) > MAX_CONTENT_CHARS:
            raise InputError(f"file content must not exceed {MAX_CONTENT_CHARS} characters")
        validated.append({"path": path, "content": content})
    return validated, max_findings


def _contains_any(annotation: ast.expr) -> bool:
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name) and node.id == "Any":
            return True
        if isinstance(node, ast.Attribute) and node.attr == "Any":
            return True
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and re.search(r"\bAny\b", node.value) is not None
        ):
            return True
    return False


def _is_staticmethod(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in func.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "staticmethod":
            return True
    return False


def _method_nodes(tree: ast.AST) -> set[int]:
    """Ids of functions defined directly in a class body (possible receivers)."""
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found.add(id(child))
    return found


def _is_receiver_arg(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    methods: set[int],
    positionals: tuple[ast.arg, ...],
    arg: ast.arg,
) -> bool:
    """True when arg is the conventional receiver of an instance/class method."""
    return (
        arg.arg in ("self", "cls")
        and id(func) in methods
        and not _is_staticmethod(func)
        and bool(positionals)
        and arg is positionals[0]
    )


def _scan_functions(path: str, tree: ast.AST, emit: Any, counts: dict[str, int]) -> None:
    """Check every function definition, including nested ones.

    Nested functions are visited with ast.walk because annotation coverage
    matters at every level: an unannotated closure is as unchecked as an
    unannotated top-level function.
    """
    methods = _method_nodes(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        counts["functions"] += 1
        positionals = (*node.args.posonlyargs, *node.args.args)
        parameters: list[tuple[ast.arg, str]] = [
            (arg, arg.arg)
            for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        ]
        if node.args.vararg is not None:
            parameters.append((node.args.vararg, f"*{node.args.vararg.arg}"))
        if node.args.kwarg is not None:
            parameters.append((node.args.kwarg, f"**{node.args.kwarg.arg}"))

        eligible = [
            (arg, display)
            for arg, display in parameters
            if not _is_receiver_arg(node, methods, positionals, arg)
        ]
        if node.type_comment is not None:
            counts["args_total"] += len(eligible)
            counts["args_annotated"] += len(eligible)
            counts["returns_total"] += 1
            counts["returns_annotated"] += 1
            if re.search(r"\bAny\b", node.type_comment) is not None:
                emit(
                    "any-annotation",
                    "annotation precision",
                    f"{path}:{node.lineno}",
                    f"def {node.name} type comment uses Any",
                )
            continue
        for arg, display in eligible:
            counts["args_total"] += 1
            if arg.annotation is None:
                emit(
                    "unannotated-arg",
                    "annotation coverage",
                    f"{path}:{node.lineno}",
                    f"def {node.name} has unannotated arg {display}",
                )
            else:
                counts["args_annotated"] += 1
                if _contains_any(arg.annotation):
                    emit(
                        "any-annotation",
                        "annotation precision",
                        f"{path}:{arg.lineno}",
                        f"def {node.name} annotates {display} as Any",
                    )
        counts["returns_total"] += 1
        if node.returns is None:
            emit(
                "missing-return",
                "annotation coverage",
                f"{path}:{node.lineno}",
                f"def {node.name} has no return annotation",
            )
        else:
            counts["returns_annotated"] += 1
            if _contains_any(node.returns):
                emit(
                    "any-annotation",
                    "annotation precision",
                    f"{path}:{node.returns.lineno}",
                    f"def {node.name} returns Any",
                )


def _scan_annassigns(path: str, tree: ast.AST, emit: Any) -> None:
    """Flag `Any` on annotated variable and attribute assignments."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and node.annotation is not None
            and _contains_any(node.annotation)
        ):
            emit(
                "any-annotation",
                "annotation precision",
                f"{path}:{node.lineno}",
                "annotated assignment uses Any",
            )


def _scan_casts(path: str, tree: ast.AST, emit: Any) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_cast = (isinstance(func, ast.Name) and func.id == "cast") or (
            isinstance(func, ast.Attribute) and func.attr == "cast"
        )
        if is_cast:
            emit(
                "cast-call",
                "annotation precision",
                f"{path}:{node.lineno}",
                "cast() call narrows without proof",
            )


def _scan_bare_ignores(path: str, content: str, emit: Any) -> None:
    for lineno, line in enumerate(content.splitlines(), start=1):
        if re.search(_BARE_IGNORE_PATTERN, line):
            emit(
                "bare-ignore",
                "suppression hygiene",
                f"{path}:{lineno}",
                line.strip()[:200],
            )


def scan_source_files(payload: Any) -> dict[str, Any]:
    """Validate the payload and scan each file for annotation findings."""
    files, max_findings = _validate_payload(payload)
    findings: list[dict[str, Any]] = []
    truncated = False
    counts = {
        "functions": 0,
        "args_annotated": 0,
        "args_total": 0,
        "returns_annotated": 0,
        "returns_total": 0,
    }

    def emit(pattern: str, dimension: str, location: str, evidence: str) -> None:
        nonlocal truncated
        if len(findings) >= max_findings:
            truncated = True
            return
        findings.append(
            {
                "finding_id": f"F{len(findings) + 1:03d}",
                "pattern": pattern,
                "dimension": dimension,
                "location": location,
                "evidence": evidence,
                "severity": "advisory",
            }
        )

    for entry in files:
        path = entry["path"]
        content = entry["content"]
        try:
            tree = ast.parse(content, type_comments=True)
        except (SyntaxError, ValueError) as error:
            emit("unparseable-file", "executability", f"{path}:1", str(error)[:200])
            continue
        _scan_functions(path, tree, emit, counts)
        _scan_annassigns(path, tree, emit)
        _scan_casts(path, tree, emit)
        _scan_bare_ignores(path, content, emit)
    return {
        "findings": findings,
        "truncated": truncated,
        "summary": {
            "files_scanned": len(files),
            "functions_scanned": counts["functions"],
            "args_annotated": counts["args_annotated"],
            "args_total": counts["args_total"],
            "returns_annotated": counts["returns_annotated"],
            "returns_total": counts["returns_total"],
        },
    }


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Scan Python source files for annotation findings from JSON on stdin."
    )


def _reject_non_finite_json(_: str) -> None:
    raise InputError("JSON input must not contain NaN or Infinity")


def main() -> int:
    """Read stdin, emit stable JSON, and return a process status."""
    _parser().parse_args()
    try:
        payload = json.load(sys.stdin, parse_constant=_reject_non_finite_json)
        result = scan_source_files(payload)
        output = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (
        InputError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
