from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
AUDIT_DIR = ROOT / ".agents" / "skills" / "python-test-suite-audit" / "scripts"
SCANNER = AUDIT_DIR / "audit_assertions.py"
PLANNER = AUDIT_DIR / "plan_audit_scope.py"

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


SCANNER_MOD = _load("audit_assertions", SCANNER)
PLANNER_MOD = _load("plan_audit_scope", PLANNER)


def _imported_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".", maxsplit=1)[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    return roots


@pytest.mark.parametrize("script", [SCANNER, PLANNER], ids=["scanner", "planner"])
def test_audit_scripts_exist(script):
    assert script.is_file()


@pytest.mark.parametrize("script", [SCANNER, PLANNER], ids=["scanner", "planner"])
def test_audit_scripts_use_only_allowlisted_imports(script):
    assert _imported_roots(script.read_text(encoding="utf-8")) <= ALLOWED_ROOTS


@pytest.mark.parametrize("script", [SCANNER, PLANNER], ids=["scanner", "planner"])
def test_audit_scripts_never_execute_targets(script):
    tree = ast.parse(script.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in FORBIDDEN_CALLS
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in FORBIDDEN_CALLS


def _scan(files, max_findings=50):
    return SCANNER_MOD.scan_test_files({"files": files, "max_findings": max_findings})


def _patterns(result):
    return [f["pattern"] for f in result["findings"]]


def test_scanner_flags_weak_truthy_assert():
    result = _scan([{"path": "t.py", "content": "def test_a():\n    assert result\n"}])
    assert "weak-truthy-assert" in _patterns(result)


def test_scanner_flags_constant_and_length_asserts():
    result = _scan(
        [
            {
                "path": "t.py",
                "content": "def test_a():\n    assert True\ndef test_b():\n    assert len(d) > 0\n",
            }
        ]
    )
    assert "constant-assert" in _patterns(result)
    assert "weak-length-assert" in _patterns(result)


def test_scanner_flags_no_assertion_test():
    result = _scan([{"path": "t.py", "content": "def test_a():\n    setup()\n"}])
    assert "no-assertion" in _patterns(result)


def test_scanner_ignores_local_underscore_variable():
    result = _scan(
        [{"path": "t.py", "content": "def test_x():\n    _result = 1\n    assert _result == 1\n"}]
    )
    assert "private-name-access" not in _patterns(result)


def test_scanner_flags_cross_boundary_private_name():
    result = _scan(
        [{"path": "t.py", "content": "import pkg\ndef test_x():\n    assert pkg._helper() == 1\n"}]
    )
    assert "private-access" in _patterns(result)


RAISES_WITHOUT_MATCH = (
    "import pytest\ndef test_e():\n    with pytest.raises(ValueError):\n        f()\n"
)
RAISES_WITH_MATCH = (
    'import pytest\ndef test_e():\n    with pytest.raises(ValueError, match="bad"):\n        f()\n'
)


def test_scanner_raises_requires_match():
    without = _scan([{"path": "t.py", "content": RAISES_WITHOUT_MATCH}])
    with_match = _scan([{"path": "t.py", "content": RAISES_WITH_MATCH}])
    assert "raises-without-match" in _patterns(without)
    assert "raises-without-match" not in _patterns(with_match)


def test_scanner_ignores_unrelated_raises_substring():
    result = _scan([{"path": "t.py", "content": "def test_x():\n    praises()\n"}])
    assert "raises-without-match" not in _patterns(result)


def test_scanner_flags_broad_except_and_call_order():
    result = _scan(
        [
            {
                "path": "t.py",
                "content": (
                    "def test_x(m):\n"
                    "    try:\n"
                    "        f()\n"
                    "    except Exception:\n"
                    "        pass\n"
                    "    m.assert_called_once_with(1)\n"
                    "    assert m.call_count == 1\n"
                ),
            }
        ]
    )
    patterns = _patterns(result)
    assert "broad-except" in patterns
    assert "call-order-lock" in patterns
    assert "call-count-assert" in patterns


def test_scanner_flags_mock_echo_suspect():
    result = _scan(
        [
            {
                "path": "t.py",
                "content": (
                    "from unittest.mock import Mock\n"
                    "def test_m():\n"
                    "    m = Mock(return_value=1)\n"
                    "    assert m() == 1\n"
                ),
            }
        ]
    )
    assert "mock-echo-suspect" in _patterns(result)


def test_scanner_marks_unparseable_file_without_crashing():
    result = _scan([{"path": "t.py", "content": "def (: bad"}])
    assert _patterns(result) == ["unparseable-file"]


def test_scanner_caps_findings_and_marks_truncation():
    files = [{"path": f"t{i}.py", "content": "def test_a():\n    assert x\n"} for i in range(5)]
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


@pytest.mark.parametrize("script", [SCANNER, PLANNER], ids=["scanner", "planner"])
@pytest.mark.parametrize("text", ["{bad", "NaN", "Infinity"])
def test_audit_scripts_reject_malformed_json(script, text):
    proc = _run_text(script, text)
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


def test_planner_sorted_priority_and_truncation():
    result = PLANNER_MOD.plan_audit_scope({"paths": ["b.py", "a.py"], "max_files": 5})
    assert result["files"] == ["a.py", "b.py"]
    assert result["truncated"] is False
    assert result["strategy"] == "sorted-priority"


def test_planner_seeded_sample_is_deterministic():
    payload = {"paths": ["a.py", "b.py", "c.py"], "max_files": 5, "seed": 7, "sample_size": 2}
    first = PLANNER_MOD.plan_audit_scope(payload)
    second = PLANNER_MOD.plan_audit_scope(payload)
    assert first == second
    assert first["strategy"] == "seeded-sample"
    assert len(first["files"]) == 2


def test_planner_requires_seed_and_sample_together():
    with pytest.raises(ValueError, match="together"):
        PLANNER_MOD.plan_audit_scope({"paths": ["a.py"], "max_files": 5, "seed": 1})
    with pytest.raises(ValueError, match="together"):
        PLANNER_MOD.plan_audit_scope({"paths": ["a.py"], "max_files": 5, "sample_size": 1})


def test_planner_rejects_unknown_fields_and_bad_budgets():
    proc = _run_text(PLANNER, json.dumps({"paths": ["a.py"], "max_files": 5, "nope": 1}))
    assert proc.returncode == 2
    with pytest.raises(ValueError, match="max_files"):
        PLANNER_MOD.plan_audit_scope({"paths": ["a.py"], "max_files": 0})
