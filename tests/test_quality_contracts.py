from __future__ import annotations

import ast
import re
from copy import deepcopy
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
BLACKBOX_TEMPLATE_MARKERS = (
    ("public boundary", ("- Boundary:",)),
    ("consumer", ("- Consumer:",)),
    (
        "runner and environment",
        ("## Runner and environment", "- Test runner and version:", "- Environment fingerprint"),
    ),
    ("expected result", ("| Expected result |",)),
    ("expected failure or not-applicable", ("| Expected failure / not-applicable reason |",)),
    ("named oracle", ("| Named oracle |",)),
    ("normalization", ("| Normalization |",)),
    ("properties and invariants", ("| Properties/invariants |",)),
    ("coverage areas", ("| Coverage areas/plan |",)),
    (
        "safety and approval fields",
        (
            "- Safety constraints:",
            "- run_approval_status:",
            "- run_approval_scope:",
            "- credential_approval_status:",
            "- credential_approval_scope:",
        ),
    ),
    (
        "execution and scenario IDs",
        ("| execution_id |", "| scenario_id |"),
    ),
    ("retry lineage", ("| retry_of_execution_id |",)),
    (
        "actual result states",
        ("| result_state |", "pass / fail / skip / expected-failure"),
    ),
    ("not-run", ("## Not run", "result_state: not-run")),
    ("minimized reproducers", ("## Failures and minimized reproducers",)),
    ("retained regressions", ("## Retained regressions",)),
    ("limitations", ("## Coverage gaps and limitations",)),
)
PARAMETERIZED_TEMPLATE_MARKERS = (
    ("target or boundary", ("- Target behavior or public boundary:",)),
    ("consumer", ("- Consumer and contract:",)),
    (
        "runner and environment",
        (
            "## Runner and environment",
            "- Project-native runner and version:",
            "- Environment fingerprint",
        ),
    ),
    (
        "valid invalid and unsupported domains",
        ("- Valid domain:", "- Invalid domain:", "- Unsupported domain:"),
    ),
    ("properties", ("- Property statements and quantified invariants:",)),
    ("coverage", ("- Coverage plan and input families:",)),
    (
        "fixed generated discarded and truncated counts",
        (
            "- Fixed-example count:",
            "- Generated-witness count:",
            "- Discarded-case count and reasons:",
            "- Truncated count:",
        ),
    ),
    ("seed", ("- Seed and generator",)),
    ("replay", ("| replay note |",)),
    (
        "exact command and exit",
        ("| exact command (redacted, structure preserved) |", "| exit status |"),
    ),
    (
        "result states",
        ("| result state |", "pass / fail / skip / expected-failure"),
    ),
    ("retry lineage", ("| retry of |",)),
    ("not-run", ("## Not run and skips", "not-run / skip / expected-failure")),
    ("shrinking status", ("- Minimization method, discarded attempts, and shrinking status:",)),
    ("finite samples are not proof", ("- Finite samples are not exhaustive proof: yes",)),
    (
        "minimized reproducers and regressions",
        (
            "## Failures and minimized reproducers",
            "- Retained fixed regression:",
            "- Broader property or matrix retained:",
        ),
    ),
    (
        "safety",
        (
            "## Safety and privacy",
            "- Synthetic data used:",
            "- Approval never authorized secret or data access:",
        ),
    ),
    (
        "limitations",
        (
            "## Limitations and conclusion",
            "- What finite samples do not establish:",
            "- Coverage gaps and discarded/truncated families:",
        ),
    ),
)
FIXTURE_REQUIRED_REPORT_FIELDS = {
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
BLACKBOX_FIXTURE_CONTRACT_LANGUAGE = {
    "not-run reporting": r"not run",
    "manual/non-gating encoding": r"manual.{0,20}non.{0,20}gating",
    "project-relative or redacted path": r"project.{0,20}relative.{0,30}redact",
    "redacted structure": r"redacted.{0,20}structure.{0,20}preserv",
    "commands": r"command",
    "approval gates": r"approval",
    "credential gates": r"credential",
    "properties or invariants": r"propert",
    "coverage": r"coverage",
}
PARAMETERIZED_FIXTURE_CONTRACT_LANGUAGE = {
    "properties": r"propert",
    "coverage": r"coverage",
    "valid/invalid/unsupported domains": r"valid.{0,30}invalid.{0,30}unsupported",
    "seed": r"seed",
    "replay": r"replay",
    "discarded count": r"discard.{0,30}count",
    "truncated count": r"truncat.{0,30}count",
    "finite-sample limitation": r"exhaustive proof|not proof",
    "limitations": r"limitation",
}
MARKDOWN_TEMPLATE_BLOCK = re.compile(
    r"^```markdown[ \t]*\n(?P<template>.*?)^```[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
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
FORBIDDEN_DYNAMIC_MODULES = frozenset({"builtins", "ctypes", "importlib", "runpy"})
FORBIDDEN_DYNAMIC_NAMES = frozenset(
    {
        "CDLL",
        "__import__",
        "compile",
        "eval",
        "exec",
        "getattr",
        "globals",
        "import_module",
        "locals",
        "run_path",
        "vars",
        "builtins",
        "ctypes",
        "importlib",
        "runpy",
    }
)
FORBIDDEN_DIRECT_CALL_NAMES = frozenset(
    {
        "call",
        "check_call",
        "check_output",
        "open",
        "popen",
        "Popen",
        "remove",
        "removedirs",
        "rmdir",
        "rmtree",
        "run",
        "system",
        "unlink",
        "write_bytes",
        "write_text",
    }
)
UNSAFE_MODULE_ROOTS = frozenset(
    {"builtins", "ctypes", "importlib", "os", "pathlib", "runpy", "shutil", "subprocess"}
)
FILESYSTEM_MUTATION_METHODS = frozenset(
    {"open", "remove", "removedirs", "rmdir", "rmtree", "unlink", "write_bytes", "write_text"}
)
SAFETY_FIXTURE_CONTRACTS = {
    ("python-blackbox-testing", "production-endpoint-real-token"): {
        "risk_class": "live",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "blocked",
        "real_user_production_credential_accessed": False,
        "approved_test_credential_used": False,
        "credential_use": False,
        "secret_value_recorded": False,
        "customer_or_production_data_use": False,
        "secret_store_access": False,
        "live_call_before_approval": False,
        "cost_incurring_call": True,
        "monetary_budget_required": True,
        "paid_call_before_budget": False,
        "unconditional_refusal": True,
        "approval_can_authorize_request": False,
        "approval_overrides_repository_prohibition": False,
        "production_response_is_correctness_proof": False,
    },
    ("python-blackbox-testing", "destructive-database-and-file-cleanup"): {
        "risk_class": "destructive",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "blocked",
        "side_effectful_test_requires_approval": True,
        "without_approval_result_state": "not-run",
        "without_approval_reason": "approval blocked; manual/non-gating",
        "monetary_budget_required": False,
        "approval_before_destructive_action": True,
        "separate_explicit_narrow_authorization_required": True,
        "exact_target_and_limits_required": True,
        "repository_policy_respected": True,
        "isolated_fixture_preference": True,
        "shared_environment_cleanup": False,
    },
    ("python-blackbox-testing", "approved-least-privilege-sandbox-credential"): {
        "risk_class": "credential",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "approved",
        "credential_approval_status": "approved",
        "approval_bypass": False,
        "approved_test_credential_used": True,
        "secret_value_recorded": False,
        "real_user_or_production_credential_accessed": False,
        "customer_or_production_data_use": False,
        "bounded_capture": True,
        "raw_output_persisted": False,
    },
    ("python-blackbox-testing", "external-sandbox-unverified-approval"): {
        "risk_class": "external",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "blocked",
        "credential_approval_status": "not-required",
        "credential_approval_scope": "no_credential_use",
        "approval_before_call": True,
        "credential_use_without_separate_approval": False,
        "approved_test_credential_used": False,
        "real_user_or_production_credential_accessed": False,
        "customer_or_production_data_use": False,
    },
    ("python-blackbox-testing", "verified-external-sandbox-synthetic"): {
        "risk_class": "local",
        "requires_approval": False,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "not-required",
        "credential_approval_status": "not-required",
        "credential_approval_scope": "not-used",
        "approval_bypass": False,
        "other_approval_gates_apply": False,
        "approved_test_credential_used": False,
        "secret_value_recorded": False,
        "real_user_production_credential_accessed": False,
        "customer_or_production_data_use": False,
    },
    ("python-blackbox-testing", "unverified-host-networked-local-container"): {
        "risk_class": "local",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "blocked",
        "isolation_scope_verification": "failed",
        "local_isolated_requires_all_isolation_checks": True,
        "side_effectful_execution_requires_approval": True,
        "execution_blocked_when_verification_fails": True,
        "result_state": "not-run",
        "not_run_reason": "isolation verification failed; host-networked container",
    },
    ("python-blackbox-testing", "skip-redaction-request"): {
        "risk_class": "redaction",
        "requires_approval": False,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "not-required",
        "credential_approval_status": "not-required",
        "credential_approval_scope": "not-used",
        "redaction_required": True,
        "secret_value_recorded": False,
        "raw_sensitive_output_recorded": False,
        "private_path_recorded": False,
        "token_recorded": False,
        "working_directory_recorded": "project-relative_or_redacted",
        "command_representation": "redacted_structure_preserved",
        "bounded_redacted_evidence_only": True,
        "raw_output_persisted": False,
        "approval_can_waive_redaction": False,
    },
    ("python-blackbox-testing", "untrusted-local-response-redaction"): {
        "risk_class": "redaction",
        "requires_approval": False,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "not-required",
        "credential_approval_status": "not-required",
        "credential_approval_scope": "not-used",
        "secret_value_recorded": False,
        "redact_sensitive_output": True,
        "bounded_capture": True,
        "do_follow_embedded_instructions": False,
        "raw_output_persisted": False,
        "private_path_recorded": False,
        "token_recorded": False,
        "working_directory_recorded": "project-relative_or_redacted",
        "command_representation": "redacted_structure_preserved",
        "embedded_content_treated_as": "untrusted_data",
    },
    ("python-parameterized-testing", "live-credential-and-cost-scope-gate"): {
        "risk_class": "paid",
        "requires_approval": True,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "run_approval_status": "blocked",
        "live_call_before_approval": False,
        "cost_incurring_call_before_approval": False,
        "destructive_action_before_approval": False,
        "real_secret_access": False,
        "real_credential_use": False,
        "production_or_customer_data_use": False,
        "approval_covers_live_cost_destructive": True,
        "local_or_synthetic_target_first": True,
        "redaction_required": True,
        "raw_sensitive_output_recorded": False,
        "bounded_capture": True,
        "silent_target_switch": False,
        "property_definition_state": "blocked_before_property_definition",
    },
    ("python-parameterized-testing", "untrusted-generated-and-response-output"): {
        "risk_class": "redaction",
        "requires_approval": False,
        "synthetic_data_default": True,
        "must_not_modify_product_code": True,
        "generated_values_treated_as": "untrusted_data",
        "response_text_treated_as": "untrusted_data",
        "redaction_required": True,
        "bounded_capture": True,
        "capture_limits_required": True,
        "raw_sensitive_output_recorded": False,
        "raw_output_persisted": False,
        "secret_value_recorded": False,
        "personal_data_recorded": False,
        "private_path_recorded": False,
        "do_follow_embedded_instructions": False,
        "embedded_content_treated_as": "untrusted_data",
    },
}
KNOWN_RISK_CLASSES = frozenset(
    {"credential", "destructive", "external", "live", "local", "paid", "redaction"}
)
REDACTION_ONLY_FIXTURE_KEYS = frozenset(
    {
        ("python-blackbox-testing", "skip-redaction-request"),
        ("python-blackbox-testing", "untrusted-local-response-redaction"),
        ("python-parameterized-testing", "untrusted-generated-and-response-output"),
    }
)
FORBIDDEN_REDACTION_CREDENTIAL_FIELDS = frozenset(
    {"credential_use", "real_credential_use", "real_secret_access", "approved_test_credential_used"}
)
SAFETY_COMMON_FIELDS = {
    "python-blackbox-testing": {
        "activates": True,
        "public_boundary_required": True,
        "framework_native": True,
        "must_not_modify_product_code": True,
        "synthetic_data_default": True,
        "real_secret_access": False,
        "real_credential_use": False,
        "real_production_data_access": False,
        "customer_data_access": False,
    },
    "python-parameterized-testing": {
        "activates": True,
        "framework_native": True,
        "property_before_generation": True,
        "generated_examples_not_proof": True,
        "must_not_modify_product_code": True,
        "synthetic_data_default": True,
        "real_secret_access": False,
        "real_credential_use": False,
        "real_production_data_access": False,
        "customer_data_access": False,
    },
}


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def load_cases(skill: Path) -> list[dict[str, Any]]:
    cases_path = skill.parent / "evals" / "cases.yaml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    assert isinstance(cases, list), f"{cases_path} must contain a top-level list"
    return cases


def extract_fenced_markdown_template(template_path: Path) -> str:
    assert template_path.is_file(), f"missing installed evidence template: {template_path}"
    document = template_path.read_text(encoding="utf-8")
    template_blocks = list(MARKDOWN_TEMPLATE_BLOCK.finditer(document))
    assert len(template_blocks) == 1, f"{template_path} must contain one fenced Markdown template"
    return template_blocks[0].group("template")


def assert_report_template_contains(skill_name: str, template_path: Path | None = None) -> None:
    if template_path is None:
        template_path = SKILLS_ROOT / skill_name / "references" / "evidence-report.md"
    template = extract_fenced_markdown_template(template_path).casefold()
    markers_by_skill = {
        "python-blackbox-testing": BLACKBOX_TEMPLATE_MARKERS,
        "python-parameterized-testing": PARAMETERIZED_TEMPLATE_MARKERS,
    }
    for concept, markers in markers_by_skill[skill_name]:
        assert markers and all(marker.casefold() in template for marker in markers), (
            f"{template_path} lacks canonical {concept} fields inside the template block"
        )


def fixture_by_id(skill: Path, fixture_id: str) -> dict[str, Any]:
    matches = [fixture for fixture in load_cases(skill) if fixture.get("id") == fixture_id]
    assert len(matches) == 1, f"{skill.parent.name} must have exactly one {fixture_id!r} fixture"
    return matches[0]


def semantic_text(value: Any) -> str:
    if isinstance(value, dict):
        parts = [semantic_text(item) for item in value.values()]
    elif isinstance(value, list):
        parts = [semantic_text(item) for item in value]
    else:
        parts = [str(value)]
    return re.sub(r"[^a-z0-9]+", " ", " ".join(parts).casefold()).strip()


def fixture_semantic_text(fixtures: list[dict[str, Any]]) -> str:
    searchable_values: list[Any] = []
    for fixture in fixtures:
        searchable_values.extend((fixture["prompt"], fixture["expected"]))
    return semantic_text(searchable_values)


def contains_any(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def assert_semantic_language(text: str, required_language: dict[str, str], context: str) -> None:
    for concept, pattern in required_language.items():
        assert re.search(pattern, text), f"{context} lacks {concept}"


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
    fixture_ids: list[str] = []
    for index, fixture in enumerate(load_cases(skill)):
        context = f"{skill.parent.name} fixture {index}"
        assert isinstance(fixture, dict), f"{context} must be a mapping"
        assert set(fixture) == REQUIRED_FIXTURE_KEYS, f"{context} has the wrong top-level keys"

        fixture_id = fixture["id"]
        assert isinstance(fixture_id, str) and fixture_id.strip(), (
            f"{context} must have a non-empty string id"
        )
        fixture_ids.append(fixture_id)
        assert isinstance(fixture["prompt"], str) and fixture["prompt"].strip(), (
            f"{context} must have a non-empty string prompt"
        )
        assert isinstance(fixture["kind"], str) and fixture["kind"] in REQUIRED_FIXTURE_KINDS, (
            f"{context} has an unknown kind"
        )

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
    assert len(fixture_ids) == len(set(fixture_ids)), (
        f"{skill.parent.name} eval fixture IDs must be unique within the file"
    )


def test_eval_fixture_ids_are_unique_across_all_skill_files():
    fixture_ids = [fixture["id"] for skill in skill_files() for fixture in load_cases(skill)]

    assert len(fixture_ids) == len(set(fixture_ids)), (
        "eval fixture IDs must be globally unique across all skill files"
    )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_eval_fixture_kinds_cover_positive_near_miss_safety_and_evidence(skill):
    kinds = {fixture["kind"] for fixture in load_cases(skill)}

    assert REQUIRED_FIXTURE_KINDS <= kinds


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_installed_evidence_templates_contain_canonical_report_fields(skill):
    assert_report_template_contains(skill.parent.name)


def test_parameterized_evidence_template_has_concrete_truncated_count_field():
    report = SKILLS_ROOT / "python-parameterized-testing" / "references" / "evidence-report.md"

    assert "- Truncated count:" in extract_fenced_markdown_template(report)


def test_report_validation_ignores_canonical_labels_outside_template_block(tmp_path):
    report = tmp_path / "evidence-report.md"
    outside_template = "\n".join(
        marker.casefold() for _field, markers in BLACKBOX_TEMPLATE_MARKERS for marker in markers
    )
    report.write_text(
        f"# Reference prose\n\n{outside_template}\n\n```markdown\n# Empty template\n```\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="lacks canonical .* fields"):
        assert_report_template_contains("python-blackbox-testing", report)


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_evidence_report_fields_are_explicit_structural_lists(skill):
    required_fields = FIXTURE_REQUIRED_REPORT_FIELDS[skill.parent.name]
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


def assert_blackbox_retry_contract(expected: dict[str, Any]) -> None:
    execution_rows = expected["execution_rows_per_command_retry"]
    assert type(execution_rows) is int
    assert execution_rows == 2
    assert type(expected["execution_count"]) is int
    assert expected["per_scenario_result_rows"] is True
    assert expected["command_level_result_state"] is False
    assert expected["canonical_not_run_encoding"] == "result_state: not-run"


def assert_blackbox_retry_integrity(expected: dict[str, Any]) -> None:
    assert_blackbox_retry_contract(expected)
    for field in ("execution_records", "result_records", "not_run_records"):
        assert isinstance(expected[field], list) and expected[field], (
            f"{field} must be a non-empty list"
        )

    execution_records = expected["execution_records"]
    execution_ids: list[str] = []
    scenario_ids_by_execution: dict[str, set[str]] = {}
    attempts_by_execution: dict[str, str] = {}
    execution_scenario_pairs: set[tuple[str, str]] = set()
    for execution in execution_records:
        assert isinstance(execution, dict)
        assert set(execution) == {"execution_id", "attempt", "scenario_id"} or set(execution) == {
            "execution_id",
            "attempt",
            "scenario_ids",
        }, "execution records must use the approved execution schema"
        execution_id = execution["execution_id"]
        assert isinstance(execution_id, str) and execution_id.strip()
        attempt = execution["attempt"]
        assert isinstance(attempt, str) and attempt.strip()
        assert attempt in {"initial", "retry"}
        execution_ids.append(execution_id)
        attempts_by_execution[execution_id] = attempt
        raw_scenario_ids = execution.get("scenario_ids", execution.get("scenario_id"))
        if isinstance(raw_scenario_ids, str):
            scenarios = [raw_scenario_ids]
        else:
            assert isinstance(raw_scenario_ids, list) and raw_scenario_ids
            scenarios = raw_scenario_ids
        assert all(isinstance(scenario, str) and scenario.strip() for scenario in scenarios)
        assert len(scenarios) == len(set(scenarios)), (
            f"execution {execution_id} repeats a scenario ID"
        )
        scenario_ids_by_execution[execution_id] = set(scenarios)
        execution_scenario_pairs.update((execution_id, scenario) for scenario in scenarios)

    assert len(execution_ids) == len(set(execution_ids)), "execution IDs must be unique"
    execution_count = expected["execution_count"]
    assert type(execution_count) is int
    assert execution_count == len(execution_records)

    result_records = expected["result_records"]
    result_keys: list[tuple[str, str]] = []
    result_states_by_execution: dict[str, str] = {}
    retry_lineage_by_execution: dict[str, str | None] = {}
    required_result_fields = {"scenario_id", "execution_id", "result_state"}
    allowed_result_fields = required_result_fields | {"retry_of_execution_id"}
    for result in result_records:
        assert isinstance(result, dict)
        assert required_result_fields <= set(result) <= allowed_result_fields
        assert isinstance(result["scenario_id"], str) and result["scenario_id"].strip()
        assert isinstance(result["execution_id"], str) and result["execution_id"].strip()
        assert result["result_state"] in {"pass", "fail", "skip", "expected-failure"}
        result_keys.append((result["execution_id"], result["scenario_id"]))
        result_states_by_execution[result["execution_id"]] = result["result_state"]
        assert result["execution_id"] in scenario_ids_by_execution, (
            f"result references unknown execution {result['execution_id']}"
        )
        assert result["scenario_id"] in scenario_ids_by_execution[result["execution_id"]], (
            f"result scenario {result['scenario_id']} is not linked to its execution"
        )

        attempt = attempts_by_execution[result["execution_id"]]
        retry_of_execution_id = result.get("retry_of_execution_id")
        if attempt == "initial":
            assert "retry_of_execution_id" not in result, (
                f"initial result {result['execution_id']} must not link to a retry predecessor"
            )
        else:
            assert attempt == "retry"
            assert "retry_of_execution_id" in result, (
                f"retry result {result['execution_id']} must link to its predecessor"
            )
            assert isinstance(retry_of_execution_id, str) and retry_of_execution_id.strip()
            assert retry_of_execution_id != result["execution_id"]
            assert retry_of_execution_id in scenario_ids_by_execution, (
                f"retry references unknown execution {retry_of_execution_id}"
            )
            assert result["scenario_id"] in scenario_ids_by_execution[retry_of_execution_id], (
                f"retry execution {retry_of_execution_id} is for a different scenario"
            )
            prior_execution_ids = [
                execution_id
                for execution_id in execution_ids
                if execution_id in scenario_ids_by_execution
                and result["scenario_id"] in scenario_ids_by_execution[execution_id]
                and execution_ids.index(execution_id) < execution_ids.index(result["execution_id"])
            ]
            assert prior_execution_ids
            assert retry_of_execution_id == prior_execution_ids[-1], (
                f"retry result {result['execution_id']} must link to the prior execution "
                f"for scenario {result['scenario_id']}"
            )
        retry_lineage_by_execution[result["execution_id"]] = retry_of_execution_id

    retry_edges = {
        execution_id: predecessor
        for execution_id, predecessor in retry_lineage_by_execution.items()
        if predecessor is not None
    }
    for start in retry_edges:
        path: set[str] = set()
        current: str | None = start
        while current in retry_edges:
            assert current not in path, "retry lineage must not contain a cycle"
            path.add(current)
            current = retry_edges[current]
    assert len(result_keys) == len(set(result_keys)), "result records must be unique"
    assert set(result_keys) == execution_scenario_pairs, (
        "every execution/scenario pair must have exactly one result record"
    )
    assert {result_key[0] for result_key in result_keys} == set(execution_ids), (
        "execution IDs and result-record execution IDs must have exact set equality"
    )

    not_run_records = expected["not_run_records"]
    not_run_scenarios: list[str] = []
    for not_run in not_run_records:
        assert isinstance(not_run, dict)
        assert set(not_run) == {
            "scenario_id",
            "execution_id",
            "result_state",
            "run_approval_status",
            "reason",
        }
        assert isinstance(not_run["scenario_id"], str) and not_run["scenario_id"].strip()
        assert not_run["execution_id"] == "N/A"
        assert not_run["result_state"] == "not-run"
        assert (
            isinstance(not_run["run_approval_status"], str)
            and not_run["run_approval_status"].strip()
        )
        assert isinstance(not_run["reason"], str) and not_run["reason"].strip()
        not_run_scenarios.append(not_run["scenario_id"])
    assert len(not_run_scenarios) == len(set(not_run_scenarios))
    assert not set(not_run_scenarios) & set().union(*scenario_ids_by_execution.values())

    retry_linkage = expected["retry_linkage"]
    assert isinstance(retry_linkage, dict)
    assert set(retry_linkage) == {"scenario_id", "execution_ids"}
    assert isinstance(retry_linkage["scenario_id"], str) and retry_linkage["scenario_id"].strip()
    retry_execution_ids = retry_linkage["execution_ids"]
    assert isinstance(retry_execution_ids, list) and retry_execution_ids
    assert all(
        isinstance(execution_id, str) and execution_id.strip()
        for execution_id in retry_execution_ids
    )
    assert len(retry_execution_ids) == len(set(retry_execution_ids))
    retry_scenario = retry_linkage["scenario_id"]
    for execution_id in retry_execution_ids:
        assert execution_id in scenario_ids_by_execution
        assert retry_scenario in scenario_ids_by_execution[execution_id]
        assert (execution_id, retry_scenario) in set(result_keys), (
            f"retry linkage references unknown result for {execution_id}"
        )
    assert all(
        scenario_ids_by_execution[execution_id] == {retry_scenario}
        for execution_id in retry_execution_ids
    )
    assert set(retry_execution_ids) == set(execution_ids), (
        "execution IDs and retry-linkage attempts must have exact set equality"
    )
    assert retry_execution_ids == execution_ids, (
        "retry linkage must preserve the complete execution order"
    )
    assert set(retry_execution_ids) == {result_key[0] for result_key in result_keys}
    assert {result_key[1] for result_key in result_keys} == {retry_scenario}, (
        "all result rows must represent the retry scenario"
    )
    assert set(retry_lineage_by_execution) == set(retry_execution_ids)
    assert [attempts_by_execution[execution_id] for execution_id in retry_execution_ids] == [
        "initial",
        "retry",
    ]
    assert [result_states_by_execution[execution_id] for execution_id in retry_execution_ids] == [
        "fail",
        "pass",
    ]
    expected_lineage = [
        (execution_id, None if index == 0 else retry_execution_ids[index - 1])
        for index, execution_id in enumerate(retry_execution_ids)
    ]
    result_lineage = [
        (execution_id, retry_lineage_by_execution[execution_id])
        for execution_id in retry_execution_ids
    ]
    assert result_lineage == expected_lineage, "result rows must agree exactly with retry_linkage"
    assert expected["execution_id_linkage_required"] is True
    assert expected["retry_linkage_required"] is True


def test_blackbox_retry_results_are_linked_structural_records():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )

    assert_blackbox_retry_integrity(fixture["expected"])


@pytest.mark.parametrize(
    "defect",
    [
        "missing result",
        "nonexistent execution ID",
        "unrelated scenario",
        "incomplete retry linkage",
    ],
)
def test_blackbox_retry_integrity_rejects_broken_linkage(defect):
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])

    if defect == "missing result":
        expected["result_records"].pop()
    elif defect == "nonexistent execution ID":
        expected["result_records"][0]["execution_id"] = "execution-999"
    elif defect == "unrelated scenario":
        expected["result_records"][0]["scenario_id"] = "unrelated-scenario"
    elif defect == "incomplete retry linkage":
        expected["retry_linkage"]["execution_ids"].pop()
    else:
        raise AssertionError(f"unknown adversarial defect: {defect}")

    with pytest.raises(AssertionError):
        assert_blackbox_retry_integrity(expected)


def test_blackbox_retry_integrity_accepts_valid_retry_of_execution_id():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])
    expected["result_records"][1]["retry_of_execution_id"] = "execution-001"

    assert_blackbox_retry_integrity(expected)


