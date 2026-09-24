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
    r"(?<!!)\[[^\]]*\]\(\s*(?:<([^>\r\n]+)>|([^\s)]+))",
    re.IGNORECASE,
)
MARKDOWN_REFERENCE_DEFINITION = re.compile(
    r"^[ \t]{0,3}\[([^\]\r\n]+)\]:[ \t]*(?:\n[ \t]*)?"
    r"(?:<([^>\r\n]+)>|([^\s]+))"
    r"(?:[ \t]+(?:\((?:[^()\r\n]|\\.)*\)|"
    r"\"(?:[^\"\\\r\n]|\\.)*\"|'(?:[^'\\\r\n]|\\.)*'))?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
MARKDOWN_REFERENCE_USAGE = re.compile(
    r"(?<!!)\[([^\]\r\n]+)\](?:\[([^\]\r\n]*)\]|(?!\())",
    re.IGNORECASE,
)
ASSET_PATH = re.compile(
    r"(?<![\w.-])((?:references|scripts)/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:md|py))"
)
EXCLUDED_MARKDOWN_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".tox",
        ".nox",
        ".cache",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "superpowers",
    }
)
TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]*(.*))?$")
METADATA_FIELD = re.compile(r"^  ([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(.*)$")
YAML_INTEGER = re.compile(r"^[+-]?[0-9]+$")
YAML_DECIMAL = re.compile(
    r"^[+-]?(?:(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)$"
)
YAML_UNSUPPORTED_NUMBER = re.compile(
    r"^[+-]?(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|\.inf|\.nan)$",
    re.IGNORECASE,
)
YAML_TRUE_VALUES = frozenset({"true", "yes", "on"})
YAML_FALSE_VALUES = frozenset({"false", "no", "off"})
YAML_NULL_VALUES = frozenset({"null", "~"})


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


def _validate_yaml_characters(path: Path, text: str) -> None:
    for offset, character in enumerate(text):
        codepoint = ord(character)
        if (
            codepoint in {0x09, 0x0A, 0x0D}
            or 0x20 <= codepoint <= 0x7E
            or codepoint == 0x85
            or 0xA0 <= codepoint <= 0xD7FF
            or 0xE000 <= codepoint <= 0xFFFD
            or 0x10000 <= codepoint <= 0x10FFFF
        ):
            continue
        line_index = text.count("\n", 0, offset) + 1
        line_start = text.rfind("\n", 0, offset) + 1
        column_index = offset - line_start + 1
        raise _frontmatter_error(
            path,
            f"contains forbidden control character U+{codepoint:04X} "
            f"at line {line_index}, column {column_index}",
        )


def _parse_scalar(path: Path, key: str, raw_value: str) -> object:
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
    if YAML_UNSUPPORTED_NUMBER.fullmatch(value):
        raise _frontmatter_error(path, f"{key} uses an unsupported YAML number or special value")

    normalized_value = value.casefold()
    if normalized_value in YAML_TRUE_VALUES:
        return True
    if normalized_value in YAML_FALSE_VALUES:
        return False
    if normalized_value in YAML_NULL_VALUES:
        return None
    if YAML_INTEGER.fullmatch(value):
        return int(value, 10)
    if YAML_DECIMAL.fullmatch(value):
        return float(value)
    return value


def _parse_folded_scalar(path: Path, key: str, lines: list[str], index: int) -> tuple[str, int]:
    content_indent: int | None = None
    for candidate in lines[index:]:
        if not candidate.strip():
            continue
        candidate_indent = len(candidate) - len(candidate.lstrip(" "))
        if candidate_indent == 0:
            break
        content_indent = candidate_indent
        break

    if content_indent is None:
        raise _frontmatter_error(path, f"{key} folded scalar must contain an indented value")

    content_lines: list[str] = []
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            content_lines.append("")
            index += 1
            continue
        if "\t" in line:
            raise _frontmatter_error(path, f"{key} folded scalar uses a tab")
        indentation = len(line) - len(line.lstrip(" "))
        if indentation < content_indent:
            break
        if indentation > content_indent:
            raise _frontmatter_error(
                path,
                f"{key} folded scalar has an unsupported more-indented continuation line",
            )
        content_lines.append(line[content_indent:])
        index += 1

    rendered_lines: list[str] = []
    pending_newlines = 0
    for line in content_lines:
        if not line:
            pending_newlines += 1
            continue
        if not rendered_lines:
            rendered_lines.append("\n" * pending_newlines + line)
        else:
            separator = " " if pending_newlines == 0 else "\n" * pending_newlines
            rendered_lines.append(separator + line)
        pending_newlines = 0

    value = "".join(rendered_lines)
    if not value.strip():
        raise _frontmatter_error(path, f"{key} folded scalar must contain a value")
    return value, index


