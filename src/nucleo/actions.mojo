from nucleo.fusion import resolve_board_outcome
from nucleo.game_state import (
    EMPTY,
    GameState,
    MAX_ATOMS,
    MAX_RING_CAPACITY,
    MINUS,
    NEUTRINO,
    PLUS,
)
from nucleo.ring import insert_at, remove_at
from nucleo.spawn import spawn_piece

comptime MAX_ACTION_SLOTS: Int = MAX_RING_CAPACITY + 1


def gap_action_count(state: GameState) -> Int:
    if state.token_count == 0:
        return 1

    return state.token_count


def update_terminal_state(mut state: GameState):
    if state.atom_count > MAX_ATOMS:
        state.is_terminal = True
        return

    if state.atom_count < MAX_ATOMS:
        state.is_terminal = False
        return

    if state.holding_piece:
        state.is_terminal = False
        return

    state.is_terminal = state.current_piece > 0


def legal_actions(
    state: GameState,
) -> Tuple[InlineArray[Bool, MAX_ACTION_SLOTS], Int]:
    var mask = InlineArray[Bool, MAX_ACTION_SLOTS](fill=False)

    if state.is_terminal:
        var valid_count = gap_action_count(state)
        return (mask, valid_count)

    if state.holding_piece:
        var valid_count = gap_action_count(state)
        for index in range(valid_count):
            mask[index] = True

        if state.held_can_convert:
            mask[valid_count] = True
            valid_count += 1

        return (mask, valid_count)

    if state.current_piece == MINUS or state.current_piece == NEUTRINO:
        var valid_count = state.token_count
        for index in range(state.token_count):
            var token = state.pieces[index]
            mask[index] = token > 0
        return (mask, valid_count)

    var can_place_regular = not (
        state.current_piece > 0 and state.atom_count >= MAX_ATOMS
    )
    var action_is_legal = can_place_regular or state.current_piece <= 0

    var valid_count = gap_action_count(state)
    for index in range(valid_count):
        mask[index] = action_is_legal

    return (mask, valid_count)


def finish_placement_turn(mut state: GameState, action: Int) raises -> Int:
    insert_at(state, action, state.current_piece)

    var outcome = resolve_board_outcome(state, action)
    state.score += outcome[0]
    state.holding_piece = False
    state.held_piece = EMPTY
    state.held_can_convert = False
    state.move_count += 1

    if state.atom_count > MAX_ATOMS:
        state.is_terminal = True
        return outcome[1]

    spawn_piece(state)
    update_terminal_state(state)
    return outcome[1]


def apply_action(mut state: GameState, action: Int) raises -> Int:
    """Apply a legal action and return reward.

    Negative actions raise immediately because they indicate a caller bug.
    Invalid positive actions still return `0` so callers that already operate
    on a legal-action mask can safely treat them as a no-op.
    """
    debug_assert(
        action >= 0,
        "apply_action: action must be non-negative (got ",
        action,
        ")",
    )
    if action < 0:
        raise Error("apply_action: action must be non-negative")

    var mask_result = legal_actions(state)

    if action >= mask_result[1] or not mask_result[0][action]:
        return 0

    if state.holding_piece:
        var convert_action = gap_action_count(state)
        if state.held_can_convert and action == convert_action:
            state.current_piece = PLUS
            state.holding_piece = False
            state.held_piece = EMPTY
            state.held_can_convert = False
            state.is_terminal = False
            return 0

        return finish_placement_turn(state, action)

    if state.current_piece == MINUS:
        var absorbed = remove_at(state, action)
        state.current_piece = absorbed
        state.holding_piece = True
        state.held_piece = absorbed
        state.held_can_convert = True
        state.is_terminal = False
        return 0

    if state.current_piece == NEUTRINO:
        var copied = state.pieces[action]
        state.current_piece = copied
        state.holding_piece = True
        state.held_piece = copied
        state.held_can_convert = False
        state.is_terminal = False
        return 0

    return finish_placement_turn(state, action)


def step(mut state: GameState, action: Int) raises -> Tuple[Int, Bool]:
    var reward = apply_action(state, action)
    return (reward, state.is_terminal)
