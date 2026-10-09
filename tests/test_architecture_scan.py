from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCANNER = ROOT / "src" / "python-architecture-review" / "scripts" / "scan_architecture.py"

ALLOWED_ROOTS = frozenset(
    {
        "__future__",
        "argparse",
        "ast",
        "collections",
        "json",
        "re",
        "sys",
        "typing",
    }
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_helper(payload):
    assert SCANNER.is_file(), f"helper script is absent: {SCANNER}"
    return subprocess.run(
        [sys.executable, str(SCANNER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )


def run_helper_text(input_text):
    return subprocess.run(
        [sys.executable, str(SCANNER)],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def test_scanner_exists():
    assert SCANNER.is_file()


def test_scanner_uses_only_allowlisted_imports():
    tree = ast.parse(SCANNER.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".", maxsplit=1)[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", maxsplit=1)[0])
    assert roots <= ALLOWED_ROOTS


def test_scanner_flags_infra_import_in_domain():
    payload = {
        "files": [
            {
                "path": "src/shop/domain/model.py",
                "content": "import sqlalchemy\nfrom sqlalchemy import Column\n",
            }
        ],
        "max_findings": 10,
    }
    result = json.loads(run_helper(payload).stdout)
    patterns = [finding["pattern"] for finding in result["findings"]]
    assert "infra-import-in-domain" in patterns
    assert result["summary"]["files_scanned"] == 1


def test_scanner_flags_session_outside_uow():
    payload = {
        "files": [
            {
                "path": "src/shop/service_layer/handlers.py",
                "content": "def handle(cmd, session):\n    session.commit()\n",
            }
        ],
        "max_findings": 10,
    }
    result = json.loads(run_helper(payload).stdout)
    patterns = [finding["pattern"] for finding in result["findings"]]
    assert "session-outside-uow" in patterns


def test_scanner_is_deterministic_and_respects_limit():
    payload = {
        "files": [
            {"path": "src/shop/domain/a.py", "content": "import sqlalchemy\n"},
            {"path": "src/shop/domain/b.py", "content": "import django.db\n"},
        ],
        "max_findings": 1,
    }
    first = run_helper(payload)
    second = run_helper(payload)
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert len(result["findings"]) <= 1
    assert result["truncated"] is True


def test_scanner_help():
    assert SCANNER.is_file(), f"helper script is absent: {SCANNER}"
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()


def test_scanner_rejects_malformed_input():
    try:
        run_helper({"files": [], "max_findings": 0})
    except subprocess.CalledProcessError as error:
        assert error.returncode == 2
    else:
        raise AssertionError("expected CalledProcessError for malformed input")


def test_scanner_rejects_non_finite_json():
    result = run_helper_text('{"files": [{"path": "a.py", "content": NaN}], "max_findings": 1}')
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error:")


def test_helper_has_no_execution_or_network_imports():
    source = SCANNER.read_text()
    assert "import subprocess" not in source
    assert "import requests" not in source
    assert "from my_project" not in source