def _parse_metadata(path: Path, lines: list[str], index: int) -> tuple[dict[str, object], int]:
    metadata: dict[str, object] = {}
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


def repository_markdown_files(repository_root: Path = ROOT) -> list[Path]:
    return sorted(
        path
        for path in repository_root.rglob("*.md")
        if not any(
            part in EXCLUDED_MARKDOWN_DIRECTORIES
            for part in path.relative_to(repository_root).parts[:-1]
        )
    )


def parse_frontmatter(path: Path) -> dict[str, object]:
    """Parse the small, portable frontmatter subset used by these skills.

    This intentionally does not implement YAML. Skill frontmatter is limited to
    scalar fields, folded scalar blocks, and a flat string metadata map, so a
    malformed file gets a direct, actionable error instead of silently relying
    on a development-only YAML dependency.
    """
    text = path.read_text(encoding="utf-8")
    _validate_yaml_characters(path, text)
    lines = text.splitlines()
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
        if key in {"name", "description"} and not isinstance(value, str):
            raise _frontmatter_error(path, f"{key} must be a string")
        frontmatter[key] = value

    missing_fields = REQUIRED_FRONTMATTER_FIELDS - frontmatter.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise _frontmatter_error(path, f"is missing required fields: {missing}")

    if "compatibility" in frontmatter:
        compatibility = frontmatter["compatibility"]
        if not isinstance(compatibility, str) or not compatibility.strip():
            raise _frontmatter_error(path, "compatibility must be a non-empty string")

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


def _normalize_reference_label(label: str) -> str:
    return " ".join(label.split()).casefold()


def _reference_definitions(markdown: str) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for match in MARKDOWN_REFERENCE_DEFINITION.finditer(markdown):
        label = _normalize_reference_label(match.group(1))
        target = match.group(2) or match.group(3)
        definitions.setdefault(label, target.strip())
    return definitions


def _is_heading_label(markdown: str, start: int) -> bool:
    line_start = markdown.rfind("\n", 0, start) + 1
    return re.match(r"^[ \t]{0,3}#{1,6}(?:[ \t]+|$)", markdown[line_start:start]) is not None


def markdown_targets(markdown: str) -> Iterator[str]:
    for match in MARKDOWN_LINK.finditer(markdown):
        yield match.group(1) or match.group(2)

    definitions = _reference_definitions(markdown)
    for match in MARKDOWN_REFERENCE_USAGE.finditer(markdown):
        if _is_heading_label(markdown, match.start()):
            continue
        if markdown[match.end() :].lstrip().startswith(":"):
            continue

        link_text = match.group(1).strip()
        explicit_label = match.group(2)
        label = (
            link_text if explicit_label is None or not explicit_label.strip() else explicit_label
        )
        normalized_label = _normalize_reference_label(label)
        if explicit_label is None and normalized_label not in definitions:
            continue
        yield definitions.get(normalized_label, label)


def local_link_target(source: Path, target: str, repository_root: Path = ROOT) -> Path | None:
    stripped = target.strip()
    parsed = urlsplit(stripped)
    if parsed.scheme or parsed.netloc or stripped.startswith(("#", "//")):
        return None
    if not parsed.path:
        return None
    decoded_path = unquote(parsed.path)
    if decoded_path.startswith("/"):
        return (repository_root / decoded_path.lstrip("/")).resolve()
    return (source.parent / decoded_path).resolve()


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


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("yes", True),
        ("False", False),
        ("OFF", False),
        ("null", None),
        ("Null", None),
        ("NULL", None),
        ("~", None),
        ("1", 1),
        ("-2", -2),
        ("1.5", 1.5),
        (".5", 0.5),
    ],
)
def test_frontmatter_parser_recognizes_unquoted_plain_scalar_types(tmp_path, raw_value, expected):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when testing\nlicense: MIT\n"
        f"compatibility: {raw_value}\n---\n",
        encoding="utf-8",
    )

    parsed_value = _parse_scalar(skill, "compatibility", raw_value)

    assert type(parsed_value) is type(expected)
    assert parsed_value == expected


@pytest.mark.parametrize(
    "raw_value",
    ["0x10", "0o7", "0b1", ".inf", ".nan", "True", "NULL", "~"],
)
@pytest.mark.parametrize("field", ["compatibility", "metadata.version"])
def test_frontmatter_parser_rejects_unsupported_plain_metadata_scalars(tmp_path, field, raw_value):
    skill = tmp_path / "SKILL.md"
    if field == "compatibility":
        frontmatter = f"compatibility: {raw_value}\n"
    else:
        frontmatter = f"metadata:\n  version: {raw_value}\n"
    skill.write_text(
        f"---\nname: example\ndescription: Use when testing\nlicense: MIT\n{frontmatter}---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter"):
        parse_frontmatter(skill)


