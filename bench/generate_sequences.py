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
    """
    Parse an integer command-line argument from sys.argv at the given index, or return the provided default if the argument is absent.
    
    Parameters:
        index (int): Position in sys.argv to read.
        default (int): Fallback value returned when no argument is present at `index`.
    
    Returns:
        int: The parsed integer from sys.argv[index], or `default` if the argument is missing.
    
    Raises:
        ValueError: If the argument is present but cannot be converted to an integer.
    """
    if len(sys.argv) > index:
        return int(sys.argv[index])
    return default


def generate_sequence(
    seed_value: int,
    float_count: int,
    int_count: int,
    int_min: int,
    int_max: int,
) -> dict[str, object]:
    """
    Generate a deterministic payload of random floats and integers using the provided seed.
    
    Parameters:
        seed_value (int): Seed used to initialize a local deterministic RNG.
        float_count (int): Number of uniform floats to generate.
        int_count (int): Number of integers to generate.
        int_min (int): Minimum integer value (inclusive).
        int_max (int): Maximum integer value (inclusive).
    
    Returns:
        payload (dict): Dictionary containing:
            - "seed": the provided seed_value
            - "float_count": the provided float_count
            - "int_count": the provided int_count
            - "int_min": the provided int_min
            - "int_max": the provided int_max
            - "floats": list of `float_count` floats in [0.0, 1.0)
            - "ints": list of `int_count` integers each in [int_min, int_max]
    """
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
    """
    Parse CLI arguments, generate deterministic random float and integer sequences, write the payload as pretty-printed JSON to an output file, and print a human-readable summary.
    
    The function reads command-line arguments (in order) for: seed (argv[1]), float_count (argv[2]), int_count (argv[3]), int_min (argv[4]), int_max (argv[5]), and an optional output path (argv[6]). It validates that float_count and int_count are greater than zero and that int_min <= int_max, generates a deterministic payload based on the seed, ensures the output directory exists, writes the JSON payload to the output path, and prints a summary block to stdout.
    
    Raises:
        ValueError: if float_count <= 0, if int_count <= 0, or if int_min > int_max.
    """
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
