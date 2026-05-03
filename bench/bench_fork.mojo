from nucleo.actions import MAX_ACTION_SLOTS, legal_actions, step
from nucleo.game_state import GameState
from std.sys import argv
from std.time import perf_counter_ns


comptime DEFAULT_COPY_COUNT: Int = 1_000_000
comptime DEFAULT_WARMUP_STEPS: Int = 10
comptime DEFAULT_SEED: Int = 42


def parse_arg_or_default(
    args: Span[StaticString, ...], index: Int, default: Int
) raises -> Int:
    if index < len(args):
        return atol(args[index])

    return default


def first_legal_action(
    mask: InlineArray[Bool, MAX_ACTION_SLOTS], valid_count: Int
) raises -> Int:
    for index in range(valid_count):
        if mask[index]:
            return index

    raise Error("first_legal_action: no legal actions available")


def prepare_state(warmup_steps: Int, seed_value: Int) raises -> GameState:
    var state = GameState(seed_value)
    var steps_taken = 0

    while not state.is_terminal and steps_taken < warmup_steps:
        var mask_result = legal_actions(state)
        var action = first_legal_action(mask_result[0], mask_result[1])
        _ = step(state, action)
        steps_taken += 1

    return state^


def main() raises:
    var args = argv()
    var copy_count = parse_arg_or_default(args, 1, DEFAULT_COPY_COUNT)
    var warmup_steps = parse_arg_or_default(args, 2, DEFAULT_WARMUP_STEPS)
    var seed_value = parse_arg_or_default(args, 3, DEFAULT_SEED)

    if copy_count <= 0:
        raise Error("copy_count must be positive")
    if warmup_steps < 0:
        raise Error("warmup_steps must be non-negative")

    var state = prepare_state(warmup_steps, seed_value)
    var sink_score = 0

    var start_ns = perf_counter_ns()
    for iteration in range(copy_count):
        var state_copy = state
        state_copy.move_count += iteration % 2
        sink_score += state_copy.move_count
    var elapsed_ns = perf_counter_ns() - start_ns

    var ns_per_copy = Float64(elapsed_ns) / Float64(copy_count)
    var copies_per_second = Float64(copy_count) / (Float64(elapsed_ns) / 1e9)

    print("=== Nucleo Benchmark (GameState Fork) ===")
    print("Copy count:", copy_count)
    print("Warmup steps:", warmup_steps)
    print("Seed:", seed_value)
    print("Prepared state token count:", state.token_count)
    print("Elapsed (ns):", elapsed_ns)
    print("Fork cost (ns):", ns_per_copy)
    print("Copies/second:", copies_per_second)

    if sink_score < 0:
        print("Blackhole score:", sink_score)

    print("{")
    print('  "benchmark": "fork",')
    print('  "engine": "mojo",')
    print('  "copy_count": ', copy_count, ",")
    print('  "warmup_steps": ', warmup_steps, ",")
    print('  "seed": ', seed_value, ",")
    print('  "prepared_state_token_count": ', state.token_count, ",")
    print('  "elapsed_ns": ', elapsed_ns, ",")
    print('  "fork_cost_ns": ', ns_per_copy, ",")
    print('  "copies_per_second": ', copies_per_second)
    print("}")
