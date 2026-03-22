"""Legal actions, placement flow, and step API (Mojo ``actions.mojo`` port)."""

from __future__ import annotations

from .constants import MAX_ATOMS
from .fusion import resolve_board_outcome
from .game_state import EMPTY, GameState, MINUS, NEUTRINO, PLUS
from .ring import insert_at, remove_at
from .spawn import spawn_piece


def gap_action_count(state: GameState) -> int:
    """
    Number of gap actions available for the current board.
    
    Parameters:
        state (GameState): Game state whose `pieces` determine available gap actions.
    
    Returns:
        int: `1` when `state.pieces` is empty, otherwise `len(state.pieces)`.
    """
    if len(state.pieces) == 0:
        return 1
    return len(state.pieces)


def update_terminal_state(state: GameState) -> None:
    """
    Set the state's terminal flag based on atom count, whether a piece is held, and the current piece index.
    
    When the number of atoms exceeds MAX_ATOMS the state becomes terminal. If the atom count is less than MAX_ATOMS the state is non-terminal. When the atom count equals MAX_ATOMS the state is non-terminal while a piece is being held; otherwise the state is terminal if and only if `state.current_piece > 0`.
    """
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


def legal_actions(state: GameState) -> list[bool]:
    """
    Produce a boolean mask indicating which actions are legal for the given game state.
    
    The mask length corresponds to the set of actionable indices for the current turn (typically gap_action_count(state), except when the current piece is MINUS or NEUTRINO, in which case the mask covers state.pieces). Entries are `True` for indices that may be acted on given terminal status, holding/convert state, token presence, and atom-count placement limits.
    
    Parameters:
        state (GameState): Current game state.
    
    Returns:
        list[bool]: Mask where `True` denotes a legal action at that index, `False` denotes an illegal action.
    """
    mask: list[bool] = []

    if state.is_terminal:
        for _ in range(gap_action_count(state)):
            mask.append(False)
        return mask

    if state.holding_piece:
        for _ in range(gap_action_count(state)):
            mask.append(True)

        if state.held_can_convert:
            mask.append(True)

        return mask

    if state.current_piece == MINUS or state.current_piece == NEUTRINO:
        for token in state.pieces:
            mask.append(token > 0)
        return mask

    can_place_regular = not (state.current_piece > 0 and state.atom_count >= MAX_ATOMS)
    action_is_legal = can_place_regular or state.current_piece <= 0

    for _ in range(gap_action_count(state)):
        mask.append(action_is_legal)

    return mask


def finish_placement_turn(state: GameState, action: int) -> int:
    """
    Finalize placing the current piece at the specified action and advance the game state.
    
    Mutates the provided GameState by applying the placement, resolving board effects (updating score), clearing any holding state, incrementing the move count, and then either marking the state terminal if atom limits are exceeded or spawning the next piece and updating terminal status.
    
    Parameters:
        state (GameState): The game state to modify.
        action (int): Index of the gap or slot where the current piece is placed.
    
    Returns:
        int: The secondary outcome value produced by resolving the board at the placement location.
    """
    insert_at(state, action, state.current_piece)

    outcome = resolve_board_outcome(state, action)
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


def apply_action(state: GameState, action: int) -> int:
    """
    Apply the given action to the game state and return the reward for any placement resolved.
    
    Negative actions raise ValueError. If the action is out of range or masked illegal, the call is a no-op and returns 0. When the action leads to a placement resolution, the returned integer is the merged atom value produced by that placement; holding/convert/absorb actions that do not resolve placement return 0.
    
    Returns:
        int: Reward value — the merged atom value for a resolved placement, or 0 otherwise.
    """
    if action < 0:
        raise ValueError("apply_action: action must be non-negative")

    mask = legal_actions(state)

    if action >= len(mask) or not mask[action]:
        return 0

    if state.holding_piece:
        convert_action = gap_action_count(state)
        if state.held_can_convert and action == convert_action:
            state.current_piece = PLUS
            state.holding_piece = False
            state.held_piece = EMPTY
            state.held_can_convert = False
            state.is_terminal = False
            return 0

        return finish_placement_turn(state, action)

    if state.current_piece == MINUS:
        absorbed = remove_at(state, action)
        state.current_piece = absorbed
        state.holding_piece = True
        state.held_piece = absorbed
        state.held_can_convert = True
        state.is_terminal = False
        return 0

    if state.current_piece == NEUTRINO:
        copied = state.pieces[action]
        state.current_piece = copied
        state.holding_piece = True
        state.held_piece = copied
        state.held_can_convert = False
        state.is_terminal = False
        return 0

    return finish_placement_turn(state, action)


def step(state: GameState, action: int) -> tuple[int, bool]:
    """
    Advance the game state by applying the given action and report the resulting reward and terminal status.
    
    Parameters:
        state (GameState): Current game state to be mutated by the action.
        action (int): Index of the action to apply.
    
    Returns:
        tuple[int, bool]: A pair where the first element is the integer reward from applying the action, and the second element is `True` if the state is terminal after the action, `False` otherwise.
    """
    reward = apply_action(state, action)
    return (reward, state.is_terminal)
