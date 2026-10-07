from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
TYPES_DIR = ROOT / "src" / "python-type-safety" / "scripts"
SCANNER = TYPES_DIR / "scan_annotations.py"

ALLOWED_ROOTS = frozenset(
    {
        "__future__",
        "argparse",
        "ast",
        "collections",
        "itertools",
        "json",
        "math",
        "random",
        "re",
        "sys",
        "typing",
    }
)
FORBIDDEN_CALLS = frozenset(
    {
        "open",
        "exec",
        "eval",
        "compile",
        "system",
        "popen",
        "Popen",
        "run",
        "check_output",
        "check_call",
    }
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCANNER_MOD = _load("scan_annotations", SCANNER)


def _imported_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".", maxsplit=1)[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


def test_type_scanner_exists():
    assert SCANNER.is_file()


def test_type_scanner_uses_only_allowlisted_imports():
    assert _imported_roots(SCANNER.read_text(encoding="utf-8")) <= ALLOWED_ROOTS


def test_type_scanner_never_executes_targets():
    tree = ast.parse(SCANNER.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALLS
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALLS


def _scan(files, max_findings=50):
    return SCANNER_MOD.scan_source_files({"files": files, "max_findings": max_findings})


def _patterns(result):
    return [f["pattern"] for f in result["findings"]]


def test_scanner_flags_unannotated_args():
    result = _scan([{"path": "m.py", "content": "def f(a, b: int) -> int:\n    return 1\n"}])
    patterns = _patterns(result)
    assert "unannotated-arg" in patterns
    assert len([f for f in result["findings"] if f["pattern"] == "unannotated-arg"]) == 1


def test_scanner_skips_self_and_cls():
    result = _scan(
        [
            {
                "path": "m.py",
                "content": "class C:\n    def m(self, x: int) -> int:\n        return x\n",
            }
        ]
    )
    assert _patterns(result) == []


def test_scanner_flags_missing_return():
    result = _scan([{"path": "m.py", "content": "def f(a: int):\n    print(a)\n"}])
    assert "missing-return" in _patterns(result)


def test_scanner_flags_any_annotation():
    result = _scan(
        [
            {
                "path": "m.py",
                "content": "from typing import Any\ndef f(a: Any) -> int:\n    return 1\n",
            }
        ]
    )
    assert "any-annotation" in _patterns(result)


def test_scanner_flags_bare_ignore_but_not_coded_ignore():
    bare = _scan([{"path": "m.py", "content": "x = 1  # type: ignore\n"}])
    assert "bare-ignore" in _patterns(bare)
    coded = _scan([{"path": "m.py", "content": "x = 1  # type: ignore[assignment]\n"}])
    assert "bare-ignore" not in _patterns(coded)


def test_scanner_flags_cast_call():
    result = _scan(
        [
            {
                "path": "m.py",
                "content": "from typing import cast\ndef f(a: object) -> int:\n    return cast(int, a)\n",
            }
        ]
    )
    assert "cast-call" in _patterns(result)


def test_scanner_marks_unparseable_file_without_crashing():
    result = _scan([{"path": "m.py", "content": "def (: bad"}])
    assert _patterns(result) == ["unparseable-file"]


def test_scanner_caps_findings_and_marks_truncation():
    files = [{"path": f"m{i}.py", "content": "def f(a):\n    return a\n"} for i in range(5)]
    result = _scan(files, max_findings=3)
    assert len(result["findings"]) == 3
    assert result["truncated"] is True


def _run_text(script: Path, text: str):
    return subprocess.run(
        [sys.executable, str(script)],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("text", ["{bad", "NaN", "Infinity"])
def test_type_scanner_rejects_malformed_json(text):
    proc = _run_text(SCANNER, text)
    assert proc.returncode == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"files": [], "max_findings": 10},
        {"files": [{"path": "", "content": "x"}], "max_findings": 10},
        {"files": [{"path": "a.py", "content": "x"}]},
        {"files": [{"path": "a.py", "content": "x"}], "max_findings": True},
        {"files": [{"path": "a.py", "content": "x"}], "max_findings": 10, "nope": 1},
    ],
)
def test_scanner_rejects_malformed_payloads(payload):
    proc = _run_text(SCANNER, json.dumps(payload))
    assert proc.returncode == 2
