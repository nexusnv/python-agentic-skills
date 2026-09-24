from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
EXPECTED_SKILLS = {"python-blackbox-testing", "python-parameterized-testing"}
EXPECTED_REFERENCE_FILES = {
    "python-blackbox-testing": frozenset(
        {
            "boundaries-and-oracles.md",
            "adapters-and-safety.md",
            "evidence-report.md",
        }
    ),
    "python-parameterized-testing": frozenset(
        {
            "domains-and-properties.md",
            "generation-and-replay.md",
            "evidence-report.md",
        }
    ),
}
TOP_LEVEL_FIELDS = frozenset({"name", "description", "license", "compatibility", "metadata"})
REQUIRED_FRONTMATTER_FIELDS = frozenset({"name", "description", "license"})
FOLDED_SCALAR_MARKER = ">-"
MAX_SKILL_LINES = 500
MAX_SKILL_WORDS = 5_000
MAX_SKILL_CHARACTERS = 20_000

MARKDOWN_LINK = re.compile(
    r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))",
    re.IGNORECASE,
)
ASSET_PATH = re.compile(
    r"(?<![\w.-])((?:references|scripts)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:md|py))"
)
TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
METADATA_FIELD = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$")


def _frontmatter_error(path: Path, detail: str) -> AssertionError:
    return AssertionError(f"{path}: malformed frontmatter: {detail}")


def _parse_quoted_scalar(path: Path, key: str, value: str) -> str:
    quote = value[0]
    if len(value) < 2 or value[-1] != quote:
        raise _frontmatter_error(path, f"{key} has an unterminated quoted scalar")

    if quote == '"':
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise _frontmatter_error(path, f"{key} has an invalid double-quoted scalar") from error
        if not isinstance(parsed, str):
            raise _frontmatter_error(path, f"{key} must be a string")
        return parsed

    body = value[1:-1]
    parsed: list[str] = []
    index = 0
    while index < len(body):
        character = body[index]
        if character == "'":
            if index + 1 < len(body) and body[index + 1] == "'":
                parsed.append("'")
                index += 2
                continue
            raise _frontmatter_error(path, f"{key} has an invalid single-quoted scalar")
        parsed.append(character)
        index += 1
    return "".join(parsed)