@pytest.mark.parametrize("scalar", ['"0x10"', '"True"', '"NULL"', '"~"'])
def test_frontmatter_parser_keeps_quoted_yaml_looking_scalars_as_strings(tmp_path, scalar):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when testing\nlicense: MIT\n"
        f"compatibility: {scalar}\n---\n",
        encoding="utf-8",
    )

    assert parse_frontmatter(skill)["compatibility"] == scalar[1:-1]


@pytest.mark.parametrize(
    "metadata",
    ["author: Nexus Envision Sdn Bhd", "version: 0.1.0", "release: v1.2.3"],
)
def test_frontmatter_parser_keeps_plain_version_and_author_strings(tmp_path, metadata):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when testing\nlicense: MIT\n"
        f"metadata:\n  {metadata}\n---\n",
        encoding="utf-8",
    )

    assert parse_frontmatter(skill)["metadata"] == dict(
        [tuple(item.split(": ", maxsplit=1)) for item in (metadata,)]
    )


@pytest.mark.parametrize("metadata_field", ["version: 1", "enabled: true", "empty: null"])
def test_frontmatter_parser_rejects_non_string_metadata_values(tmp_path, metadata_field):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when testing\nlicense: MIT\n"
        f"metadata:\n  {metadata_field}\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter:.*string map"):
        parse_frontmatter(skill)


def test_frontmatter_parser_uses_json_and_yaml_quoted_scalar_rules(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\n"
        "description: 'Use when: it''s requested'\n"
        'compatibility: "3.0"\n'
        "license: MIT\n---\n",
        encoding="utf-8",
    )

    parsed = parse_frontmatter(skill)

    assert parsed["description"] == "Use when: it's requested"
    assert parsed["compatibility"] == "3.0"


def test_frontmatter_parser_rejects_invalid_plain_scalar_syntax(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\ndescription: Use when: testing\nlicense: MIT\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter:.*invalid plain scalar syntax"):
        parse_frontmatter(skill)


@pytest.mark.parametrize("field", ["name", "description"])
def test_frontmatter_parser_rejects_non_text_name_and_description(tmp_path, field):
    values = {"name": "true", "description": "false"}
    fields = {
        "name": "example",
        "description": "Use when testing",
        "license": "MIT",
    }
    fields[field] = values[field]
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\n" + "".join(f"{key}: {value}\n" for key, value in fields.items()) + "---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match=rf"malformed frontmatter:.*{field} must be a string"):
        parse_frontmatter(skill)


@pytest.mark.parametrize("control_character", ["\x00", "\x01", "\x0b", "\x7f", "\x9f"])
def test_frontmatter_parser_rejects_yaml_forbidden_control_characters(tmp_path, control_character):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\n"
        f"description: Use when testing{control_character}\n"
        "license: MIT\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter:.*forbidden control character"):
        parse_frontmatter(skill)


def test_frontmatter_parser_folds_folded_scalar_lines_and_preserves_blank_line(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\n"
        "description: >-\n"
        "  first line\n"
        "  second line\n"
        "\n"
        "  third line\n"
        "license: MIT\n---\n",
        encoding="utf-8",
    )

    assert parse_frontmatter(skill)["description"] == "first line second line\nthird line"


def test_frontmatter_parser_rejects_more_indented_folded_scalar_lines(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "---\nname: example\n"
        "description: >-\n"
        "  first line\n"
        "    unsupported more-indented line\n"
        "license: MIT\n---\n",
        encoding="utf-8",
    )

    with pytest.raises(AssertionError, match="malformed frontmatter:.*more-indented"):
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


def test_repository_markdown_files_include_repository_contracts_and_skill_documents():
    files = {path.relative_to(ROOT).as_posix() for path in repository_markdown_files()}

    assert {
        "README.md",
        "AGENTS.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CHANGELOG.md",
    } <= files
    assert any(path.startswith("docs/") for path in files)
    assert ".agents/skills/python-blackbox-testing/SKILL.md" in files
    assert ".agents/skills/python-parameterized-testing/SKILL.md" in files


def test_repository_markdown_files_exclude_generated_and_cache_directories(tmp_path):
    retained = tmp_path / "docs" / "retained.md"
    retained.parent.mkdir()
    retained.write_text("retained\n", encoding="utf-8")
    for directory in (".git", ".venv", "__pycache__", "build", "node_modules"):
        path = tmp_path / directory / "generated.md"
        path.parent.mkdir()
        path.write_text("generated\n", encoding="utf-8")

    assert repository_markdown_files(tmp_path) == [retained]


def test_all_relative_markdown_links_resolve():
    missing_targets: list[str] = []
    markdown_files = repository_markdown_files()

    for source in markdown_files:
        for target in markdown_targets(source.read_text(encoding="utf-8")):
            resolved = local_link_target(source, target)
            if resolved is not None and not resolved.exists():
                missing_targets.append(f"{source.relative_to(ROOT)} -> {target}")

    assert not missing_targets, "missing local Markdown targets:\n" + "\n".join(missing_targets)


