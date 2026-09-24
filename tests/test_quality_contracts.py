from __future__ import annotations

import ast
import re
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
REQUIRED_REPORT_FIELDS = {
    "python-blackbox-testing": frozenset(
        {
            "scenario_id",
            "execution_id",
            "working_directory_project_relative_or_redacted",
            "command_redacted_structure_preserved",
            "exit_status",
            "environment_mode",
            "isolation_scope_verification",
            "run_approval_status",
            "run_approval_scope",
            "credential_approval_status",
            "credential_approval_scope",
            "properties_invariants",
            "coverage_areas_plan",
            "runner",
            "environment_fingerprint",
            "not_run_status",
            "coverage_gaps",
        }
    ),
    "python-parameterized-testing": frozenset(
        {
            "properties_invariants",
            "coverage_areas_plan",
            "valid_invalid_unsupported_domains",
            "oracle_and_normalization",
            "fixed_example_count",
            "generated_witness_count",
            "discarded_count",
            "truncated_count",
            "seed",
            "runner",
            "environment",
            "exact_commands",
            "process_exit_statuses",
            "pass_fail_skip_expected_failure_and_not_run_results",
            "replay_command",
            "shrinking_status",
            "coverage_gaps",
            "limitations",
            "finite_samples_are_not_proof",
        }
    ),
}
ALLOWED_HELPER_IMPORTS = frozenset(
    {
        "__future__",
        "argparse",
        "collections",
        "itertools",
        "json",
        "math",
        "random",
        "sys",
        "typing",
    }
)
FORBIDDEN_HELPER_IMPORTS = frozenset(
    {
        "builtins",
        "ctypes",
        "importlib",
        "os",
        "pathlib",
        "requests",
        "runpy",
        "shutil",
        "socket",
        "subprocess",
        "urllib",
    }
)
FORBIDDEN_HELPER_NAMES = frozenset(
    {
        "CDLL",
        "__import__",
        "call",
        "check_call",
        "check_output",
        "exec",
        "eval",
        "import_module",
        "open",
        "popen",
        "Popen",
        "remove",
        "removedirs",
        "rmdir",
        "rmtree",
        "run",
        "run_path",
        "system",
        "unlink",
        "write_bytes",
        "write_text",
    }
)
RISKY_SAFETY_PROMPT_PATTERNS = (
    r"\blive\b",
    r"\bexternal\b",
    r"\bproduction\b",
    r"\b(?:destructive|delete|recursively delete)\b",
    r"\bcredential\b",
    r"\breal\s+(?:bearer\s+)?(?:token|secret|credential)\b",
    r"\b(?:paid|cost[- ]incurring|incur(?:s|red|ring)?|monetary budget)\b",
    r"\b(?:unisolated|privileged|host[- ]mounted|host[- ]networked|side[- ]effectful)\b",
    r"\bremote\s+sandbox\b.*\b(?:unverified|cannot be verified)\b",
)
SYNTHETIC_DATA_PROMPT_PATTERNS = (
    r"\bsynthetic\b",
    r"\bfake\b",
    r"\b(?:customer|production|user)\s+(?:data|records)\b",
)
REAL_SECRET_PROMPT_PATTERNS = (r"\breal\s+(?:bearer\s+)?(?:token|secret|credential)\b",)
PRODUCTION_DATA_PROMPT_PATTERNS = (
    r"\b(?:real\s+)?customer\s+(?:data|records)\b",
    r"\bproduction\s+(?:data|records)\b",
)
REAL_SECRET_REFUSAL_FIELDS = {
    "credential_use",
    "real_credential_use",
    "real_secret_access",
    "real_user_or_production_credential_accessed",
    "real_user_production_credential_accessed",
    "secret_value_recorded",
}
PRODUCTION_DATA_REFUSAL_FIELDS = {
    "customer_or_production_data_accessed",
    "customer_or_production_data_use",
    "production_or_customer_data_use",
}


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def load_cases(skill: Path) -> list[dict[str, Any]]:
    cases_path = skill.parent / "evals" / "cases.yaml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    assert isinstance(cases, list), f"{cases_path} must contain a top-level list"
    return cases


def fixture_by_id(skill: Path, fixture_id: str) -> dict[str, Any]:
    matches = [fixture for fixture in load_cases(skill) if fixture.get("id") == fixture_id]
    assert len(matches) == 1, f"{skill.parent.name} must have exactly one {fixture_id!r} fixture"
    return matches[0]


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


