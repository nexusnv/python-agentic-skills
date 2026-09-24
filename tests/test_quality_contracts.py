from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
HELPER = SKILLS_ROOT / "python-parameterized-testing" / "scripts" / "plan_case_matrix.py"
REQUIRED_HEADINGS = {
    "## Non-negotiable rules",
    "## Workflow",
    "## Failure handling",
    "## Output contract",
    "## References",
}
REQUIRED_FIXTURE_KEYS = {"id", "prompt", "kind", "expected"}
REQUIRED_FIXTURE_KINDS = {"positive", "near-miss", "safety", "evidence"}


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def load_cases(skill: Path) -> list[dict[str, Any]]:
    cases_path = skill.parent / "evals" / "cases.yaml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    assert isinstance(cases, list), f"{cases_path} must contain a top-level list"
    return cases


def semantic_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = [semantic_text(key) for key in value]
        parts.extend(semantic_text(item) for item in value.values())
    elif isinstance(value, list):
        parts = [semantic_text(item) for item in value]
    else:
        parts = [str(value)]
    return re.sub(r"[^a-z0-9]+", " ", " ".join(parts).casefold()).strip()


def contains_any(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def has_boolean_expectation(
    expected: Any,
    subject_patterns: tuple[str, ...],
    wanted: bool,
) -> bool:
    if not isinstance(expected, dict):
        return False
    for key, value in expected.items():
        if isinstance(value, dict):
            if has_boolean_expectation(value, subject_patterns, wanted):
                return True
        elif isinstance(value, list):
            if any(has_boolean_expectation(item, subject_patterns, wanted) for item in value):
                return True
        elif value is wanted and contains_any(semantic_text(key), *subject_patterns):
            return True
    return False


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_has_required_quality_headings(skill):
    headings = set(re.findall(r"^## .+$", skill.read_text(encoding="utf-8"), re.MULTILINE))

    assert REQUIRED_HEADINGS <= headings


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_has_concise_safety_and_output_language(skill):
    text = semantic_text(skill.read_text(encoding="utf-8"))
    contracts = {
        "synthetic data": (r"synthetic data",),
        "explicit approval": (
            r"(?:explicit|separate|narrow(?:ly)?).{0,80}approval",
            r"approval.{0,80}(?:explicit|separate|narrow(?:ly)?|before)",
        ),
        "redaction": (r"redact",),
        "not-run work": (r"not run", r"not-run"),
        "coverage gaps": (r"coverage gaps?", r"coverage gaps"),
        "exact command": (r"exact.{0,80}command", r"command.{0,80}exact"),
        "exact exit status": (r"exit status(?:es)?",),
        "no automatic product-code fix": (
            r"(?:do not|never).{0,80}(?:modify|change|repair|fix).{0,40}product code",
        ),
        "public boundary or domain": (r"public boundary", r"input domain", r"target contract"),
        "report location": (r"test reports", r"report convention"),
    }

    for concept, patterns in contracts.items():
        assert contains_any(text, *patterns), f"{skill} lacks {concept} language"


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_eval_fixture_shape(skill):
    for index, fixture in enumerate(load_cases(skill)):
        context = f"{skill.parent.name} fixture {index}"
        assert isinstance(fixture, dict), f"{context} must be a mapping"
        assert set(fixture) == REQUIRED_FIXTURE_KEYS, f"{context} has the wrong top-level keys"
        assert all(fixture[key] for key in REQUIRED_FIXTURE_KEYS), f"{context} has a blank field"
        assert fixture["kind"] in REQUIRED_FIXTURE_KINDS, f"{context} has an unknown kind"

        expected = fixture["expected"]
        assert isinstance(expected, dict), f"{context} expected must be a mapping"
        assert expected.get("properties_invariants"), f"{context} lacks properties/invariants"
        coverage = expected.get("coverage_areas_plan")
        assert isinstance(coverage, list) and coverage, f"{context} lacks a coverage plan"


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_eval_fixture_kinds_cover_positive_near_miss_safety_and_evidence(skill):
    kinds = {fixture["kind"] for fixture in load_cases(skill)}

    assert REQUIRED_FIXTURE_KINDS <= kinds


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_safety_fixtures_encode_appropriate_gates(skill):
    for fixture in load_cases(skill):
        if fixture["kind"] != "safety":
            continue

        expected = fixture["expected"]
        context = semantic_text(fixture)
        assert isinstance(expected.get("requires_approval"), bool)
        assert expected.get("synthetic_data_default") is True
        assert expected.get("must_not_modify_product_code") is True

        if contains_any(context, r"redact", r"secret", r"token", r"personal data", r"unbounded"):
            has_redaction = has_boolean_expectation(expected, (r"redact",), True)
            excludes_sensitive_output = has_boolean_expectation(
                expected,
                (r"secret", r"raw.{0,20}(?:output|response)", r"sensitive.{0,20}output"),
                False,
            )
            assert has_redaction or excludes_sensitive_output, (
                f"{fixture['id']} lacks a concrete redaction expectation"
            )

        if expected.get("approved_test_credential_used") is True:
            assert "credential_approval_status" in expected
            assert "credential_approval_scope" in expected


def test_parameterized_fixtures_cover_generation_contracts():
    expected_values = [
        fixture["expected"]
        for fixture in load_cases(SKILLS_ROOT / "python-parameterized-testing" / "SKILL.md")
    ]

    assert any(item.get("property_before_generation") is True for item in expected_values)
    assert any(item.get("generated_examples_not_proof") is True for item in expected_values)
    assert any(
        item.get("deterministic_seed") is True and item.get("replay_command_required") is True
        for item in expected_values
    )
    assert any(
        item.get("hypothesis_optional") is True
        and (
            item.get("fallback_disclosure_required") is True or bool(item.get("fallback_strategy"))
        )
        for item in expected_values
    )


def test_blackbox_fixtures_cover_boundary_oracle_and_characterization_contracts():
    expected_values = [
        fixture["expected"]
        for fixture in load_cases(SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md")
    ]

    assert any(item.get("public_boundary_required") is True for item in expected_values)
    assert any(item.get("oracle") for item in expected_values)
    assert any(item.get("characterization_not_correctness") is True for item in expected_values)


def test_blackbox_evidence_and_safety_fixture_contracts_are_complete():
    fixtures = load_cases(SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md")
    contract = semantic_text(
        [fixture for fixture in fixtures if fixture["kind"] in {"evidence", "safety"}]
    )
    required_language = {
        "canonical not-run encoding": r"canonical.{0,30}not.{0,10}run",
        "manual/non-gating encoding": r"manual.{0,20}non.{0,20}gating",
        "working directory": r"working.{0,20}director",
        "project-relative or redacted path": r"project.{0,20}relative.{0,30}redact",
        "redacted command structure": r"command.{0,80}(?:redact|structure.{0,20}preserv)",
        "run approval": r"run.{0,20}approval",
        "credential approval": r"credential.{0,20}approval",
        "properties or invariants": r"propert",
        "coverage": r"coverage",
    }

    for concept, pattern in required_language.items():
        assert re.search(pattern, contract), f"black-box fixtures lack {concept}"


def test_parameterized_evidence_fixture_contract_is_complete():
    fixtures = load_cases(SKILLS_ROOT / "python-parameterized-testing" / "SKILL.md")
    evidence = [fixture for fixture in fixtures if fixture["kind"] == "evidence"]
    assert evidence

    contract = semantic_text(evidence)
    required_language = {
        "properties": r"propert",
        "coverage": r"coverage",
        "valid/invalid/unsupported domains": r"valid.{0,30}invalid.{0,30}unsupported",
        "seed": r"seed",
        "replay": r"replay",
        "discarded count": r"discard.{0,30}count",
        "truncated count": r"truncat.{0,30}count",
        "limitations": r"limitation",
    }

    for concept, pattern in required_language.items():
        assert re.search(pattern, contract), f"parameterized evidence lacks {concept}"


def test_case_matrix_helper_uses_only_standard_library_imports():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])

    forbidden_roots = {"subprocess", "socket", "urllib", "requests", "os", "shutil", "pathlib"}
    assert not imported_roots & forbidden_roots
    non_standard_library = imported_roots - sys.stdlib_module_names - {"__future__"}
    assert not non_standard_library


def test_case_matrix_helper_cannot_execute_or_mutate_the_filesystem():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    forbidden_names = {"eval", "exec", "open"}
    forbidden_methods = {
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

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_names
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_methods