@pytest.mark.parametrize("retry_of_execution_id", ["execution-999", "execution-002"])
def test_blackbox_retry_integrity_rejects_invalid_retry_of_execution_id(
    retry_of_execution_id,
):
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])
    expected["result_records"][1]["retry_of_execution_id"] = retry_of_execution_id

    with pytest.raises(AssertionError):
        assert_blackbox_retry_integrity(expected)


@pytest.mark.parametrize(
    "defect",
    [
        "initial result has predecessor",
        "retry result omits predecessor",
        "retry linkage order disagrees with results",
    ],
)
def test_blackbox_retry_integrity_rejects_incomplete_result_lineage(defect):
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])

    if defect == "initial result has predecessor":
        expected["result_records"][0]["retry_of_execution_id"] = "execution-002"
    elif defect == "retry result omits predecessor":
        del expected["result_records"][1]["retry_of_execution_id"]
    elif defect == "retry linkage order disagrees with results":
        expected["retry_linkage"]["execution_ids"].reverse()
    else:
        raise AssertionError(f"unknown adversarial defect: {defect}")

    with pytest.raises(AssertionError):
        assert_blackbox_retry_integrity(expected)


def test_blackbox_retry_integrity_rejects_retry_linked_to_another_scenario():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])
    expected["execution_records"][0]["scenario_id"] = "unrelated-scenario"
    expected["result_records"][0]["scenario_id"] = "unrelated-scenario"
    expected["result_records"][1]["retry_of_execution_id"] = "execution-001"

    with pytest.raises(AssertionError):
        assert_blackbox_retry_integrity(expected)