def _parse_scalar(path: Path, key: str, raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        raise _frontmatter_error(path, f"{key} must not be empty")
    if "\t" in raw_value:
        raise _frontmatter_error(path, f"{key} uses a tab")

    if value[0] in {"'", '"'}:
        return _parse_quoted_scalar(path, key, value)

    if value.startswith(("&", "*", "!", "[", "]", "{", "}", "|", ">", "%", "@", "`", "#")):
        raise _frontmatter_error(path, f"{key} uses an unsupported scalar form")
    if re.match(r"^(?:-|\?|:)(?:\s|$)", value) or value.startswith(","):
        raise _frontmatter_error(path, f"{key} has invalid plain scalar syntax")
    if re.search(r":(?:\s|$)", value):
        raise _frontmatter_error(path, f"{key} has invalid plain scalar syntax")
    if " #" in value:
        raise _frontmatter_error(path, f"{key} uses an unsupported inline comment")
    return value


def _parse_folded_scalar(path: Path, key: str, lines: list[str], index: int) -> tuple[str, int]:
    folded_lines: list[str] = []
    while index < len(lines):
        line = lines[index]
        if line and not line[0].isspace():
            break
        if line and "\t" in line:
            raise _frontmatter_error(path, f"{key} folded scalar uses a tab")
        folded_lines.append(line.strip())
        index += 1

    if not folded_lines or not any(folded_lines):
        raise _frontmatter_error(path, f"{key} folded scalar must contain a value")
    return " ".join(folded_lines), index


def _parse_metadata(path: Path, lines: list[str], index: int) -> tuple[dict[str, str], int]:
    metadata: dict[str, str] = {}
    while index < len(lines):
        line = lines[index]
        if not line.startswith("  "):
            break
        if not line.strip() or line.startswith("   ") or line.startswith("\t"):
            raise _frontmatter_error(path, "metadata must contain flat key/value entries")

        match = METADATA_FIELD.fullmatch(line)
        if match is None:
            raise _frontmatter_error(path, "metadata must contain indented key/value entries")
        key, raw_value = match.groups()
        if key in metadata:
            raise _frontmatter_error(path, f"metadata key {key!r} is duplicated")
        metadata[key] = _parse_scalar(path, f"metadata.{key}", raw_value)
        index += 1

    if not metadata:
        raise _frontmatter_error(path, "metadata must contain a non-empty string map")
    return metadata, index


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def parse_frontmatter(path: Path) -> dict[str, object]:
    """Parse the small, portable frontmatter subset used by these skills.

    This intentionally does not implement YAML. Skill frontmatter is limited to
    scalar fields, folded scalar blocks, and a flat string metadata map, so a
    malformed file gets a direct, actionable error instead of silently relying
    on a development-only YAML dependency.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise _frontmatter_error(path, "must start with a frontmatter fence")

    try:
        closing_fence = next(
            index for index, line in enumerate(lines[1:], start=1) if line == "---"
        )
    except StopIteration as error:
        raise _frontmatter_error(path, "has no closing frontmatter fence") from error

    frontmatter_lines = lines[1:closing_fence]
    if not frontmatter_lines:
        raise _frontmatter_error(path, "must contain fields")

    frontmatter: dict[str, object] = {}
    index = 0
    while index < len(frontmatter_lines):
        line = frontmatter_lines[index]
        if not line or line[0].isspace():
            raise _frontmatter_error(path, "contains an unindented or blank field line")

        match = TOP_LEVEL_FIELD.fullmatch(line)
        if match is None:
            raise _frontmatter_error(path, "contains an invalid top-level field")
        key, raw_value = match.groups()
        if key not in TOP_LEVEL_FIELDS:
            raise _frontmatter_error(path, f"unsupported top-level field {key!r}")
        if key in frontmatter:
            raise _frontmatter_error(path, f"top-level field {key!r} is duplicated")

        if key == "metadata":
            if raw_value:
                raise _frontmatter_error(path, "metadata must be a nested mapping")
            metadata, index = _parse_metadata(path, frontmatter_lines, index + 1)
            frontmatter[key] = metadata
            continue

        if raw_value == FOLDED_SCALAR_MARKER:
            value, index = _parse_folded_scalar(path, key, frontmatter_lines, index + 1)
        else:
            value = _parse_scalar(path, key, raw_value or "")
            index += 1
        frontmatter[key] = value

    missing_fields = REQUIRED_FRONTMATTER_FIELDS - frontmatter.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise _frontmatter_error(path, f"is missing required fields: {missing}")

    metadata = frontmatter.get("metadata")
    if metadata is not None and (
        not isinstance(metadata, dict)
        or not metadata
        or not all(
            isinstance(key, str) and isinstance(value, str) and value.strip()
            for key, value in metadata.items()
        )
    ):
        raise _frontmatter_error(path, "metadata must be a non-empty string map")
    return frontmatter


def markdown_targets(markdown: str) -> Iterator[str]:
    for match in MARKDOWN_LINK.finditer(markdown):
        yield match.group(1) or match.group(2)


def local_link_target(source: Path, target: str) -> Path | None:
    parsed = urlsplit(target.strip())
    if parsed.scheme or parsed.netloc or target.startswith(("#", "//", "/")):
        return None
    if not parsed.path:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def declared_asset_paths(skill: Path) -> set[str]:
    return set(ASSET_PATH.findall(skill.read_text(encoding="utf-8")))


def declared_reference_links(skill: Path) -> set[str]:
    links: set[str] = set()
    for target in markdown_targets(skill.read_text(encoding="utf-8")):
        parsed = urlsplit(target.strip())
        if parsed.scheme or parsed.netloc or target.startswith(("/", "//")):
            continue
        if parsed.path.startswith("references/"):
            links.add(unquote(parsed.path))
    return links


def test_exactly_expected_skills_are_discovered():
    discovered = {skill.parent.name for skill in skill_files()}

    assert discovered == EXPECTED_SKILLS


def test_no_duplicate_root_skills_tree_exists():
    assert not (ROOT / "skills").exists()


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (
            "---\nname: example\ndescription: [broken\nlicense: MIT\n"
            "compatibility: Python\nmetadata:\n  author: Example\n  version: 1\n---\n",
            "unsupported scalar form",
        ),
        ("---\nname: example\n", "closing frontmatter fence"),
    ],
)
def test_frontmatter_parser_rejects_malformed_frontmatter(tmp_path, body, message):
    skill = tmp_path / "SKILL.md"
    skill.write_text(body, encoding="utf-8")

    with pytest.raises(AssertionError, match=rf"malformed frontmatter:.*{message}"):
        parse_frontmatter(skill)


def test_frontmatter_parser_accepts_required_fields_without_optional_sections(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: 'Use when: testing is requested'\nlicense: MIT\n---\n",
        encoding="utf-8",
    )

    assert parse_frontmatter(skill) == {
        "name": "example",
        "description": "Use when: testing is requested",
        "license": "MIT",
    }


def test_frontmatter_parser_rejects_invalid_plain_scalar_syntax(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when: testing\nlicense: MIT\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter:.*invalid plain scalar syntax"):
        parse_frontmatter(skill)


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_frontmatter_is_portable_and_complete(skill):
    frontmatter = parse_frontmatter(skill)

    assert frontmatter["name"] == skill.parent.name
    assert isinstance(frontmatter["description"], str)
    assert frontmatter["description"].strip()
    assert "Use when" in frontmatter["description"]
    assert frontmatter["license"] == "MIT"
    if "compatibility" in frontmatter:
        assert (
            isinstance(frontmatter["compatibility"], str) and frontmatter["compatibility"].strip()
        )
    if "metadata" in frontmatter:
        metadata = frontmatter["metadata"]
        assert isinstance(metadata, dict)
        assert all(
            isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()
        )
        assert all(value.strip() for value in metadata.values())


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_frontmatter_has_no_client_specific_keys(skill):
    frontmatter = parse_frontmatter(skill)
    metadata = frontmatter.get("metadata", {})

    assert isinstance(metadata, dict)
    assert not {"disable-model-invocation", "paths"} & frontmatter.keys()
    assert not {"opencode", "claude", "cursor"} & metadata.keys()


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_stays_within_concise_size_budget(skill):
    text = skill.read_text(encoding="utf-8")
    line_count = len(text.splitlines())
    word_count = len(text.split())
    estimated_tokens = max(word_count, len(text) // 4)

    assert line_count < MAX_SKILL_LINES
    assert word_count < MAX_SKILL_WORDS
    assert len(text) < MAX_SKILL_CHARACTERS
    assert estimated_tokens < 5_000


def test_all_relative_markdown_links_resolve():
    missing_targets: list[str] = []
    markdown_files = sorted(SKILLS_ROOT.rglob("*.md"))

    for source in markdown_files:
        for target in markdown_targets(source.read_text(encoding="utf-8")):
            resolved = local_link_target(source, target)
            if resolved is not None and not resolved.exists():
                missing_targets.append(f"{source.relative_to(ROOT)} -> {target}")

    assert not missing_targets, "missing local Markdown targets:\n" + "\n".join(missing_targets)


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_declares_only_existing_local_assets(skill):
    assets = declared_asset_paths(skill)
    reference_assets = {asset for asset in assets if asset.startswith("references/")}

    assert reference_assets
    for asset in assets:
        assert (skill.parent / asset).is_file(), f"{skill} references missing asset {asset}"


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_has_exact_approved_reference_files(skill):
    skill_dir = skill.parent
    references_dir = skill_dir / "references"
    actual_references = {
        path.relative_to(references_dir).as_posix()
        for path in references_dir.rglob("*")
        if path.is_file()
    }

    assert actual_references == EXPECTED_REFERENCE_FILES[skill_dir.name]


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_skill_declares_each_reference_as_a_relative_markdown_link(skill):
    expected_links = {
        f"references/{reference}" for reference in EXPECTED_REFERENCE_FILES[skill.parent.name]
    }

    assert declared_reference_links(skill) == expected_links


@pytest.mark.parametrize("skill_name", sorted(EXPECTED_SKILLS))
def test_each_skill_has_one_eval_fixture(skill_name):
    assert (SKILLS_ROOT / skill_name / "evals" / "cases.yaml").is_file()


def test_parameterized_skill_includes_case_matrix_planner():
    assert (
        SKILLS_ROOT / "python-parameterized-testing" / "scripts" / "plan_case_matrix.py"
    ).is_file()
