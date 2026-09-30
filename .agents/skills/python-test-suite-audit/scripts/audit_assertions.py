"""Scan Python test source for advisory audit patterns without executing project code."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from typing import Any

MAX_FILES = 500
MAX_CONTENT_CHARS = 500_000
MAX_FINDINGS = 1_000

_ALLOWED_TOP_LEVEL_FIELDS = frozenset({"files", "max_findings"})
_ALLOWED_FILE_FIELDS = frozenset({"path", "content"})


class InputError(ValueError):
    """Raised when the scanner receives malformed input."""


def _validate_files(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    unknown = sorted(set(payload) - _ALLOWED_TOP_LEVEL_FIELDS)
    if unknown:
        raise InputError(f"unknown top-level field: {unknown[0]!r}")
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise InputError("files must be a non-empty list")
    if len(files) > MAX_FILES:
        raise InputError(f"files must contain at most {MAX_FILES} entries")
    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(files):
        location = f"files[{index}]"
        if not isinstance(entry, dict):
            raise InputError(f"{location} must be an object")
        unknown_entry = sorted(set(entry) - _ALLOWED_FILE_FIELDS)
        if unknown_entry:
            raise InputError(f"{location} has unknown field: {unknown_entry[0]!r}")
        path = entry.get("path")
        content = entry.get("content")
        if not isinstance(path, str) or not path.strip():
            raise InputError(f"{location}.path must be a non-empty string")
        if not isinstance(content, str):
            raise InputError(f"{location}.content must be a string")
        if len(content) > MAX_CONTENT_CHARS:
            raise InputError(f"{location}.content exceeds the character budget")
        validated.append({"path": path, "content": content})
    return validated


def _validate_max_findings(payload: dict[str, Any]) -> int:
    if "max_findings" not in payload:
        raise InputError("max_findings is required")
    max_findings = payload["max_findings"]
    if isinstance(max_findings, bool) or not isinstance(max_findings, int) or max_findings <= 0:
        raise InputError("max_findings must be a positive integer")
    if max_findings > MAX_FINDINGS:
        raise InputError(f"max_findings must not exceed {MAX_FINDINGS}")
    return max_findings


def _test_functions(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Return only test functions pytest would collect.

    Module-level ``test_*`` functions and methods directly under a top-level
    class (e.g. ``Test*`` groupings) are collected. Nested functions are never
    collected by pytest, so they are excluded here.
    """
    collected: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                collected.append(node)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name.startswith("test"):
                        collected.append(child)
    return collected


def _owned_nodes(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    """Return descendant nodes owned by a test, excluding nested scopes.

    Bodies of nested ``def``/``async def``/``class``/``lambda`` helpers belong
    to a different scope and are never executed as part of the outer test body
    itself, so their asserts and calls must not satisfy the outer test.
    """
    owned: list[ast.AST] = []
    stack = list(ast.iter_child_nodes(func))
    while stack:
        node = stack.pop()
        owned.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return owned


_MOCK_FACTORY_ATTRS = frozenset({"Mock", "MagicMock", "AsyncMock", "mock_open", "patch"})


def _function_configures_mock(nodes: list[ast.AST]) -> bool:
    """Check whether the test itself configures a mock object.

    Requires a ``return_value``/``side_effect`` keyword on a call to a known
    mock factory (``Mock``/``MagicMock``/``patch``/``mocker.patch``/...), so an
    unrelated ``return_value`` keyword on a non-mock call is not flagged.
    """
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        if not any(kw.arg in {"return_value", "side_effect"} for kw in node.keywords):
            continue
        called = node.func
        if isinstance(called, ast.Name) and called.id in _MOCK_FACTORY_ATTRS:
            return True
        if isinstance(called, ast.Attribute) and called.attr in _MOCK_FACTORY_ATTRS:
            return True
    return False


def _type_contains_broad_exception(node: ast.AST) -> bool:
    """Recursively check for a broad base exception, including tuple forms."""
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Attribute):
        return node.attr in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(_type_contains_broad_exception(elt) for elt in node.elts)
    return False