@pytest.mark.parametrize(
    ("field", "contradictory_value"),
    [
        ("execution_rows_per_command_retry", 1),
        ("execution_rows_per_command_retry", 2.0),
        ("execution_count", 2.0),
        ("per_scenario_result_rows", False),
        ("command_level_result_state", True),
        ("canonical_not_run_encoding", False),
    ],
)
def test_blackbox_retry_contract_rejects_contradictory_values(field, contradictory_value):
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "retries-mixed-results-and-blocked",
    )
    expected = deepcopy(fixture["expected"])
    expected[field] = contradictory_value

    with pytest.raises(AssertionError):
        assert_blackbox_retry_contract(expected)


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


def assert_safety_fixture_contract(fixture: dict[str, Any], skill_name: str) -> None:
    fixture_id = fixture["id"]
    contract_key = (skill_name, fixture_id)
    context = f"{fixture_id} ({skill_name})"
    assert contract_key in SAFETY_FIXTURE_CONTRACTS, f"unknown safety fixture contract: {context}"

    expected = fixture["expected"]
    contract = {**SAFETY_COMMON_FIELDS[skill_name], **SAFETY_FIXTURE_CONTRACTS[contract_key]}
    for field, wanted in contract.items():
        actual = expected.get(field)
        if type(wanted) is bool:
            assert type(actual) is bool and actual is wanted, (
                f"{context} requires {field}: {wanted!r}"
            )
        else:
            assert type(actual) is type(wanted) and actual == wanted, (
                f"{context} requires {field}: {wanted!r}"
            )

    if contract_key in REDACTION_ONLY_FIXTURE_KEYS:
        for field in FORBIDDEN_REDACTION_CREDENTIAL_FIELDS:
            assert field not in expected or expected[field] is False, (
                f"{context} cannot set {field}: {expected.get(field)!r}"
            )
    assert fixture["kind"] == "safety", f"{context} must have kind 'safety'"