def safety_prompt_text(prompt: str) -> str:
    text = prompt.casefold()
    for negated_clause in (
        r"\b(?:it )?does not authorize\b.*?(?:\.|$)",
        r"\bdo not treat this approval as permission to use\b.*?(?:\.|$)",
        r"\bcannot access\b.*?(?:\.|$)",
    ):
        text = re.sub(negated_clause, " ", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def safety_prompt_requires_approval(prompt: str) -> bool:
    return contains_any(safety_prompt_text(prompt), *RISKY_SAFETY_PROMPT_PATTERNS)


def assert_false_refusal_field(
    expected: dict[str, Any], field_names: set[str], context: str
) -> None:
    assert any(expected.get(field) is False for field in field_names), (
        f"{context} lacks a concrete false no-real-data/secret refusal field"
    )


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
        properties = expected.get("properties_invariants")
        assert isinstance(properties, str) and properties.strip(), (
            f"{context} lacks properties/invariants"
        )
        coverage = expected.get("coverage_areas_plan")
        assert isinstance(coverage, list) and coverage, f"{context} lacks a coverage plan"
        assert all(isinstance(area, str) and area.strip() for area in coverage), (
            f"{context} has a non-string or blank coverage area"
        )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_eval_fixture_kinds_cover_positive_near_miss_safety_and_evidence(skill):
    kinds = {fixture["kind"] for fixture in load_cases(skill)}

    assert REQUIRED_FIXTURE_KINDS <= kinds


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_evidence_report_fields_are_explicit_structural_lists(skill):
    required_fields = REQUIRED_REPORT_FIELDS[skill.parent.name]
    declared_fixtures = [
        fixture
        for fixture in load_cases(skill)
        if fixture["kind"] == "evidence" and "required_report_fields" in fixture["expected"]
    ]

    assert len(declared_fixtures) == 1
    expected = declared_fixtures[0]["expected"]
    report_fields = expected["required_report_fields"]
    assert isinstance(report_fields, list)
    assert all(isinstance(field, str) and field.strip() for field in report_fields)
    assert len(report_fields) == len(set(report_fields)), "report fields must not be duplicated"
    assert set(report_fields) == required_fields


def test_blackbox_evidence_fixture_checks_boundary_linkage_and_not_run_structurally():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "reproducible-evidence-with-not-run-gap",
    )
    expected = fixture["expected"]

    assert expected["public_boundary_required"] is True
    assert expected["not_run_linkage"] == "scenario_id_with_execution_id_na"
    assert expected["not_run_reason_required"] is True
    assert expected["not_run_command_recorded"] is False
    assert expected["not_run_exit_status_recorded"] is False
    assert isinstance(expected["required_report_fields"], list)


def test_blackbox_retry_results_are_linked_structural_records():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = fixture["expected"]

    for field in ("execution_records", "result_records", "not_run_records"):
        assert isinstance(expected[field], list) and expected[field], (
            f"{field} must be a non-empty list"
        )
    for execution in expected["execution_records"]:
        assert {"execution_id", "attempt", "scenario_id"} <= execution.keys()
    for result in expected["result_records"]:
        assert {"scenario_id", "execution_id", "result_state"} <= result.keys()
        assert result["result_state"] in {"pass", "fail", "skip", "expected-failure"}
    for not_run in expected["not_run_records"]:
        assert {"scenario_id", "execution_id", "result_state", "reason"} <= not_run.keys()
        assert not_run["execution_id"] == "N/A"
        assert not_run["result_state"] == "not-run"
    assert expected["execution_id_linkage_required"] is True
    assert expected["retry_linkage_required"] is True
    assert isinstance(expected["retry_linkage"], dict)


def test_parameterized_evidence_mapping_checks_domains_counts_replay_and_limits():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-parameterized-testing" / "SKILL.md",
        "complete-reproducible-evidence-report",
    )
    expected = fixture["expected"]

    required_expectations = {
        "fixed_examples_required": True,
        "generated_examples_not_proof": True,
        "valid_invalid_unsupported_separated": True,
        "deterministic_seed": True,
        "replay_command_required": True,
        "environment_record_required": True,
        "runner_record_required": True,
        "oracle_reported": True,
        "discarded_count_reported": True,
        "truncated_count_reported": True,
        "exact_command_required": True,
        "exit_status_required": True,
        "must_report_not_run": True,
        "limitations_required": True,
    }
    for field, wanted in required_expectations.items():
        assert expected.get(field) is wanted, f"parameterized evidence lacks {field}: {wanted}"
    assert expected["seed"] == "161803"
    assert isinstance(expected["required_report_fields"], list)
    assert "shrinking_status" in expected["required_report_fields"]


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_safety_fixtures_encode_appropriate_gates(skill):
    for fixture in load_cases(skill):
        if fixture["kind"] != "safety":
            continue

        expected = fixture["expected"]
        prompt = fixture["prompt"]
        context = f"{fixture['id']} ({skill.parent.name})"
        assert isinstance(expected.get("requires_approval"), bool)
        assert expected.get("must_not_modify_product_code") is True

        if safety_prompt_requires_approval(prompt):
            assert expected["requires_approval"] is True, (
                f"{context} requests an approval-gated operation"
            )

        if contains_any(safety_prompt_text(prompt), *SYNTHETIC_DATA_PROMPT_PATTERNS):
            assert expected.get("synthetic_data_default") is True, (
                f"{context} lacks synthetic-data gating"
            )

        if contains_any(safety_prompt_text(prompt), *REAL_SECRET_PROMPT_PATTERNS):
            assert_false_refusal_field(expected, REAL_SECRET_REFUSAL_FIELDS, context)

        if contains_any(safety_prompt_text(prompt), *PRODUCTION_DATA_PROMPT_PATTERNS):
            assert_false_refusal_field(expected, PRODUCTION_DATA_REFUSAL_FIELDS, context)

        if contains_any(
            safety_prompt_text(prompt),
            r"redact",
            r"secret",
            r"token",
            r"personal data",
            r"unbounded",
        ):
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


def _imported_roots(tree: ast.AST) -> set[str]:
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
            if node.level:
                imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
    return imported_roots


def test_case_matrix_helper_uses_only_allowlisted_standard_library_imports():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imported_roots = _imported_roots(tree)

    assert not imported_roots & FORBIDDEN_HELPER_IMPORTS
    assert imported_roots <= ALLOWED_HELPER_IMPORTS, (
        f"helper imports outside the allowlist: {sorted(imported_roots - ALLOWED_HELPER_IMPORTS)}"
    )


def test_case_matrix_helper_uses_no_execution_or_filesystem_mutation_operations():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_HELPER_NAMES
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_HELPER_NAMES
