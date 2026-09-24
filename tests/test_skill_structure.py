from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
import yaml

ROOT = Path(__file__).parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
EXPECTED_SKILLS = {"python-blackbox-testing", "python-parameterized-testing"}
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


def skill_files() -> list[Path]:
    return sorted(SKILLS_ROOT.glob("*/SKILL.md"))


def parse_frontmatter(path: Path) -> dict[str, object]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path} must start with a YAML frontmatter fence")

    try:
        closing_fence = next(
            index for index, line in enumerate(lines[1:], start=1) if line == "---"
        )
    except StopIteration as error:
        raise AssertionError(f"{path} has no closing YAML frontmatter fence") from error

    frontmatter = yaml.safe_load("\n".join(lines[1:closing_fence]))
    assert isinstance(frontmatter, dict), f"{path} frontmatter must be a mapping"
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


def test_exactly_expected_skills_are_discovered():
    discovered = {skill.parent.name for skill in skill_files()}

    assert discovered == EXPECTED_SKILLS


def test_no_duplicate_root_skills_tree_exists():
    assert not (ROOT / "skills").exists()


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_frontmatter_is_portable_and_complete(skill):
    frontmatter = parse_frontmatter(skill)

    assert frontmatter["name"] == skill.parent.name
    assert isinstance(frontmatter["description"], str)
    assert frontmatter["description"].strip()
    assert frontmatter["description"].startswith("Use when")
    assert frontmatter["license"] == "MIT"
    assert frontmatter.get("compatibility")
    metadata = frontmatter.get("metadata")
    assert isinstance(metadata, dict)
    assert set(metadata) >= {"author", "version"}
    assert all(isinstance(key, str) and isinstance(value, str) for key, value in metadata.items())
    assert metadata["author"].strip()
    assert metadata["version"].strip()


@pytest.mark.parametrize("skill", skill_files(), ids=lambda path: path.parent.name)
def test_frontmatter_has_no_client_specific_keys(skill):
    frontmatter = parse_frontmatter(skill)
    metadata = frontmatter.get("metadata")

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
def test_skill_has_required_package_files(skill):
    skill_dir = skill.parent

    assert skill.is_file()
    assert any((skill_dir / "references").glob("*.md"))
    assert (skill_dir / "evals" / "cases.yaml").is_file()


def test_parameterized_skill_includes_case_matrix_planner():
    assert (
        SKILLS_ROOT / "python-parameterized-testing" / "scripts" / "plan_case_matrix.py"
    ).is_file()