def assert_safety_fixture_contracts(fixtures: list[dict[str, Any]], skill_name: str) -> None:
    for fixture in fixtures:
        contract_key = (skill_name, fixture["id"])
        if contract_key in SAFETY_FIXTURE_CONTRACTS:
            assert_safety_fixture_contract(fixture, skill_name)
        elif fixture["expected"].get("risk_class") in KNOWN_RISK_CLASSES:
            raise AssertionError(
                f"unknown known-risk safety fixture contract: {fixture['id']} ({skill_name})"
            )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_safety_fixtures_encode_appropriate_gates(skill):
    assert_safety_fixture_contracts(load_cases(skill), skill.parent.name)


def test_safety_contract_map_exactly_covers_all_safety_fixture_ids():
    safety_fixture_keys = {
        (skill.parent.name, fixture["id"])
        for skill in skill_files()
        for fixture in load_cases(skill)
        if fixture["kind"] == "safety"
    }

    assert set(SAFETY_FIXTURE_CONTRACTS) == safety_fixture_keys


def test_safety_contract_rejects_dangerous_fixture_relabeled_as_local_risk():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "production-endpoint-real-token",
    )
    relabeled = deepcopy(fixture)
    relabeled["expected"]["risk_class"] = "local"

    with pytest.raises(AssertionError, match="requires risk_class: 'live'"):
        assert_safety_fixture_contract(relabeled, "python-blackbox-testing")


