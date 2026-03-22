"""Pure-Python throughput benchmark for the Nucleo engine."""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path


BENCH_DIR = Path(__file__).resolve().parent
if str(BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(BENCH_DIR))

from python_engine import GameState, legal_actions, step  # noqa: E402


DEFAULT_WARMUP_GAMES = 100
DEFAULT_MEASUREMENT_GAMES = 1_000
DEFAULT_REPETITIONS = 5
DEFAULT_SEED = 42
MAX_STEPS_PER_GAME = 5_000


def parse_arg_or_default(index: int, default: int) -> int:
    if len(sys.argv) > index:
        return int(sys.argv[index])
    return default


def choose_random_legal_action(state: GameState, mask: list[bool]) -> int:
    legal_indices = [index for index, is_legal in enumerate(mask) if is_legal]
    if not legal_indices:
        raise ValueError("choose_random_legal_action: no legal actions available")
    return legal_indices[state._rng.randint(0, len(legal_indices) - 1)]


def play_one_game(seed_value: int) -> tuple[int, int]:
    game = GameState(rng_seed=seed_value)
    step_count = 0

    while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
        mask = legal_actions(game)
        action = choose_random_legal_action(game, mask)
        step(game, action)
        step_count += 1

    if not game.is_terminal:
        raise RuntimeError("play_one_game: exceeded turn limit")

    return step_count, game.score


def run_pass(seed_start: int, game_count: int) -> tuple[int, int, int]:
    total_steps = 0
    total_score = 0
    start_ns = time.perf_counter_ns()

    for game_index in range(game_count):
        step_count, score = play_one_game(seed_start + game_index)
        total_steps += step_count
        total_score += score

    elapsed_ns = time.perf_counter_ns() - start_ns
    return total_steps, total_score, elapsed_ns


def mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    return statistics.pstdev(values)


def main() -> None:
    measurement_games = parse_arg_or_default(1, DEFAULT_MEASUREMENT_GAMES)
    seed_start = parse_arg_or_default(2, DEFAULT_SEED)
    repetitions = parse_arg_or_default(3, DEFAULT_REPETITIONS)
    warmup_games = parse_arg_or_default(4, DEFAULT_WARMUP_GAMES)

    if measurement_games <= 0:
        raise ValueError("measurement_games must be positive")
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")
    if warmup_games < 0:
        raise ValueError("warmup_games must be non-negative")

    for repetition in range(repetitions):
        run_pass(seed_start + repetition * (warmup_games + measurement_games), warmup_games)
    print(f"Warmup complete: {warmup_games} games across {repetitions} runs")

    steps_per_second_values: list[float] = []
    elapsed_ms_values: list[float] = []
    avg_steps_per_game_values: list[float] = []
    avg_game_duration_ms_values: list[float] = []
    total_steps_across_runs = 0
    total_score_across_runs = 0

    for repetition in range(repetitions):
        run_seed = seed_start + repetitions * warmup_games + repetition * measurement_games
        total_steps, total_score, elapsed_ns = run_pass(run_seed, measurement_games)
        elapsed_ms = elapsed_ns / 1e6
        steps_per_second = total_steps / (elapsed_ns / 1e9)
        avg_steps_per_game = total_steps / measurement_games
        avg_game_duration_ms = elapsed_ms / measurement_games

        steps_per_second_values.append(steps_per_second)
        elapsed_ms_values.append(elapsed_ms)
        avg_steps_per_game_values.append(avg_steps_per_game)
        avg_game_duration_ms_values.append(avg_game_duration_ms)
        total_steps_across_runs += total_steps
        total_score_across_runs += total_score

    steps_mean = mean(steps_per_second_values)
    steps_stddev = stddev(steps_per_second_values)
    coefficient_of_variation = (steps_stddev / steps_mean) * 100.0 if steps_mean > 0 else 0.0

    print("=== Nucleo Benchmark (Python Throughput) ===")
    print(f"Measurement games/run: {measurement_games}")
    print(f"Warmup games/run: {warmup_games}")
    print(f"Repetitions: {repetitions}")
    print(f"Seed start: {seed_start}")
    print(f"Total steps across runs: {total_steps_across_runs}")
    print(f"Total score across runs: {total_score_across_runs}")
    print(f"Steps/sec mean: {steps_mean}")
    print(f"Steps/sec median: {median(steps_per_second_values)}")
    print(f"Steps/sec min: {min(steps_per_second_values)}")
    print(f"Steps/sec max: {max(steps_per_second_values)}")
    print(f"Steps/sec stddev: {steps_stddev}")
    print(f"CV (%): {coefficient_of_variation}")
    print(f"Elapsed ms mean: {mean(elapsed_ms_values)}")
    print(f"Avg steps/game: {mean(avg_steps_per_game_values)}")
    print(f"Avg game duration (ms): {mean(avg_game_duration_ms_values)}")

    if coefficient_of_variation > 10.0:
        print("WARNING: benchmark coefficient of variation exceeds 10%")

    print("{")
    print('  "benchmark": "throughput",')
    print('  "engine": "python",')
    print(f'  "measurement_games_per_run": {measurement_games},')
    print(f'  "warmup_games_per_run": {warmup_games},')
    print(f'  "repetitions": {repetitions},')
    print(f'  "seed_start": {seed_start},')
    print(f'  "total_steps_across_runs": {total_steps_across_runs},')
    print(f'  "total_score_across_runs": {total_score_across_runs},')
    print(f'  "steps_per_second_mean": {steps_mean},')
    print(f'  "steps_per_second_median": {median(steps_per_second_values)},')
    print(f'  "steps_per_second_min": {min(steps_per_second_values)},')
    print(f'  "steps_per_second_max": {max(steps_per_second_values)},')
    print(f'  "steps_per_second_stddev": {steps_stddev},')
    print(f'  "coefficient_of_variation_percent": {coefficient_of_variation},')
    print(f'  "elapsed_ms_mean": {mean(elapsed_ms_values)},')
    print(f'  "avg_steps_per_game": {mean(avg_steps_per_game_values)},')
    print(f'  "avg_game_duration_ms": {mean(avg_game_duration_ms_values)}')
    print("}")


if __name__ == "__main__":
    main()
