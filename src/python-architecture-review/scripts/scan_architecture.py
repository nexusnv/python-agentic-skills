"""Scan Python source text for Cosmic Python layer violations without executing it."""

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

_INFRA_MODULES = frozenset(
    {
        "sqlalchemy",
        "django",
        "flask",
        "fastapi",
        "requests",
        "redis",
        "smtplib",
        "pika",
        "boto3",
        "celery",
    }
)

_SESSION_METHODS = frozenset({"commit", "query", "add"})

_ORM_BASES = frozenset({"Base", "Model", "DeclarativeBase"})

# Matches mock.patch(...), mocker.patch(...), and bare patch(...) (from
# unittest.mock import patch) whose argument names an owned port, including
# the .object(...) spelling. Bounded to 500 chars and [^)] so multiline
# calls are found without catastrophic backtracking. Bare patch uses a
# lookbehind so dotted calls such as json.patch(...) are not flagged.
_MOCK_OF_OWNED_PORT_RE = re.compile(
    r"(?:mock\.patch|mocker\.patch|(?<![\w.])patch)(?:\.object)?"
    r"\s*\(\s*[^)]{0,500}?(?:Repository|UnitOfWork|MessageBus|Notifications)"
)


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


def _imported_roots(tree: ast.AST) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((alias.name.split(".", maxsplit=1)[0], node.lineno))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append((node.module.split(".", maxsplit=1)[0], node.lineno))
    return found


def _normalized_parts(path: str) -> list[str]:
    return [part for part in path.replace("\\", "/").split("/") if part not in ("", ".")]


def _filename(path: str) -> str:
    parts = _normalized_parts(path)
    return parts[-1] if parts else ""


def _stem(filename: str) -> str:
    return filename.rsplit(".", 1)[0] if "." in filename else filename


def _is_domain_path(path: str) -> bool:
    parts = _normalized_parts(path)
    if "domain" in parts:
        return True
    return _stem(_filename(path)) == "domain"


def _is_uow_or_adapter_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if "unit_of_work" in normalized:
        return True
    parts = _normalized_parts(path)
    if "adapters" in parts:
        return True
    return _stem(_filename(path)) == "adapters"


def _render_receiver(value: ast.AST) -> str:
    unparse = getattr(ast, "unparse", None)
    if callable(unparse):
        try:
            return unparse(value)
        except Exception:
            pass
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return f"{_render_receiver(value.value)}.{value.attr}"
    return "session"


def _session_receiver_label(node: ast.Attribute) -> str | None:
    """Return the session receiver label, or None when not a session access."""
    value = node.value
    if isinstance(value, ast.Name):
        if value.id == "session":
            return "session"
        return None
    if isinstance(value, ast.Attribute):
        if value.attr == "session":
            return _render_receiver(value)
        return None
    return None


def scan_source_files(payload: Any) -> dict[str, Any]:
    """Validate the payload and scan each file for advisory layer findings.

    Every finding uses severity "advisory". When transferring scanner output
    into the proposal report, grade each unconfirmed finding as report
    severity Minor with confirmed set to no; promote only after confirming
    by reading code or an independent review.
    """
    files, max_findings = _validate_payload(payload)
    findings: list[dict[str, Any]] = []
    truncated = False
    scanned = 0

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
        if truncated:
            break
        scanned += 1
        path = entry["path"]
        content = entry["content"]
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError) as error:
            emit("unparseable-file", "executability", f"{path}:1", str(error)[:200])
            continue
        for root, lineno in sorted(_imported_roots(tree), key=lambda item: item[1]):
            if truncated:
                break
            if _is_domain_path(path) and root in _INFRA_MODULES:
                emit(
                    "infra-import-in-domain",
                    "layer boundary",
                    f"{path}:{lineno}",
                    f"import {root} inside domain path",
                )
        if truncated:
            break
        for node in ast.walk(tree):
            if truncated:
                break
            if isinstance(node, ast.Attribute) and node.attr in _SESSION_METHODS:
                receiver = _session_receiver_label(node)
                if receiver is not None and not _is_uow_or_adapter_path(path):
                    emit(
                        "session-outside-uow",
                        "transaction ownership",
                        f"{path}:{node.lineno}",
                        f"{receiver}.{node.attr} outside unit_of_work/adapters",
                    )
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = ""
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    if base_name in _ORM_BASES and _is_domain_path(path):
                        emit(
                            "orm-base-in-domain",
                            "persistence ignorance",
                            f"{path}:{node.lineno}",
                            f"class {node.name} extends {base_name} inside domain",
                        )
        if truncated:
            break
        for match in _MOCK_OF_OWNED_PORT_RE.finditer(content):
            if truncated:
                break
            lineno = content.count("\n", 0, match.start()) + 1
            snippet = " ".join(match.group(0).split())[:200]
            emit(
                "mock-of-owned-port",
                "test isolation",
                f"{path}:{lineno}",
                snippet,
            )
    return {
        "findings": findings,
        "truncated": truncated,
        "summary": {"files_scanned": scanned},
    }


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Scan Python source files for architecture layer findings from JSON on stdin."
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