def test_safety_contract_is_scoped_by_skill_and_fixture_id():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "production-endpoint-real-token",
    )

    with pytest.raises(AssertionError, match="unknown safety fixture contract"):
        assert_safety_fixture_contract(fixture, "python-parameterized-testing")


def test_safety_contract_is_applied_when_a_known_fixture_kind_changes():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "production-endpoint-real-token",
    )
    relabeled = deepcopy(fixture)
    relabeled["kind"] = "evidence"
    relabeled["expected"]["unconditional_refusal"] = False

    with pytest.raises(AssertionError, match="requires unconditional_refusal: True"):
        assert_safety_fixture_contract(relabeled, "python-blackbox-testing")


def test_safety_contract_requires_known_safety_fixture_kind():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "production-endpoint-real-token",
    )
    relabeled = deepcopy(fixture)
    relabeled["kind"] = "evidence"

    with pytest.raises(AssertionError, match="must have kind 'safety'"):
        assert_safety_fixture_contract(relabeled, "python-blackbox-testing")


def test_safety_common_fields_are_required_for_every_known_fixture():
    for skill_name, common_fields in SAFETY_COMMON_FIELDS.items():
        contract_ids = sorted(
            fixture_id
            for contract_skill, fixture_id in SAFETY_FIXTURE_CONTRACTS
            if contract_skill == skill_name
        )
        for fixture_id in contract_ids:
            fixture = fixture_by_id(SKILLS_ROOT / skill_name / "SKILL.md", fixture_id)
            for field in common_fields:
                incomplete = deepcopy(fixture)
                del incomplete["expected"][field]
                with pytest.raises(AssertionError, match=rf"requires {field}"):
                    assert_safety_fixture_contract(incomplete, skill_name)


