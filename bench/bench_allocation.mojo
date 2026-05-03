from nucleo.game_state import GameState, HYDROGEN, MAX_RING_CAPACITY
from nucleo.ring import (
    insert_at,
    recalculate_atom_count,
    recalculate_highest,
    remove_at,
)
from stats import max_value, mean, median, min_value, standard_deviation
from std.sys import argv
from std.time import perf_counter_ns


comptime DEFAULT_OPS: Int = 100_000
comptime DEFAULT_REPETITIONS: Int = 5
comptime DEFAULT_WARMUP_OPS: Int = 1_000


def parse_arg_or_default(
    args: Span[StaticString, ...], index: Int, default: Int
) raises -> Int:
    if index < len(args):
        return atol(args[index])

    return default


def seed_state() -> GameState:
    var game = GameState(game_seed=7)
    for index in range(MAX_RING_CAPACITY):
        game.pieces[index] = 0

    game.token_count = 12
    game.pieces[0] = 1
    game.pieces[1] = 2
    game.pieces[2] = 3
    game.pieces[3] = 4
    game.pieces[4] = 5
    game.pieces[5] = 6
    game.pieces[6] = 7
    game.pieces[7] = 8
    game.pieces[8] = 9
    game.pieces[9] = 10
    game.pieces[10] = 11
    game.pieces[11] = 12
    recalculate_atom_count(game)
    recalculate_highest(game)
    return game^


def timer_overhead_ns(ops: Int) -> UInt:
    var total_ns = UInt(0)

    for _ in range(ops):
        var start_ns = perf_counter_ns()
        total_ns += perf_counter_ns() - start_ns

    return total_ns


def run_cycle_benchmark(ops: Int) raises -> Tuple[UInt, UInt]:
    var game = seed_state()
    var insert_ns = UInt(0)
    var remove_ns = UInt(0)
    var baseline_length = game.token_count
    var baseline_atom_count = game.atom_count
    var baseline_highest_atom = game.highest_atom

    for _ in range(ops):
        var insert_position = game.token_count // 2

        var start_ns = perf_counter_ns()
        insert_at(game, insert_position, HYDROGEN)
        insert_ns += perf_counter_ns() - start_ns

        start_ns = perf_counter_ns()
        _ = remove_at(game, insert_position)
        remove_ns += perf_counter_ns() - start_ns
    if game.token_count != baseline_length:
        raise Error("run_cycle_benchmark: ring length drifted")
    if game.atom_count != baseline_atom_count:
        raise Error("run_cycle_benchmark: atom_count drifted")
    if game.highest_atom != baseline_highest_atom:
        raise Error("run_cycle_benchmark: highest_atom drifted")

    return (insert_ns, remove_ns)


