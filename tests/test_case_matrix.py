import ast
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[1]
    / ".agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py"
)
SPEC = importlib.util.spec_from_file_location("plan_case_matrix", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HELPER
SPEC.loader.exec_module(HELPER)


def run_helper(payload):
    assert SCRIPT.is_file(), f"helper script is absent: {SCRIPT}"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )


def run_helper_text(input_text):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
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


def test_seeded_sample_is_deterministic_and_capped():
    payload = {
        "dimensions": {
            "n": {"values": [1, 2, 3], "boundary": [0, 10]},
            "text": {"values": ["a", "b"], "boundary": [""]},
        },
        "max_cases": 3,
        "seed": 8675309,
        "sample_size": 5,
    }

    first = run_helper(payload)
    second = run_helper(payload)
    result = json.loads(first.stdout)

    assert first.stdout == second.stdout
    assert result["strategy"] == "seeded-sample"
    assert result["seed"] == 8675309
    assert len(result["cases"]) == 3
    assert result["truncated"] is True
    assert all(case["n"] in {0, 1, 2, 3, 10} for case in result["cases"])
    assert all(case["text"] in {"", "a", "b"} for case in result["cases"])


def test_seeded_sample_repeats_seed_and_changes_with_different_seed():
    payload = {
        "dimensions": {"n": {"values": list(range(100))}},
        "max_cases": 10,
        "seed": 17,
        "sample_size": 10,
    }

    first = run_helper(payload)
    repeat = run_helper(payload)
    different = run_helper({**payload, "seed": 29})

    assert first.stdout == repeat.stdout
    assert json.loads(first.stdout)["cases"] != json.loads(different.stdout)["cases"]


def test_seeded_sample_is_untruncated_when_within_budget():
    result = json.loads(
        run_helper(
            {
                "dimensions": {"n": {"values": [1, 2, 3, 4]}},
                "max_cases": 4,
                "seed": 17,
                "sample_size": 4,
            }
        ).stdout
    )

    assert len(result["cases"]) == 4
    assert result["truncated"] is False


@pytest.mark.parametrize("missing", ["seed", "sample_size"])
def test_seeded_sample_requires_both_fields(missing):
    payload = {
        "dimensions": {"n": {"values": [1, 2]}},
        "max_cases": 2,
        "seed": 11,
        "sample_size": 2,
    }
    del payload[missing]

    with pytest.raises(subprocess.CalledProcessError) as error:
        run_helper(payload)

    assert error.value.returncode == 2
    assert error.value.stdout == ""


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_plan_case_matrix_rejects_non_finite_json(constant):
    input_text = '{"dimensions": {"n": {"values": [' + constant + ']}}, "max_cases": 1}'

    result = run_helper_text(input_text)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error:")
    assert len(result.stderr) < 200


def test_plan_case_matrix_rejects_malformed_max_cases_with_exact_error():
    result = run_helper_text('{"dimensions": {"n": {"values": [1]}}, "max_cases": 0}')

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error: max_cases must be a positive integer")
    assert len(result.stderr) < 200


@pytest.mark.parametrize("field", ["max_cases", "sample_size"])
def test_plan_case_matrix_rejects_hard_budget_ceilings(field):
    payload = {
        "dimensions": {"n": {"values": [1, 2, 3]}},
        "max_cases": 1,
    }
    if field == "sample_size":
        payload.update({"seed": 7, "sample_size": 10_001})
    else:
        payload["max_cases"] = 10_001

    with pytest.raises(subprocess.CalledProcessError) as error:
        run_helper(payload)

    assert error.value.returncode == 2
    assert error.value.stdout == ""


@pytest.mark.parametrize(
    "dimensions",
    [
        {1: {"values": [1]}},
        {1: {"values": [1]}, "n": {"values": [2]}},
    ],
)
def test_plan_case_matrix_requires_string_dimension_keys(dimensions):
    with pytest.raises(HELPER.InputError, match="dimension names must be strings"):
        HELPER.plan_case_matrix({"dimensions": dimensions, "max_cases": 1})


def test_plan_case_matrix_rejects_surrogate_through_api():
    with pytest.raises(HELPER.InputError, match="surrogate"):
        HELPER.plan_case_matrix({"dimensions": {"n": {"values": ["\ud800"]}}, "max_cases": 1})


def test_plan_case_matrix_rejects_surrogate_through_subprocess():
    input_text = json.dumps(
        {"dimensions": {"n": {"values": ["\ud800"]}}, "max_cases": 1},
        ensure_ascii=True,
    )

    result = run_helper_text(input_text)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error:")
    assert "surrogate" in result.stderr.lower()


def test_plan_case_matrix_rejects_invalid_boundary_type():
    with pytest.raises(subprocess.CalledProcessError):
        run_helper(
            {
                "dimensions": {"n": {"values": [1], "boundary": "invalid"}},
                "max_cases": 1,
            }
        )


def test_plan_case_matrix_marks_untruncated_matrix():
    result = json.loads(
        run_helper(
            {
                "dimensions": {"n": {"values": [2], "boundary": [0, 1]}},
                "max_cases": 3,
            }
        ).stdout
    )

    assert result["cases"] == [{"n": 0}, {"n": 1}, {"n": 2}]
    assert result["truncated"] is False


def test_plan_case_matrix_rejects_excessive_value_list():
    values = list(range(HELPER.MAX_VALUES_PER_DIMENSION + 1))

    with pytest.raises(subprocess.CalledProcessError) as error:
        run_helper({"dimensions": {"n": {"values": values}}, "max_cases": 1})

    assert error.value.returncode == 2
    assert error.value.stdout == ""


def test_plan_case_matrix_sorts_dimension_names():
    first = json.loads(
        run_helper(
            {
                "dimensions": {
                    "c": {"values": [2, 3]},
                    "b": {"values": [1, 2]},
                    "a": {"values": [0, 1]},
                },
                "max_cases": 8,
            }
        ).stdout
    )
    second = json.loads(
        run_helper(
            {
                "dimensions": {
                    "a": {"values": [0, 1]},
                    "b": {"values": [1, 2]},
                    "c": {"values": [2, 3]},
                },
                "max_cases": 8,
            }
        ).stdout
    )

    assert first == second
    assert first["cases"][:2] == [
        {"a": 0, "b": 1, "c": 2},
        {"a": 0, "b": 1, "c": 3},
    ]


def test_plan_case_matrix_rejects_non_json_value_through_api():
    with pytest.raises(HELPER.InputError, match="JSON-compatible"):
        HELPER.plan_case_matrix({"dimensions": {"n": {"values": [object()]}}, "max_cases": 1})


def test_helper_ast_has_no_execution_or_network_imports_and_no_writes():
    tree = ast.parse(SCRIPT.read_text())
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden_roots = {
        "subprocess",
        "socket",
        "urllib",
        "requests",
        "os",
        "shutil",
        "pathlib",
        "my_project",
    }
    assert not any(
        module == forbidden or module.startswith(f"{forbidden}.")
        for module in imported_modules
        for forbidden in forbidden_roots
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "write",
                    "write_text",
                    "write_bytes",
                    "unlink",
                    "mkdir",
                    "rmdir",
                    "rename",
                    "replace",
                    "touch",
                    "truncate",
                    "chmod",
                    "chown",
                    "symlink_to",
                    "hardlink_to",
                }


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