def test_root_relative_local_links_and_missing_docs_links_are_checked(tmp_path):
    (tmp_path / "docs").mkdir()
    source = tmp_path / "README.md"
    source.write_text(
        "[present](/docs/present.md)\n[missing](/docs/missing.md)\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "present.md").write_text("present\n", encoding="utf-8")

    targets = list(markdown_targets(source.read_text(encoding="utf-8")))
    resolved = [local_link_target(source, target, tmp_path) for target in targets]
    missing = [
        f"{target}"
        for target, path in zip(targets, resolved, strict=True)
        if path is not None and not path.exists()
    ]

    assert resolved[0] == tmp_path / "docs" / "present.md"
    assert missing == ["/docs/missing.md"]


def test_relative_markdown_links_do_not_fall_back_to_repository_root(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    source = docs / "source.md"
    source.write_text("[README](README.md)\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("root\n", encoding="utf-8")

    target = local_link_target(source, "README.md", tmp_path)

    assert target == docs / "README.md"
    assert not target.exists()


def test_root_relative_local_link_uses_repository_root():
    assert (
        local_link_target(ROOT / "docs" / "research" / "report.md", "/README.md")
        == ROOT / "README.md"
    )


def test_markdown_targets_keep_inline_and_angle_bracket_targets():
    markdown = "[normal](references/normal.md) [angled](<references/angled target.md>)"

    assert list(markdown_targets(markdown)) == [
        "references/normal.md",
        "references/angled target.md",
    ]


def test_markdown_targets_ignore_images_and_heading_labels():
    markdown = "![diagram](references/missing-image.png)\n# [Heading label]\n"

    assert list(markdown_targets(markdown)) == []


def test_markdown_targets_support_full_collapsed_and_shortcut_references():
    markdown = """
[full text][MiXeD   LaBeL]
[collapsed text][]
[shortcut text]

[  mixed   label  ]: references/full.md
[collapsed text]:
  references/collapsed.md
[shortcut text]: references/shortcut.md
"""

    assert list(markdown_targets(markdown)) == [
        "references/full.md",
        "references/collapsed.md",
        "references/shortcut.md",
    ]


@pytest.mark.parametrize(
    "definition",
    [
        "[label]: references/actual.md (references/label.md)",
        "[label]: <references/actual.md> (references/label.md)",
        "[label]: references/actual.md 'references/label.md'",
        '[label]: references/actual.md "references/label.md"',
    ],
)
def test_markdown_reference_titles_ignore_decoy_paths(tmp_path, definition):
    references = tmp_path / "references"
    references.mkdir()
    (references / "label.md").write_text("decoy\n", encoding="utf-8")
    markdown = f"[label]\n\n{definition}\n"

    targets = list(markdown_targets(markdown))

    assert targets == ["references/actual.md"]
    assert local_link_target(tmp_path / "source.md", targets[0]) == references / "actual.md"
    assert not (references / "actual.md").exists()


def test_markdown_targets_report_missing_full_and_collapsed_references():
    markdown = "[missing full][absent-label]\n[missing collapsed][]\n[ordinary bracket text]\n"

    assert list(markdown_targets(markdown)) == ["absent-label", "missing collapsed"]


def test_reference_style_markdown_links_resolve_case_insensitively_and_report_missing_targets(
    tmp_path,
):
    references = tmp_path / "references"
    references.mkdir()
    valid_target = references / "valid target.md"
    valid_target.write_text("valid\n", encoding="utf-8")
    titled_target = references / "titled-valid.md"
    titled_target.write_text("titled valid\n", encoding="utf-8")
    source = tmp_path / "source.md"
    source.write_text(
        "[valid][VaLiD]\n"
        "[titled valid][TITLED VALID]\n"
        "[missing][MISSING]\n"
        "[missing titled][MISSING TITLED]\n"
        "[external][external]\n"
        "[anchor][anchor]\n"
        "[mail][mail]\n"
        "\n"
        "[valid]: <references/valid target.md>\n"
        '[titled valid]: references/titled-valid.md "A titled reference"\n'
        "[missing titled]: <references/titled-missing.md> 'Another title'\n"
        "[external]: https://example.com/docs\n"
        "[anchor]: #section\n"
        "[mail]: mailto:team@example.com\n",
        encoding="utf-8",
    )

    missing_targets = []
    for target in markdown_targets(source.read_text(encoding="utf-8")):
        resolved = local_link_target(source, target)
        if resolved is not None and not resolved.exists():
            missing_targets.append(target)

    assert missing_targets == ["MISSING", "references/titled-missing.md"]


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