def main() raises:
    var args = argv()
    var ops = parse_arg_or_default(args, 1, DEFAULT_OPS)
    var repetitions = parse_arg_or_default(args, 2, DEFAULT_REPETITIONS)
    var warmup_ops = parse_arg_or_default(args, 3, DEFAULT_WARMUP_OPS)

    if ops <= 0:
        raise Error("ops must be positive")
    if repetitions <= 0:
        raise Error("repetitions must be positive")
    if warmup_ops < 0:
        raise Error("warmup_ops must be non-negative")

    if warmup_ops > 0:
        _ = run_cycle_benchmark(warmup_ops)
    print("Warmup complete:", warmup_ops, "cycles")

    var timing_overhead = timer_overhead_ns(ops)
    var insert_ops_per_second_values: List[Float64] = []
    var remove_ops_per_second_values: List[Float64] = []

    for _ in range(repetitions):
        var result = run_cycle_benchmark(ops)
        var adjusted_insert_ns = result[0]
        var adjusted_remove_ns = result[1]

        if adjusted_insert_ns > timing_overhead:
            adjusted_insert_ns -= timing_overhead
        if adjusted_remove_ns > timing_overhead:
            adjusted_remove_ns -= timing_overhead

        var insert_ops_per_second = 0.0
        if adjusted_insert_ns > 0:
            insert_ops_per_second = Float64(ops) / (
                Float64(adjusted_insert_ns) / 1e9
            )

        var remove_ops_per_second = 0.0
        if adjusted_remove_ns > 0:
            remove_ops_per_second = Float64(ops) / (
                Float64(adjusted_remove_ns) / 1e9
            )

        insert_ops_per_second_values.append(insert_ops_per_second)
        remove_ops_per_second_values.append(remove_ops_per_second)
    var insert_mean = mean(insert_ops_per_second_values)
    var remove_mean = mean(remove_ops_per_second_values)
    var insert_cv = 0.0
    var remove_cv = 0.0
    var insert_stddev = standard_deviation(insert_ops_per_second_values)
    var remove_stddev = standard_deviation(remove_ops_per_second_values)

    if insert_mean > 0.0:
        insert_cv = (insert_stddev / insert_mean) * 100.0
    if remove_mean > 0.0:
        remove_cv = (remove_stddev / remove_mean) * 100.0

    print("=== Nucleo Benchmark (Ring Allocation) ===")
    print("Cycles per repetition:", ops)
    print("Warmup cycles:", warmup_ops)
    print("Repetitions:", repetitions)
    print("Timer overhead (ns):", timing_overhead)
    print("insert_at ops/sec mean:", insert_mean)
    print("insert_at ops/sec median:", median(insert_ops_per_second_values))
    print("insert_at ops/sec min:", min_value(insert_ops_per_second_values))
    print("insert_at ops/sec max:", max_value(insert_ops_per_second_values))
    print("insert_at ops/sec stddev:", insert_stddev)
    print("insert_at CV (%):", insert_cv)
    print("remove_at ops/sec mean:", remove_mean)
    print("remove_at ops/sec median:", median(remove_ops_per_second_values))
    print("remove_at ops/sec min:", min_value(remove_ops_per_second_values))
    print("remove_at ops/sec max:", max_value(remove_ops_per_second_values))
    print("remove_at ops/sec stddev:", remove_stddev)
    print("remove_at CV (%):", remove_cv)

    if insert_cv > 10.0 or remove_cv > 10.0:
        print(
            "WARNING: allocation benchmark coefficient of variation exceeds 10%"
        )

    print("{")
    print(String('  "benchmark":"allocation",'))
    print(String('  "engine":"mojo",'))
    print(String('  "cycles_per_repetition":', ops, ","))
    print(String('  "warmup_cycles":', warmup_ops, ","))
    print(String('  "repetitions":', repetitions, ","))
    print(String('  "timer_overhead_ns":', timing_overhead, ","))
    print(String('  "insert_ops_per_second_mean":', insert_mean, ","))
    print(
        String(
            '  "insert_ops_per_second_median":',
            median(insert_ops_per_second_values),
            ",",
        )
    )
    print(
        String(
            '  "insert_ops_per_second_min":',
            min_value(insert_ops_per_second_values),
            ",",
        )
    )
    print(
        String(
            '  "insert_ops_per_second_max":',
            max_value(insert_ops_per_second_values),
            ",",
        )
    )
    print(String('  "insert_ops_per_second_stddev":', insert_stddev, ","))
    print(String('  "insert_cv_percent":', insert_cv, ","))
    print(String('  "remove_ops_per_second_mean":', remove_mean, ","))
    print(
        String(
            '  "remove_ops_per_second_median":',
            median(remove_ops_per_second_values),
            ",",
        )
    )
    print(
        String(
            '  "remove_ops_per_second_min":',
            min_value(remove_ops_per_second_values),
            ",",
        )
    )
    print(
        String(
            '  "remove_ops_per_second_max":',
            max_value(remove_ops_per_second_values),
            ",",
        )
    )
    print(String('  "remove_ops_per_second_stddev":', remove_stddev, ","))
    print(String('  "remove_cv_percent":', remove_cv))
    print("}")