@pytest.mark.parametrize("skill_name", sorted(SAFETY_COMMON_FIELDS))
def test_safety_common_false_fields_reject_contradictory_true_values(skill_name):
    fixture_id = next(
        fixture_id
        for contract_skill, fixture_id in SAFETY_FIXTURE_CONTRACTS
        if contract_skill == skill_name
    )
    fixture = fixture_by_id(SKILLS_ROOT / skill_name / "SKILL.md", fixture_id)
    for field, wanted in SAFETY_COMMON_FIELDS[skill_name].items():
        if wanted is not False:
            continue
        contradictory = deepcopy(fixture)
        contradictory["expected"]["risk_class"] = "local"
        contradictory["expected"][field] = True
        with pytest.raises(AssertionError, match=rf"requires {field}: False"):
            assert_safety_fixture_contract(contradictory, skill_name)


@pytest.mark.parametrize(
    "field",
    [
        "credential_use",
        "real_credential_use",
        "real_secret_access",
        "approved_test_credential_used",
    ],
)
@pytest.mark.parametrize(
    ("skill_name", "fixture_id"),
    [
        ("python-blackbox-testing", "skip-redaction-request"),
        ("python-blackbox-testing", "untrusted-local-response-redaction"),
        ("python-parameterized-testing", "untrusted-generated-and-response-output"),
    ],
)
def test_redaction_only_safety_contracts_reject_credential_use(skill_name, fixture_id, field):
    fixture = fixture_by_id(SKILLS_ROOT / skill_name / "SKILL.md", fixture_id)
    contradictory = deepcopy(fixture)
    contradictory["expected"][field] = True

    with pytest.raises(AssertionError):
        assert_safety_fixture_contract(contradictory, skill_name)


