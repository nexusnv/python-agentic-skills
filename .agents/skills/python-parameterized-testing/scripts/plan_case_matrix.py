"""Plan a bounded, boundary-priority case matrix without executing project code."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections.abc import Iterable
from itertools import product
from typing import Any

# Bound candidate pools before de-duplication or Cartesian expansion.
MAX_VALUES_PER_DIMENSION = 10_000
MAX_DIMENSIONS = 128
# Hard ceilings for requested output and seeded-sample allocation.
MAX_CASES = 10_000
MAX_SAMPLE_SIZE = 10_000


class InputError(ValueError):
    """Raised when the planner receives malformed input."""


def _validate_json_value(value: Any) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise InputError(
                "values must not contain unpaired Unicode surrogate code points"
            ) from error
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InputError("values must contain only finite JSON numbers")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InputError("values must be JSON-compatible objects")
            _validate_json_value(item)
        return
    raise InputError("values must be JSON-compatible")


def _canonical_value(value: Any) -> str:
    """Return a stable comparison key for a validated JSON value."""
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise InputError("values must be JSON-compatible") from error


def _ordered_unique(values: Iterable[Any]) -> list[Any]:
    """Deduplicate JSON values while retaining their input order."""
    unique: list[Any] = []
    seen: set[str] = set()
    for value in values:
        _validate_json_value(value)
        key = _canonical_value(value)
        if key not in seen:
            seen.add(key)
            unique.append(value)
    return unique


def _validate_dimensions(payload: Any) -> dict[str, list[Any]]:
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        raise InputError("dimensions must be a non-empty object")
    if len(dimensions) > MAX_DIMENSIONS:
        raise InputError(f"dimensions must contain at most {MAX_DIMENSIONS} entries")
    for name in dimensions:
        if not isinstance(name, str):
            raise InputError("dimension names must be strings")
        _validate_json_value(name)

    validated: dict[str, list[Any]] = {}
    for name in sorted(dimensions):
        definition = dimensions[name]
        if not isinstance(definition, dict):
            raise InputError(f"dimension {name!r} must be an object")
        values = definition.get("values")
        if not isinstance(values, list) or not values:
            raise InputError(f"dimension {name!r} values must be a non-empty list")
        if len(values) > MAX_VALUES_PER_DIMENSION:
            raise InputError(
                f"dimension {name!r} values must contain at most {MAX_VALUES_PER_DIMENSION} entries"
            )
        boundary = definition.get("boundary", [])
        if not isinstance(boundary, list):
            raise InputError(f"dimension {name!r} boundary must be a list")
        if len(boundary) > MAX_VALUES_PER_DIMENSION:
            raise InputError(
                f"dimension {name!r} boundary must contain at most "
                f"{MAX_VALUES_PER_DIMENSION} entries"
            )
        validated[name] = _ordered_unique([*boundary, *values])
    return validated


def _validate_max_cases(payload: dict[str, Any]) -> int:
    if "max_cases" not in payload:
        raise InputError("max_cases is required")
    max_cases = payload["max_cases"]
    if isinstance(max_cases, bool) or not isinstance(max_cases, int) or max_cases <= 0:
        raise InputError("max_cases must be a positive integer")
    if max_cases > MAX_CASES:
        raise InputError(f"max_cases must not exceed {MAX_CASES}")
    return max_cases


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


def _product_size(dimensions: dict[str, list[Any]], max_cases: int) -> tuple[int, bool]:
    total = 1
    for values in dimensions.values():
        if total > max_cases // len(values):
            return max_cases + 1, True
        total *= len(values)
    return total, total > max_cases


def _plan_cartesian(
    dimensions: dict[str, list[Any]], max_cases: int
) -> tuple[list[dict[str, Any]], bool]:
    total, truncated = _product_size(dimensions, max_cases)
    names = list(dimensions)
    value_lists = [dimensions[name] for name in names]
    cases: list[dict[str, Any]] = []
    for combination in product(*value_lists):
        if len(cases) >= max_cases:
            truncated = True
            break
        cases.append(dict(zip(names, combination, strict=True)))
    if len(cases) < total:
        truncated = True
    return cases, truncated


def _plan_seeded(
    dimensions: dict[str, list[Any]], max_cases: int, seed: int, sample_size: int
) -> tuple[list[dict[str, Any]], bool]:
    names = list(dimensions)
    value_lists = [dimensions[name] for name in names]
    generator = random.Random(seed)
    sample_count = min(sample_size, max_cases)
    cases = [
        dict(zip(names, (generator.choice(values) for values in value_lists), strict=True))
        for _ in range(sample_count)
    ]
    return cases, sample_size > max_cases


def plan_case_matrix(payload: Any) -> dict[str, Any]:
    """Validate and plan a bounded Cartesian or seeded case matrix."""
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    seed, sample_size = _validate_sampling(payload)
    max_cases = _validate_max_cases(payload)
    dimensions = _validate_dimensions(payload)
    if seed is not None and sample_size is not None:
        cases, truncated = _plan_seeded(dimensions, max_cases, seed, sample_size)
        strategy = "seeded-sample"
    else:
        cases, truncated = _plan_cartesian(dimensions, max_cases)
        strategy = "boundary-priority-cartesian"
    return {
        "cases": cases,
        "truncated": truncated,
        "seed": seed,
        "strategy": strategy,
    }


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Plan a bounded boundary-priority case matrix from JSON on stdin."
    )


def _reject_non_finite_json(_: str) -> None:
    raise InputError("JSON input must not contain NaN or Infinity")


def main() -> int:
    """Read stdin, emit stable JSON, and return a process status."""
    _parser().parse_args()
    try:
        payload = json.load(sys.stdin, parse_constant=_reject_non_finite_json)
        result = plan_case_matrix(payload)
        output = json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (InputError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
