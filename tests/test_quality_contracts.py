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
REPORT_TEMPLATE_MARKERS = {
    "python-blackbox-testing": {
        "boundary": ("Boundary",),
        "consumer": ("Consumer",),
        "runner and environment": (
            "Runner and environment",
            "Environment fingerprint",
        ),
        "expected result and failure": (
            "Expected result",
            "Expected failure / not-applicable reason",
        ),
        "properties and invariants": ("Properties/invariants",),
        "coverage areas": ("Coverage areas/plan",),
        "safety and approvals": (
            "Safety and privacy",
            "run_approval_status",
            "credential_approval_status",
        ),
        "execution and scenario IDs": ("execution_id", "scenario_id"),
        "result states": ("pass / fail / skip / expected-failure",),
        "minimized reproducers": ("Failures and minimized reproducers",),
        "retained regressions": ("Retained regressions",),
        "not-run": ("Not run",),
        "limitations": ("Coverage gaps and limitations",),
    },
    "python-parameterized-testing": {
        "target and boundary": ("Target behavior or public boundary",),
        "runner and environment": (
            "Runner and environment",
            "Project-native runner and version",
            "Environment fingerprint",
        ),
        "valid, invalid, and unsupported domains": (
            "Valid domain",
            "Invalid domain",
            "Unsupported domain",
        ),
        "properties": ("Property statements and quantified invariants",),
        "coverage": ("Coverage plan and input families",),
        "fixed, generated, discarded, and truncated counts": (
            "Fixed-example count",
            "Generated-witness count",
            "Discarded-case count",
            "Truncated",
        ),
        "seed and replay": ("Seed and generator", "replay"),
        "exact command and exit status": ("exact command", "exit status"),
        "result states": ("pass / fail / skip / expected-failure",),
        "minimized reproducers and regressions": (
            "Failures and minimized reproducers",
            "Retained fixed regression",
        ),
        "safety": ("Safety and privacy",),
        "not-run": ("Not run and skips",),
        "limitations": ("Limitations and conclusion",),
    },
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
RISK_CLASSES = frozenset(
    {
        "local",
        "redaction",
        "live",
        "external",
        "destructive",
        "credential",
        "paid",
        "flaky",
        "production",
    }
)
APPROVAL_REQUIRED_RISKS = frozenset({"live", "external", "destructive", "credential", "paid"})
NO_REAL_DATA_RISKS = frozenset({"live", "production", "paid"})
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
CREDENTIAL_PROHIBITION_FIELDS = {
    "real_user_or_production_credential_accessed",
    "real_user_production_credential_accessed",
}
REDACTION_FIELDS = {
    "raw_output_persisted",
    "raw_sensitive_output_recorded",
    "secret_value_recorded",
}


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def load_cases(skill: Path) -> list[dict[str, Any]]:
    cases_path = skill.parent / "evals" / "cases.yaml"
    cases = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    assert isinstance(cases, list), f"{cases_path} must contain a top-level list"
    return cases


def assert_report_template_contains(skill_name: str) -> None:
    template_path = SKILLS_ROOT / skill_name / "references" / "evidence-report.md"
    assert template_path.is_file(), f"missing installed evidence template: {template_path}"
    template = template_path.read_text(encoding="utf-8").casefold()
    for concept, markers in REPORT_TEMPLATE_MARKERS[skill_name].items():
        assert all(marker.casefold() in template for marker in markers), (
            f"{template_path} lacks canonical {concept} fields"
        )


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
        f"{skill.parent.name} eval fixture ids must be globally unique"
    )


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_eval_fixture_kinds_cover_positive_near_miss_safety_and_evidence(skill):
    kinds = {fixture["kind"] for fixture in load_cases(skill)}

    assert REQUIRED_FIXTURE_KINDS <= kinds


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_installed_evidence_templates_contain_canonical_report_fields(skill):
    assert_report_template_contains(skill.parent.name)


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

    execution_records = expected["execution_records"]
    execution_ids: list[str] = []
    scenario_ids_by_execution: dict[str, set[str]] = {}
    for execution in execution_records:
        assert isinstance(execution, dict)
        assert set(execution) == {"execution_id", "attempt", "scenario_id"} or set(execution) == {
            "execution_id",
            "attempt",
            "scenario_ids",
        }, "execution records must use the approved execution schema"
        execution_id = execution["execution_id"]
        assert isinstance(execution_id, str) and execution_id.strip()
        execution_ids.append(execution_id)
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

    assert len(execution_ids) == len(set(execution_ids)), "execution IDs must be unique"
    assert expected["execution_count"] == len(execution_records)

    result_records = expected["result_records"]
    result_keys: list[tuple[str, str]] = []
    for result in result_records:
        assert isinstance(result, dict)
        assert set(result) == {"scenario_id", "execution_id", "result_state"}
        assert isinstance(result["scenario_id"], str) and result["scenario_id"].strip()
        assert isinstance(result["execution_id"], str) and result["execution_id"].strip()
        assert result["result_state"] in {"pass", "fail", "skip", "expected-failure"}
        result_keys.append((result["execution_id"], result["scenario_id"]))
        assert result["execution_id"] in scenario_ids_by_execution, (
            f"result references unknown execution {result['execution_id']}"
        )
        assert result["scenario_id"] in scenario_ids_by_execution[result["execution_id"]], (
            f"result scenario {result['scenario_id']} is not linked to its execution"
        )
    assert len(result_keys) == len(set(result_keys)), "result records must be unique"

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
    assert expected["execution_id_linkage_required"] is True
    assert expected["retry_linkage_required"] is True


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
        context = f"{fixture['id']} ({skill.parent.name})"
        risk_class = expected.get("risk_class")
        assert risk_class in RISK_CLASSES, f"{context} lacks a valid risk_class"
        assert isinstance(expected.get("requires_approval"), bool)
        assert expected.get("must_not_modify_product_code") is True

        if risk_class in APPROVAL_REQUIRED_RISKS:
            assert expected["requires_approval"] is True, (
                f"{context} is an approval-gated {risk_class} risk"
            )

        if risk_class in NO_REAL_DATA_RISKS:
            assert_false_refusal_field(expected, REAL_SECRET_REFUSAL_FIELDS, context)
            assert_false_refusal_field(expected, PRODUCTION_DATA_REFUSAL_FIELDS, context)

        if risk_class == "credential":
            status = expected.get("credential_approval_status")
            assert isinstance(status, str) and status.strip(), (
                f"{context} lacks credential approval status"
            )
            scope = expected.get("credential_approval_scope")
            assert isinstance(scope, (str, list)) and scope, (
                f"{context} lacks credential approval scope"
            )
            assert expected.get("secret_value_recorded") is False
            assert_false_refusal_field(expected, CREDENTIAL_PROHIBITION_FIELDS, context)

        if risk_class == "redaction":
            assert (
                expected.get("redaction_required") is True
                or expected.get("redact_sensitive_output") is True
            ), f"{context} lacks a redaction expectation"
            assert any(expected.get(field) is False for field in REDACTION_FIELDS), (
                f"{context} lacks a concrete no-raw-output expectation"
            )


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
            if node.level:
                imported_roots.add(".")
            elif node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
    return imported_roots


