"""Generate deterministic random-number sequences for benchmark replay."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path


DEFAULT_SEED = 42
DEFAULT_FLOAT_COUNT = 50_000
DEFAULT_INT_COUNT = 50_000
DEFAULT_INT_MIN = 0
DEFAULT_INT_MAX = 1_000_000
DEFAULT_OUTPUT = Path("bench/sequences/game_100_seed42.json")


def parse_arg_or_default(index: int, default: int) -> int:
    if len(sys.argv) > index:
        try:
            return int(sys.argv[index])
        except ValueError as error:
            raise ValueError(
                f"Invalid integer for CLI arg at index {index}: '{sys.argv[index]}'"
            ) from error
    return default


def generate_sequence(
    seed_value: int,
    float_count: int,
    int_count: int,
    int_min: int,
    int_max: int,
) -> dict[str, object]:
    """Generate reproducible random floats/ints and return a metadata-rich payload dict."""
    rng = random.Random(seed_value)
    return {
        "seed": seed_value,
        "float_count": float_count,
        "int_count": int_count,
        "int_min": int_min,
        "int_max": int_max,
        "floats": [rng.random() for _ in range(float_count)],
        "ints": [rng.randint(int_min, int_max) for _ in range(int_count)],
    }


def main() -> None:
    seed_value = parse_arg_or_default(1, DEFAULT_SEED)
    float_count = parse_arg_or_default(2, DEFAULT_FLOAT_COUNT)
    int_count = parse_arg_or_default(3, DEFAULT_INT_COUNT)
    int_min = parse_arg_or_default(4, DEFAULT_INT_MIN)
    int_max = parse_arg_or_default(5, DEFAULT_INT_MAX)
    output_path = Path(sys.argv[6]) if len(sys.argv) > 6 else DEFAULT_OUTPUT

    if float_count <= 0:
        raise ValueError("float_count must be positive")
    if int_count <= 0:
        raise ValueError("int_count must be positive")
    if int_min > int_max:
        raise ValueError("int_min must be <= int_max")

    payload = generate_sequence(seed_value, float_count, int_count, int_min, int_max)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("=== Sequence Generation ===")
    print(f"Output: {output_path}")
    print(f"Seed: {seed_value}")
    print(f"Float count: {float_count}")
    print(f"Int count: {int_count}")
    print(f"Int range: [{int_min}, {int_max}]")
    print("{")
    print(f'  "output": "{output_path}",')
    print(f'  "seed": {seed_value},')
    print(f'  "float_count": {float_count},')
    print(f'  "int_count": {int_count},')
    print(f'  "int_min": {int_min},')
    print(f'  "int_max": {int_max}')
    print("}")


if __name__ == "__main__":
    main()
