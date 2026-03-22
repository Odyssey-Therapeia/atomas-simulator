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
    """
    Retrieve an integer command-line argument by position or return a default.
    
    Parameters:
        index (int): Position in sys.argv to read (0-based).
        default (int): Value to return if no argument exists at `index`.
    
    Returns:
        int: The integer parsed from sys.argv[index] if present, otherwise `default`.
    
    Raises:
        ValueError: If an argument exists at `index` but cannot be converted to an int.
    """
    if len(sys.argv) > index:
        return int(sys.argv[index])
    return default


def choose_random_legal_action(state: GameState, mask: list[bool]) -> int:
    """
    Selects a legal action index uniformly at random using the state's RNG.
    
    Parameters:
        state (GameState): Game state whose internal RNG is used for selection.
        mask (list[bool]): Boolean mask where True marks a legal action at that index.
    
    Returns:
        int: Index of a randomly chosen legal action.
    
    Raises:
        ValueError: If no entries in `mask` are True (no legal actions available).
    """
    legal_indices = [index for index, is_legal in enumerate(mask) if is_legal]
    if not legal_indices:
        raise ValueError("choose_random_legal_action: no legal actions available")
    return legal_indices[state._rng.randint(0, len(legal_indices) - 1)]


def play_one_game(seed_value: int) -> tuple[int, int]:
    """
    Play a single game initialized with the given RNG seed until it reaches a terminal state.
    
    Parameters:
        seed_value (int): Seed used to initialize the game's random number generator.
    
    Returns:
        tuple[int, int]: A pair (step_count, score) where `step_count` is the number of steps executed and `score` is the game's final score.
    
    Raises:
        RuntimeError: If the game does not reach a terminal state within MAX_STEPS_PER_GAME steps.
    """
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
    """
    Run a batch of games starting from a given seed and report aggregated metrics for the batch.
    
    Parameters:
        seed_start (int): Seed value used for the first game; subsequent games use incremented seeds.
        game_count (int): Number of games to play in this batch.
    
    Returns:
        tuple[int, int, int]: A tuple containing:
            - total_steps: sum of steps taken across all played games.
            - total_score: sum of final scores across all played games.
            - elapsed_ns: total wall-clock time in nanoseconds taken to run the batch.
    """
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
    """
    Compute the arithmetic mean of a list of numbers.
    
    Parameters:
        values (list[float]): Sequence of numeric values.
    
    Returns:
        float: The arithmetic mean of `values`, or 0.0 if `values` is empty.
    """
    return statistics.fmean(values) if values else 0.0


def median(values: list[float]) -> float:
    """
    Return the median of the provided numeric values.
    
    Returns:
        The median of `values`, or 0.0 if `values` is empty.
    """
    return statistics.median(values) if values else 0.0


def stddev(values: list[float]) -> float:
    """
    Compute the population standard deviation of a sequence of numeric values.
    
    Parameters:
        values (list[float]): Sequence of numbers to measure.
    
    Returns:
        float: Population standard deviation of `values`; `0.0` if `values` is empty.
    """
    if not values:
        return 0.0
    return statistics.pstdev(values)


def main() -> None:
    """
    Run the throughput benchmark: perform warmup runs, execute measurement runs, compute statistics, and print a human-readable report and a JSON-like summary.
    
    Reads up to four positional CLI arguments (measurement games, seed start, repetitions, warmup games) with defaults; validates that measurement games and repetitions are positive and warmup games is non-negative. Executes warmup runs (timing ignored), then runs the configured measurement passes, collecting per-run metrics (steps/sec, elapsed ms, average steps per game, average game duration). Computes mean, median, min, max, and population standard deviation for steps/sec, the coefficient of variation, and prints a detailed report. Emits a final JSON-like object containing configuration and aggregated metrics. Prints a warning if the coefficient of variation exceeds 10%.
        
    Raises:
        ValueError: If `measurement_games <= 0`, `repetitions <= 0`, or `warmup_games < 0`.
    """
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
