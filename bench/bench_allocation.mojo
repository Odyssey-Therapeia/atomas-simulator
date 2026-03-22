from nucleo.game_state import GameState, HYDROGEN
from nucleo.ring import (
    insert_at,
    recalculate_atom_count,
    recalculate_highest,
    remove_at,
)
from std.math import sqrt
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


def mean(values: List[Float64]) -> Float64:
    if len(values) == 0:
        return 0.0

    var total = 0.0
    for value in values:
        total += value

    return total / Float64(len(values))


def min_value(values: List[Float64]) -> Float64:
    var current_min = values[0]
    for value in values:
        if value < current_min:
            current_min = value

    return current_min


def max_value(values: List[Float64]) -> Float64:
    var current_max = values[0]
    for value in values:
        if value > current_max:
            current_max = value

    return current_max


def sorted_copy(values: List[Float64]) -> List[Float64]:
    var copied = values.copy()

    for index in range(1, len(copied)):
        var current_value = copied[index]
        var position = index

        while position > 0 and copied[position - 1] > current_value:
            copied[position] = copied[position - 1]
            position -= 1

        copied[position] = current_value

    return copied^


def median(values: List[Float64]) -> Float64:
    var ordered = sorted_copy(values)
    var middle = len(ordered) // 2

    if len(ordered) % 2 == 1:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2.0


def standard_deviation(values: List[Float64]) -> Float64:
    if len(values) == 0:
        return 0.0

    var average = mean(values)
    var variance = 0.0

    for value in values:
        var delta = value - average
        variance += delta * delta

    variance /= Float64(len(values))
    return sqrt(variance)


def seed_state() -> GameState:
    var game = GameState(game_seed=7)
    game.pieces = [
        Int8(1),
        Int8(2),
        Int8(3),
        Int8(4),
        Int8(5),
        Int8(6),
        Int8(7),
        Int8(8),
        Int8(9),
        Int8(10),
        Int8(11),
        Int8(12),
    ]
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
    var baseline_length = len(game.pieces)
    var baseline_atom_count = game.atom_count
    var baseline_highest_atom = game.highest_atom

    for _ in range(ops):
        var insert_position = len(game.pieces) // 2

        var start_ns = perf_counter_ns()
        insert_at(game, insert_position, HYDROGEN)
        insert_ns += perf_counter_ns() - start_ns

        start_ns = perf_counter_ns()
        _ = remove_at(game, insert_position)
        remove_ns += perf_counter_ns() - start_ns
    if len(game.pieces) != baseline_length:
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

        var insert_ops_per_second = Float64(ops) / (
            Float64(adjusted_insert_ns) / 1e9
        )
        var remove_ops_per_second = Float64(ops) / (
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
    print('  "benchmark": "allocation",')
    print('  "engine": "mojo",')
    print('  "cycles_per_repetition": ', ops, ",")
    print('  "warmup_cycles": ', warmup_ops, ",")
    print('  "repetitions": ', repetitions, ",")
    print('  "timer_overhead_ns": ', timing_overhead, ",")
    print('  "insert_ops_per_second_mean": ', insert_mean, ",")
    print(
        '  "insert_ops_per_second_median": ',
        median(insert_ops_per_second_values),
        ",",
    )
    print(
        '  "insert_ops_per_second_min": ',
        min_value(insert_ops_per_second_values),
        ",",
    )
    print(
        '  "insert_ops_per_second_max": ',
        max_value(insert_ops_per_second_values),
        ",",
    )
    print('  "insert_ops_per_second_stddev": ', insert_stddev, ",")
    print('  "insert_cv_percent": ', insert_cv, ",")
    print('  "remove_ops_per_second_mean": ', remove_mean, ",")
    print(
        '  "remove_ops_per_second_median": ',
        median(remove_ops_per_second_values),
        ",",
    )
    print(
        '  "remove_ops_per_second_min": ',
        min_value(remove_ops_per_second_values),
        ",",
    )
    print(
        '  "remove_ops_per_second_max": ',
        max_value(remove_ops_per_second_values),
        ",",
    )
    print('  "remove_ops_per_second_stddev": ', remove_stddev, ",")
    print('  "remove_cv_percent": ', remove_cv)
    print("}")