def _scan_function(func: ast.FunctionDef | ast.AsyncFunctionDef, path: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    owned = _owned_nodes(func)
    asserts = [n for n in owned if isinstance(n, ast.Assert)]
    calls = [n for n in owned if isinstance(n, ast.Call)]

    def evidence(node: ast.AST) -> str:
        try:
            text = ast.unparse(node)
        except (ValueError, SyntaxError):
            text = type(node).__name__
        return text[:200]

    has_unittest_assert = any(
        isinstance(call.func, ast.Attribute) and call.func.attr.startswith(("assert", "fail"))
        for call in calls
    )
    has_raises = any(
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "raises"
        or isinstance(call.func, ast.Name)
        and call.func.id == "assertRaises"
        for call in calls
    )

    if not asserts and not has_unittest_assert and not has_raises:
        findings.append(
            {
                "dimension": "assertion rigor",
                "location": f"{path}:{func.lineno}",
                "evidence": f"def {func.name} has no assert statement",
                "pattern": "no-assertion",
            }
        )

    for node in asserts:
        test = node.test
        if isinstance(test, ast.Constant) and test.value in (True, False):
            findings.append(
                {
                    "dimension": "assertion rigor",
                    "location": f"{path}:{node.lineno}",
                    "evidence": evidence(node),
                    "pattern": "constant-assert",
                }
            )
        elif isinstance(test, ast.Name):
            findings.append(
                {
                    "dimension": "assertion rigor",
                    "location": f"{path}:{node.lineno}",
                    "evidence": evidence(node),
                    "pattern": "weak-truthy-assert",
                }
            )
        elif (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Call)
            and isinstance(test.left.func, ast.Name)
            and test.left.func.id == "len"
        ):
            findings.append(
                {
                    "dimension": "assertion rigor",
                    "location": f"{path}:{node.lineno}",
                    "evidence": evidence(node),
                    "pattern": "weak-length-assert",
                }
            )

    for call in calls:
        is_raises = (
            isinstance(call.func, ast.Attribute) and call.func.attr in {"raises", "assertRaises"}
        ) or (isinstance(call.func, ast.Name) and call.func.id in {"raises", "assertRaises"})
        if is_raises:
            has_match = any(kw.arg == "match" for kw in call.keywords)
            if not has_match:
                findings.append(
                    {
                        "dimension": "error depth",
                        "location": f"{path}:{call.lineno}",
                        "evidence": evidence(call),
                        "pattern": "raises-without-match",
                    }
                )
        if isinstance(call.func, ast.Attribute) and call.func.attr in {
            "assert_called_once_with",
            "assert_called_with",
            "assert_has_calls",
            "assert_any_call",
        }:
            findings.append(
                {
                    "dimension": "behavioral coupling",
                    "location": f"{path}:{call.lineno}",
                    "evidence": evidence(call),
                    "pattern": "call-order-lock",
                }
            )

    local_names = set()
    for arg in (*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs):
        local_names.add(arg.arg)
    if func.args.vararg is not None:
        local_names.add(func.args.vararg.arg)
    if func.args.kwarg is not None:
        local_names.add(func.args.kwarg.arg)
    for node in owned:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            local_names.add(node.id)
        for alias in (
            getattr(node, "names", []) if isinstance(node, ast.Import | ast.ImportFrom) else []
        ):
            local_names.add(alias.asname or alias.name.split(".")[0])

    for node in owned:
        if isinstance(node, ast.ExceptHandler):
            if node.type is None or _type_contains_broad_exception(node.type):
                findings.append(
                    {
                        "dimension": "error depth",
                        "location": f"{path}:{node.lineno}",
                        "evidence": "broad except handler",
                        "pattern": "broad-except",
                    }
                )
        if isinstance(node, ast.Attribute):
            if node.attr in {"call_count", "mock_calls", "called_once"}:
                findings.append(
                    {
                        "dimension": "behavioral coupling",
                        "location": f"{path}:{node.lineno}",
                        "evidence": evidence(node),
                        "pattern": "call-count-assert",
                    }
                )
            if node.attr.startswith("_") and not node.attr.startswith("__"):
                findings.append(
                    {
                        "dimension": "behavioral coupling",
                        "location": f"{path}:{node.lineno}",
                        "evidence": evidence(node),
                        "pattern": "private-access",
                    }
                )
            if node.attr == "environ" and isinstance(node.value, ast.Name):
                findings.append(
                    {
                        "dimension": "isolation",
                        "location": f"{path}:{node.lineno}",
                        "evidence": evidence(node),
                        "pattern": "global-environ-access",
                    }
                )
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id.startswith("_")
            and not node.id.startswith("__")
        ):
            if node.id not in {"_"} and node.id not in local_names:
                findings.append(
                    {
                        "dimension": "behavioral coupling",
                        "location": f"{path}:{node.lineno}",
                        "evidence": f"name {node.id}",
                        "pattern": "private-name-access",
                    }
                )

    if _function_configures_mock(owned) and asserts:
        findings.append(
            {
                "dimension": "assertion rigor",
                "location": f"{path}:{func.lineno}",
                "evidence": f"def {func.name} configures a mock return and asserts",
                "pattern": "mock-echo-suspect",
            }
        )
    return findings


def scan_test_files(payload: Any) -> dict[str, Any]:
    """Validate input and return bounded advisory findings."""
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    files = _validate_files(payload)
    max_findings = _validate_max_findings(payload)
    findings: list[dict[str, Any]] = []
    truncated = False
    counter = 0
    for entry in files:
        path = entry["path"]
        content = entry["content"]
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError) as error:
            counter += 1
            if len(findings) < max_findings:
                findings.append(
                    {
                        "finding_id": f"F{counter:03d}",
                        "severity": "advisory",
                        "dimension": "executability",
                        "location": f"{path}:1",
                        "evidence": f"unparseable test file: {error}",
                        "pattern": "unparseable-file",
                    }
                )
            else:
                truncated = True
            continue
        for func in _test_functions(tree):
            for item in _scan_function(func, path):
                counter += 1
                if len(findings) < max_findings:
                    findings.append(
                        {
                            "finding_id": f"F{counter:03d}",
                            "severity": "advisory",
                            **item,
                        }
                    )
                else:
                    truncated = True
    return {"findings": findings, "truncated": truncated}


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Scan test source from JSON on stdin for advisory audit patterns."
    )


def _reject_non_finite_json(_: str) -> None:
    raise InputError("JSON input must not contain NaN or Infinity")


def main() -> int:
    """Read stdin, emit stable JSON, and return a process status."""
    _parser().parse_args()
    try:
        import json as json_module

        payload = json_module.load(sys.stdin, parse_constant=_reject_non_finite_json)
        result = scan_test_files(payload)
        output = json_module.dumps(
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
