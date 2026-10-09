import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).parents[1] / "src/python-property-based-testing/scripts/plan_property_matrix.py"
)


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


def base_payload():
    return {
        "target": "encode_text/decode_text",
        "properties": [
            {
                "id": "round-trip",
                "statement": "decode(encode(s)) == s",
                "domain": "valid unicode strings",
                "oracle": "exact equality",
            }
        ],
        "dimensions": {"text": {"values": ["", "a"], "boundary": [""]}},
        "max_cases": 1,
    }


def test_plan_property_matrix_is_deterministic_and_respects_limit():
    first = run_helper(base_payload())
    second = run_helper(base_payload())
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert len(result["cases"]) <= 4
    assert result["truncated"] is True
    assert result["target"] == "encode_text/decode_text"
    assert result["strategy"] == "boundary-priority-cartesian"
    assert result["strategy_sketches"][0]["property_id"] == "round-trip"


def test_plan_property_matrix_preserves_explicit_boundaries():
    payload = {
        "target": "wrap_lines",
        "properties": [
            {"id": "width", "statement": "len(line) <= w", "domain": "valid", "oracle": "bound"}
        ],
        "dimensions": {"n": {"values": [3], "boundary": [0, 4]}},
        "max_cases": 3,
    }
    result = json.loads(run_helper(payload).stdout)
    assert result["cases"] == [{"n": 0}, {"n": 4}, {"n": 3}]


def test_plan_property_matrix_seeded_sample_requires_both_fields():
    payload = dict(base_payload(), seed=11, sample_size=2)
    assert json.loads(run_helper(payload).stdout)["strategy"] == "seeded-sample"
    bad = dict(base_payload(), seed=11)
    try:
        run_helper(bad)
    except subprocess.CalledProcessError as error:
        assert error.returncode == 2
        assert error.stdout == ""
    else:
        raise AssertionError("expected CalledProcessError for seed without sample_size")


def test_plan_property_matrix_rejects_malformed_input():
    try:
        run_helper({"target": "", "properties": [], "dimensions": {}, "max_cases": 0})
    except subprocess.CalledProcessError as error:
        assert error.returncode == 2
    else:
        raise AssertionError("expected CalledProcessError for malformed input")


def test_plan_property_matrix_help():
    assert SCRIPT.is_file(), f"helper script is absent: {SCRIPT}"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()


def test_plan_property_matrix_rejects_non_finite_json():
    result = run_helper_text(
        '{"target": "t", "properties": [], "dimensions": {"n": {"values": [NaN]}}, "max_cases": 1}'
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("error:")


def test_helper_has_no_execution_or_network_imports():
    source = SCRIPT.read_text()
    assert "import subprocess" not in source
    assert "import requests" not in source
    assert "from my_project" not in source
