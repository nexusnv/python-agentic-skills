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


def _patterns_for(path, content, max_findings=10):
    payload = {"files": [{"path": path, "content": content}], "max_findings": max_findings}
    result = json.loads(run_helper(payload).stdout)
    return result


def test_scanner_ignores_non_session_commit_and_query():
    result = _patterns_for(
        "src/shop/service_layer/handlers.py",
        "def f(x):\n    x.commit()\n    y.query('q')\n    config.commit()\n",
    )
    assert result["findings"] == []


def test_scanner_flags_session_add_and_qualified_receivers():
    for snippet, expected_evidence in (
        ("def f(session):\n    session.add(x)\n", "session.add outside"),
        ("def f(session):\n    session.commit()\n", "session.commit outside"),
        ("def f(self):\n    self.session.commit()\n", "self.session.commit outside"),
        ("def f(db):\n    db.session.query('q')\n", "db.session.query outside"),
    ):
        result = _patterns_for("src/shop/service_layer/handlers.py", snippet)
        patterns = [finding["pattern"] for finding in result["findings"]]
        assert "session-outside-uow" in patterns, snippet
        assert any(expected_evidence in finding["evidence"] for finding in result["findings"]), (
            snippet
        )


def test_scanner_does_not_flag_session_inside_uow_or_adapters():
    for path in (
        "unit_of_work.py",
        "src/shop/unit_of_work.py",
        "src/shop/service_layer/unit_of_work.py",
        "adapters/repository.py",
        "src/shop/adapters/repository.py",
    ):
        result = _patterns_for(path, "def f(session):\n    session.commit()\n")
        assert result["findings"] == [], path


def test_scanner_flags_domain_relative_paths():
    for path in ("domain/model.py", "src/domain.py", "src/shop/domain/model.py"):
        result = _patterns_for(path, "import sqlalchemy\n")
        patterns = [finding["pattern"] for finding in result["findings"]]
        assert "infra-import-in-domain" in patterns, path


def test_scanner_flags_bare_patch_mocker_and_multiline():
    cases = [
        "from unittest.mock import patch\npatch('my.Repository')\n",
        "patch('my.Repository')\n",
        "def test(mocker):\n    mocker.patch('my.UnitOfWork')\n",
        "mock.patch(\n    'my.MessageBus'\n)\n",
        "mock.patch('my.Notifications')\n",
        "mock.patch.object(MyRepository, 'get')\n",
        "mocker.patch.object('my.Repository', 'get')\n",
        "from unittest.mock import patch\npatch.object(MyUnitOfWork, 'commit')\n",
    ]
    for content in cases:
        result = _patterns_for("tests/test_x.py", content)
        patterns = [finding["pattern"] for finding in result["findings"]]
        assert "mock-of-owned-port" in patterns, content


def test_scanner_does_not_flag_dotted_patch():
    result = _patterns_for("tests/test_x.py", "json.patch('my.Repository')\n")
    assert result["findings"] == []


def test_scanner_flags_declarative_base_in_domain():
    result = _patterns_for(
        "src/shop/domain/model.py",
        "from sqlalchemy.orm import DeclarativeBase\nclass Foo(DeclarativeBase):\n    pass\n",
    )
    patterns = [finding["pattern"] for finding in result["findings"]]
    assert "orm-base-in-domain" in patterns


def test_scanner_severity_stays_advisory_for_report_minor_mapping():
    result = _patterns_for("src/shop/domain/model.py", "import sqlalchemy\n")
    assert result["findings"]
    assert all(finding["severity"] == "advisory" for finding in result["findings"])
