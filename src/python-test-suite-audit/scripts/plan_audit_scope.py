"""Plan a bounded, deterministic audit scope without executing project code."""

from __future__ import annotations

import argparse
import json
import random
import sys
from typing import Any

MAX_PATHS = 2_000
MAX_FILES = 1_000
MAX_SAMPLE_SIZE = 1_000

_ALLOWED_TOP_LEVEL_FIELDS = frozenset({"paths", "max_files", "seed", "sample_size"})


class InputError(ValueError):
    """Raised when the planner receives malformed input."""


def _validate_paths(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    unknown = sorted(set(payload) - _ALLOWED_TOP_LEVEL_FIELDS)
    if unknown:
        raise InputError(f"unknown top-level field: {unknown[0]!r}")
    paths = payload.get("paths")
    if not isinstance(paths, list) or not paths:
        raise InputError("paths must be a non-empty list")
    if len(paths) > MAX_PATHS:
        raise InputError(f"paths must contain at most {MAX_PATHS} entries")
    validated: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not isinstance(path, str) or not path.strip():
            raise InputError("each path must be a non-empty string")
        if path not in seen:
            seen.add(path)
            validated.append(path)
    return sorted(validated)


def _validate_max_files(payload: dict[str, Any]) -> int:
    if "max_files" not in payload:
        raise InputError("max_files is required")
    max_files = payload["max_files"]
    if isinstance(max_files, bool) or not isinstance(max_files, int) or max_files <= 0:
        raise InputError("max_files must be a positive integer")
    if max_files > MAX_FILES:
        raise InputError(f"max_files must not exceed {MAX_FILES}")
    return max_files


def _validate_sampling(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    has_seed = "seed" in payload
    has_sample_size = "sample_size" in payload
    if has_seed != has_sample_size:
        raise InputError("seed and sample_size must be provided together")
    if not has_seed:
        return None, None
    seed = payload["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise InputError("seed must be an integer")
    sample_size = payload["sample_size"]
    if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size <= 0:
        raise InputError("sample_size must be a positive integer")
    if sample_size > MAX_SAMPLE_SIZE:
        raise InputError(f"sample_size must not exceed {MAX_SAMPLE_SIZE}")
    return seed, sample_size


def plan_audit_scope(payload: Any) -> dict[str, Any]:
    """Validate and plan a bounded deterministic file sample."""
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    seed, sample_size = _validate_sampling(payload)
    max_files = _validate_max_files(payload)
    paths = _validate_paths(payload)
    if seed is not None and sample_size is not None:
        generator = random.Random(seed)
        sample_count = min(sample_size, max_files, len(paths))
        selected = generator.sample(paths, sample_count) if sample_count else []
        selected = sorted(selected)
        truncated = sample_size > max_files or len(paths) > sample_size
        strategy = "seeded-sample"
    else:
        selected = paths[:max_files]
        truncated = len(paths) > max_files
        strategy = "sorted-priority"
    return {
        "files": selected,
        "truncated": truncated,
        "seed": seed,
        "strategy": strategy,
    }


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Plan a bounded deterministic audit scope from JSON on stdin."
    )


def _reject_non_finite_json(_: str) -> None:
    raise InputError("JSON input must not contain NaN or Infinity")


def main() -> int:
    """Read stdin, emit stable JSON, and return a process status."""
    _parser().parse_args()
    try:
        payload = json.load(sys.stdin, parse_constant=_reject_non_finite_json)
        result = plan_audit_scope(payload)
        output = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (
        InputError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        TypeError,
        ValueError,
        OverflowError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
