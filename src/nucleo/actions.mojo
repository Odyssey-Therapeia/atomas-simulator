from nucleo.fusion import resolve_board_outcome
from nucleo.game_state import (
    EMPTY,
    GameState,
    MAX_ATOMS,
    MINUS,
    NEUTRINO,
    PLUS,
)
from nucleo.ring import insert_at, remove_at
from nucleo.spawn import spawn_piece


def gap_action_count(state: GameState) -> Int:
    if len(state.pieces) == 0:
        return 1

    return len(state.pieces)


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


def legal_actions(state: GameState) -> List[Bool]:
    var mask: List[Bool] = []

    if state.is_terminal:
        for _ in range(gap_action_count(state)):
            mask.append(False)
        return mask^

    if state.holding_piece:
        for _ in range(gap_action_count(state)):
            mask.append(True)

        if state.held_can_convert:
            mask.append(True)

        return mask^

    if state.current_piece == MINUS or state.current_piece == NEUTRINO:
        for token in state.pieces:
            mask.append(token > 0)
        return mask^

    var can_place_regular = not (
        state.current_piece > 0 and state.atom_count >= MAX_ATOMS
    )
    var action_is_legal = can_place_regular or state.current_piece <= 0

    for _ in range(gap_action_count(state)):
        mask.append(action_is_legal)

    return mask^


def finish_placement_turn(mut state: GameState, action: Int) -> Int:
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


def apply_action(mut state: GameState, action: Int) -> Int:
    var mask = legal_actions(state)

    if action < 0 or action >= len(mask) or not mask[action]:
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


def step(mut state: GameState, action: Int) -> Tuple[Int, Bool]:
    var reward = apply_action(state, action)
    return (reward, state.is_terminal)