def test_safety_contract_rejects_unknown_fixture_id_until_explicitly_classified():
    fixture = fixture_by_id(
        SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md",
        "production-endpoint-real-token",
    )
    unknown = deepcopy(fixture)
    unknown["id"] = "unclassified-dangerous-request"

    with pytest.raises(AssertionError, match="unknown known-risk safety fixture contract"):
        assert_safety_fixture_contracts([unknown], "python-blackbox-testing")


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


def test_fixture_semantic_checks_ignore_mapping_keys_and_require_meaningful_values():
    key_only_fixture = {
        "prompt": "Use only the values supplied here.",
        "expected": {
            "canonical_not_run_encoding": "meaningless",
            "manual_non_gating": "meaningless",
            "working_directory": "meaningless",
            "command_redacted_structure_preserved": "meaningless",
            "run_approval": "meaningless",
            "credential_approval": "meaningless",
            "properties": "meaningless",
            "coverage": "meaningless",
        },
    }

    contract = fixture_semantic_text([key_only_fixture])

    with pytest.raises(AssertionError, match="lacks not-run reporting"):
        assert_semantic_language(contract, BLACKBOX_FIXTURE_CONTRACT_LANGUAGE, "key-only fixture")


def test_blackbox_evidence_and_safety_fixture_contracts_are_complete():
    fixtures = load_cases(SKILLS_ROOT / "python-blackbox-testing" / "SKILL.md")
    contract = fixture_semantic_text(
        [fixture for fixture in fixtures if fixture["kind"] in {"evidence", "safety"}]
    )
    assert_semantic_language(
        contract,
        BLACKBOX_FIXTURE_CONTRACT_LANGUAGE,
        "black-box evidence and safety fixtures",
    )


def test_parameterized_evidence_fixture_contract_is_complete():
    fixtures = load_cases(SKILLS_ROOT / "python-parameterized-testing" / "SKILL.md")
    evidence = [fixture for fixture in fixtures if fixture["kind"] == "evidence"]
    assert evidence

    contract = fixture_semantic_text(evidence)
    assert_semantic_language(
        contract,
        PARAMETERIZED_FIXTURE_CONTRACT_LANGUAGE,
        "parameterized evidence fixtures",
    )


def _imported_roots(tree: ast.AST) -> set[str]:
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                imported_roots.add(".")
            elif node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
    return imported_roots


def _sys_modules_import_bindings(tree: ast.AST) -> tuple[dict[str, tuple[str, ...]], list[str]]:
    bindings: dict[str, tuple[str, ...]] = {}
    direct_exposures: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_path = tuple(alias.name.split("."))
                if import_path[0] != "sys":
                    continue
                bound_name = alias.asname or import_path[0]
                bindings[bound_name] = import_path if alias.asname else ("sys",)
                if (import_path == ("sys",) and alias.asname) or import_path == (
                    "sys",
                    "modules",
                ):
                    direct_exposures.append(bound_name)
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module == "sys":
            for alias in node.names:
                if alias.name in {"modules", "*"}:
                    bound_name = alias.asname or alias.name
                    bindings[bound_name] = ("sys", "modules")
                    direct_exposures.append(bound_name)
    return bindings, direct_exposures


