"""Plan a bounded, boundary-priority case matrix without executing project code."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from itertools import product
from typing import Any


class InputError(ValueError):
    """Raised when the planner receives malformed input."""


def _canonical_value(value: Any) -> str:
    """Return a stable comparison key for JSON-compatible values."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _ordered_unique(values: Iterable[Any]) -> list[Any]:
    """Deduplicate JSON values while retaining their input order."""
    unique: list[Any] = []
    seen: set[str] = set()
    for value in values:
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

    validated: dict[str, list[Any]] = {}
    for name, definition in dimensions.items():
        if not isinstance(definition, dict):
            raise InputError(f"dimension {name!r} must be an object")
        values = definition.get("values")
        if not isinstance(values, list) or not values:
            raise InputError(f"dimension {name!r} values must be a non-empty list")
        boundary = definition.get("boundary", [])
        if not isinstance(boundary, list):
            raise InputError(f"dimension {name!r} boundary must be a list")
        validated[name] = _ordered_unique([*boundary, *values])
    return validated


def _validate_max_cases(payload: dict[str, Any]) -> int:
    if "max_cases" not in payload:
        raise InputError("max_cases is required")
    max_cases = payload["max_cases"]
    if isinstance(max_cases, bool) or not isinstance(max_cases, int) or max_cases <= 0:
        raise InputError("max_cases must be a positive integer")
    return max_cases


def _validate_seed_options(payload: dict[str, Any]) -> None:
    unsupported = [name for name in ("seed", "sample_size") if name in payload]
    if unsupported:
        names = ", ".join(unsupported)
        raise InputError(f"{names} sampling is not supported; provide explicit values")


def _product_size(dimensions: dict[str, list[Any]], max_cases: int) -> tuple[int, bool]:
    total = 1
    for values in dimensions.values():
        if total > max_cases // len(values):
            return max_cases + 1, True
        total *= len(values)
    return total, total > max_cases


def _plan(dimensions: dict[str, list[Any]], max_cases: int) -> tuple[list[dict[str, Any]], bool]:
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


def plan_case_matrix(payload: Any) -> dict[str, Any]:
    """Validate and plan a bounded Cartesian product from a JSON-like object."""
    if not isinstance(payload, dict):
        raise InputError("top-level JSON value must be an object")
    _validate_seed_options(payload)
    dimensions = _validate_dimensions(payload)
    max_cases = _validate_max_cases(payload)
    cases, truncated = _plan(dimensions, max_cases)
    return {
        "cases": cases,
        "truncated": truncated,
        "seed": None,
        "strategy": "boundary-priority-cartesian",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan a bounded boundary-priority case matrix from JSON on stdin."
    )
    return parser


def main() -> int:
    """Read stdin, emit stable JSON, and return a process status."""
    _parser().parse_args()
    try:
        payload = json.load(sys.stdin)
        result = plan_case_matrix(payload)
    except (InputError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