def _root_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _root_name(node.value)
    return None


def _is_forbidden_direct_call(node: ast.Call) -> bool:
    if isinstance(node.func, ast.Name):
        return node.func.id in FORBIDDEN_DIRECT_CALL_NAMES
    if not isinstance(node.func, ast.Attribute):
        return False

    attribute = node.func.attr
    if attribute in FORBIDDEN_DYNAMIC_NAMES:
        return True
    if attribute in FILESYSTEM_MUTATION_METHODS:
        return True
    return (
        attribute
        in {
            "call",
            "check_call",
            "check_output",
            "Popen",
            "run",
            "system",
            "popen",
        }
        and _root_name(node.func.value) in UNSAFE_MODULE_ROOTS
    )


def test_case_matrix_helper_uses_only_allowlisted_standard_library_imports():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))
    imported_roots = _imported_roots(tree)

    assert not imported_roots & FORBIDDEN_DYNAMIC_MODULES
    assert imported_roots <= ALLOWED_HELPER_IMPORTS, (
        f"helper imports outside the allowlist: {sorted(imported_roots - ALLOWED_HELPER_IMPORTS)}"
    )


def test_case_matrix_helper_rejects_forbidden_direct_execution_apis():
    tree = ast.parse(HELPER.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_DYNAMIC_NAMES
        elif isinstance(node, ast.Call):
            assert not _is_forbidden_direct_call(node)