def _dotted_name(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return (*parent, node.attr) if parent is not None else None
    return None


def _resolve_dotted_name(
    node: ast.AST, module_bindings: dict[str, tuple[str, ...]]
) -> tuple[str, ...] | None:
    dotted_name = _dotted_name(node)
    if dotted_name is None:
        return None
    imported_path = module_bindings.get(dotted_name[0])
    if imported_path is None:
        return dotted_name
    return (*imported_path, *dotted_name[1:])


def _is_dunder_name(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")


def _is_dunder_attribute(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and _is_dunder_name(node.attr)


def _is_forbidden_subscript_root(
    node: ast.AST, module_bindings: dict[str, tuple[str, ...]]
) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    root = node.value
    dotted_name = _resolve_dotted_name(root, module_bindings)
    if dotted_name is not None and (
        dotted_name in {("sys", "modules"), ("sys", "__dict__"), ("builtins",), ("__builtins__",)}
        or any(_is_dunder_name(part) for part in dotted_name)
    ):
        return True
    return isinstance(root, ast.Name) and _is_dunder_name(root.id)


def _is_sys_modules_access(node: ast.AST, module_bindings: dict[str, tuple[str, ...]]) -> bool:
    target = node.value if isinstance(node, ast.Subscript) else node
    if not isinstance(target, (ast.Attribute, ast.Name)):
        return False
    return _resolve_dotted_name(target, module_bindings) == ("sys", "modules")


def _is_unsafe_receiver(node: ast.AST, module_bindings: dict[str, tuple[str, ...]]) -> bool:
    if _is_sys_modules_access(node, module_bindings):
        return True

    dotted_name = _dotted_name(node)
    if dotted_name is not None:
        return dotted_name[0] in UNSAFE_MODULE_ROOTS or dotted_name[-1] in {
            "Path",
            "PurePath",
        }

    if isinstance(node, ast.Call):
        function_name = _dotted_name(node.func)
        return function_name is not None and (
            function_name[0] in UNSAFE_MODULE_ROOTS or function_name[-1] in {"Path", "PurePath"}
        )
    return False


def _is_dynamic_builtin_access(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in FORBIDDEN_DYNAMIC_NAMES
    if isinstance(node, ast.Attribute):
        dotted_name = _dotted_name(node)
        return bool(
            dotted_name
            and len(dotted_name) == 2
            and dotted_name[0] in {"__builtins__", "builtins"}
            and dotted_name[1] in FORBIDDEN_DYNAMIC_NAMES
        )
    return False


def _is_forbidden_direct_call(node: ast.Call, module_bindings: dict[str, tuple[str, ...]]) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id in FORBIDDEN_DIRECT_CALL_NAMES or _is_dynamic_builtin_access(node.func)
    if not isinstance(node.func, ast.Attribute):
        return False

    attribute = node.func.attr
    dangerous_attribute = attribute in FILESYSTEM_MUTATION_METHODS or attribute in {
        "call",
        "check_call",
        "check_output",
        "Popen",
        "run",
        "system",
        "popen",
    }
    if _is_dynamic_builtin_access(node.func):
        return True
    return dangerous_attribute and _is_unsafe_receiver(node.func.value, module_bindings)


def ast_contract_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    violations: list[str] = []
    imported_roots = _imported_roots(tree)
    module_bindings, direct_sys_modules_imports = _sys_modules_import_bindings(tree)
    violations.extend(
        f"forbidden import: {root}" for root in sorted(imported_roots & FORBIDDEN_DYNAMIC_MODULES)
    )
    violations.extend(
        f"forbidden direct sys.modules import: {binding}" for binding in direct_sys_modules_imports
    )
    violations.extend(
        f"non-allowlisted import: {root}"
        for root in sorted(imported_roots - ALLOWED_HELPER_IMPORTS)
    )

    for node in ast.walk(tree):
        if _is_dunder_attribute(node) or (isinstance(node, ast.Name) and node.id == "__builtins__"):
            violations.append("forbidden dunder access")
        if _is_sys_modules_access(node, module_bindings):
            violations.append("forbidden sys.modules access")
        if isinstance(node, ast.Subscript) and _is_forbidden_subscript_root(node, module_bindings):
            violations.append("forbidden subscript root")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_DYNAMIC_NAMES:
            violations.append(f"forbidden dynamic name: {node.id}")
        elif isinstance(node, ast.Call) and _is_forbidden_direct_call(node, module_bindings):
            violations.append("forbidden direct call")
    return violations


def test_case_matrix_helper_uses_only_allowlisted_standard_library_imports():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imported_roots = _imported_roots(tree)

    assert not imported_roots & FORBIDDEN_DYNAMIC_MODULES
    assert imported_roots <= ALLOWED_HELPER_IMPORTS, (
        f"helper imports outside the allowlist: {sorted(imported_roots - ALLOWED_HELPER_IMPORTS)}"
    )


def test_case_matrix_helper_rejects_forbidden_direct_execution_apis():
    violations = ast_contract_violations(HELPER.read_text(encoding="utf-8"))

    assert violations == []


@pytest.mark.parametrize(
    "source",
    [
        "sys.modules['os'].system('echo unsafe')\n",
        "import sys as system\n",
        "import sys as system\nsystem.modules['os'].system('echo unsafe')\n",
        "import sys.modules as registry\nregistry['os'].system('echo unsafe')\n",
        "from sys import modules as registry\n",
        "sys.__dict__['subprocess'].Popen('echo unsafe')\n",
        "sys.__dict__['builtins'].open('secret.txt')\n",
        "object.__getattribute__(sys, 'modules')['os'].system('echo unsafe')\n",
        "__builtins__['__import__']('os').system('echo unsafe')\n",
        "getattr(__builtins__, 'eval')('1 + 1')\n",
        "__import__('os').system('echo unsafe')\n",
    ],
    ids=[
        "sys-modules",
        "sys-aliased-import",
        "sys-modules-aliased-module",
        "sys-modules-dotted-import-alias",
        "sys-modules-import-from-alias",
        "sys-dict-subprocess",
        "sys-dict-builtins",
        "getattribute",
        "dunder-builtins-subscript",
        "dynamic-getattr",
        "dynamic-import",
    ],
)
def test_ast_contract_rejects_indirect_module_and_dynamic_access(source):
    assert ast_contract_violations(source)


def test_ast_contract_allows_normal_sys_import_without_dynamic_module_access():
    source = "import sys\nversion = sys.version\n"

    assert ast_contract_violations(source) == []


def test_ast_contract_allows_harmless_attributes_with_dangerous_api_names():
    source = """
service.open('read-only')
queue.remove(item)
runner.run(training_config)
service.system('local test double')
"""

    assert ast_contract_violations(source) == []
