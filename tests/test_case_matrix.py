import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / ".agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py"


def run_helper(payload):
    assert SCRIPT.is_file(), f"helper script is absent: {SCRIPT}"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )


def test_plan_case_matrix_is_deterministic_and_respects_limit():
    payload = {
        "dimensions": {
            "n": {"values": [0, 1, 10], "boundary": [0, 10]},
            "text": {"values": ["", "a"], "boundary": [""]},
        },
        "max_cases": 4,
    }
    first = run_helper(payload)
    second = run_helper(payload)

    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert len(result["cases"]) <= 4
    assert result["truncated"] is True


def test_plan_case_matrix_rejects_malformed_input():
    with pytest.raises(subprocess.CalledProcessError):
        run_helper({"dimensions": {"n": {"values": []}}, "max_cases": 0})


def test_plan_case_matrix_help():
    assert SCRIPT.is_file(), f"helper script is absent: {SCRIPT}"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "usage:" in result.stdout.lower()


def test_plan_case_matrix_preserves_explicit_boundaries():
    payload = {
        "dimensions": {
            "n": {"values": [3], "boundary": [0, 4]},
        },
        "max_cases": 3,
    }
    result = json.loads(run_helper(payload).stdout)

    assert result["cases"] == [
        {"n": 0},
        {"n": 4},
        {"n": 3},
    ]


def test_helper_has_no_execution_or_network_imports():
    source = SCRIPT.read_text()

    assert "import subprocess" not in source
    assert "import requests" not in source
    assert "from my_project" not in source
