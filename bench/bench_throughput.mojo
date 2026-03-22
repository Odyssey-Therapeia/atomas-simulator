from invariants import assert_game_invariants

from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step
from nucleo.game_state import GameState
from stats import max_value, mean, median, min_value, standard_deviation
from std.random import random_si64
from std.sys import argv
from std.time import perf_counter_ns


comptime DEFAULT_WARMUP_GAMES: Int = 100
comptime DEFAULT_MEASUREMENT_GAMES: Int = 1_000
comptime DEFAULT_REPETITIONS: Int = 5
comptime DEFAULT_SEED: Int = 42
comptime MAX_STEPS_PER_GAME: Int = 5_000


def choose_random_legal_action(
    mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int
) raises -> Int:
    var legal_indices: List[Int] = []

    for index in range(valid_count):
        if mask[index]:
            legal_indices.append(index)

    if len(legal_indices) == 0:
        raise Error("choose_random_legal_action: no legal actions available")

    var choice = Int(random_si64(0, Int64(len(legal_indices) - 1)))
    return legal_indices[choice]


def parse_arg_or_default(
    args: Span[StaticString, ...], index: Int, default: Int
) raises -> Int:
    if index < len(args):
        return atol(args[index])

    return default


def play_one_game(seed_value: Int) raises -> Tuple[Int, Int]:
    var game = GameState(game_seed=seed_value)
    var step_count = 0
    var previous_score = 0

    assert_game_invariants(game, previous_score)

    while not game.is_terminal and step_count < MAX_STEPS_PER_GAME:
        var mask_result = legal_actions(game)
        var action = choose_random_legal_action(
            mask_result[0], mask_result[1]
        )
        _ = step(game, action)
        assert_game_invariants(game, previous_score)
        previous_score = game.score
        step_count += 1

    if not game.is_terminal:
        raise Error("play_one_game: exceeded turn limit")

    return (step_count, game.score)


def run_pass(seed_start: Int, game_count: Int) raises -> Tuple[Int, Int, UInt]:
    var total_steps = 0
    var total_score = 0
    var start_ns = perf_counter_ns()

    for game_index in range(game_count):
        var result = play_one_game(seed_start + game_index)
        total_steps += result[0]
        total_score += result[1]

    var elapsed_ns = perf_counter_ns() - start_ns
    return (total_steps, total_score, elapsed_ns)


def main() raises:
    var args = argv()
    var measurement_games = parse_arg_or_default(
        args, 1, DEFAULT_MEASUREMENT_GAMES
    )
    var seed_start = parse_arg_or_default(args, 2, DEFAULT_SEED)
    var repetitions = parse_arg_or_default(args, 3, DEFAULT_REPETITIONS)
    var warmup_games = parse_arg_or_default(args, 4, DEFAULT_WARMUP_GAMES)

    if measurement_games <= 0:
        raise Error("measurement_games must be positive")
    if repetitions <= 0:
        raise Error("repetitions must be positive")
    if warmup_games < 0:
        raise Error("warmup_games must be non-negative")

    for repetition in range(repetitions):
        _ = run_pass(
            seed_start + repetition * (warmup_games + measurement_games),
            warmup_games,
        )
    print("Warmup complete:", warmup_games, "games across", repetitions, "runs")

    var steps_per_second_values: List[Float64] = []
    var elapsed_ms_values: List[Float64] = []
    var avg_steps_per_game_values: List[Float64] = []
    var avg_game_duration_ms_values: List[Float64] = []
    var total_steps_across_runs = 0
    var total_score_across_runs = 0

    for repetition in range(repetitions):
        var run_seed = (
            seed_start
            + repetitions * warmup_games
            + repetition * measurement_games
        )
        var result = run_pass(run_seed, measurement_games)
        var elapsed_ns = result[2]
        var elapsed_ms = Float64(elapsed_ns) / 1e6
        var steps_per_second = Float64(result[0]) / (Float64(elapsed_ns) / 1e9)
        var avg_steps_per_game = Float64(result[0]) / Float64(measurement_games)
        var avg_game_duration_ms = elapsed_ms / Float64(measurement_games)

        steps_per_second_values.append(steps_per_second)
        elapsed_ms_values.append(elapsed_ms)
        avg_steps_per_game_values.append(avg_steps_per_game)
        avg_game_duration_ms_values.append(avg_game_duration_ms)
        total_steps_across_runs += result[0]
        total_score_across_runs += result[1]
    var steps_mean = mean(steps_per_second_values)
    var steps_stddev = standard_deviation(steps_per_second_values)
    var coefficient_of_variation = 0.0
    if steps_mean > 0.0:
        coefficient_of_variation = (steps_stddev / steps_mean) * 100.0

    print("=== Nucleo Benchmark (Mojo Throughput) ===")
    print("Measurement games/run:", measurement_games)
    print("Warmup games/run:", warmup_games)
    print("Repetitions:", repetitions)
    print("Seed start:", seed_start)
    print("Total steps across runs:", total_steps_across_runs)
    print("Total score across runs:", total_score_across_runs)
    print("Steps/sec mean:", steps_mean)
    print("Steps/sec median:", median(steps_per_second_values))
    print("Steps/sec min:", min_value(steps_per_second_values))
    print("Steps/sec max:", max_value(steps_per_second_values))
    print("Steps/sec stddev:", steps_stddev)
    print("CV (%):", coefficient_of_variation)
    print("Elapsed ms mean:", mean(elapsed_ms_values))
    print("Avg steps/game:", mean(avg_steps_per_game_values))
    print("Avg game duration (ms):", mean(avg_game_duration_ms_values))

    if coefficient_of_variation > 10.0:
        print("WARNING: benchmark coefficient of variation exceeds 10%")

    print("{")
    print('  "benchmark": "throughput",')
    print('  "engine": "mojo",')
    print('  "measurement_games_per_run": ', measurement_games, ",")
    print('  "warmup_games_per_run": ', warmup_games, ",")
    print('  "repetitions": ', repetitions, ",")
    print('  "seed_start": ', seed_start, ",")
    print('  "total_steps_across_runs": ', total_steps_across_runs, ",")
    print('  "total_score_across_runs": ', total_score_across_runs, ",")
    print('  "steps_per_second_mean": ', steps_mean, ",")
    print('  "steps_per_second_median": ', median(steps_per_second_values), ",")
    print('  "steps_per_second_min": ', min_value(steps_per_second_values), ",")
    print('  "steps_per_second_max": ', max_value(steps_per_second_values), ",")
    print('  "steps_per_second_stddev": ', steps_stddev, ",")
    print(
        '  "coefficient_of_variation_percent": ', coefficient_of_variation, ","
    )
    print('  "elapsed_ms_mean": ', mean(elapsed_ms_values), ",")
    print('  "avg_steps_per_game": ', mean(avg_steps_per_game_values), ",")
    print('  "avg_game_duration_ms": ', mean(avg_game_duration_ms_values))
    print("}")
