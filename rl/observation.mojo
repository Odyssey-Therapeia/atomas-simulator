from nucleo.game_state import GameState


comptime OBSERVATION_SIZE: Int = 40
comptime TOKEN_SLOT_COUNT: Int = 36


def get_observation(state: GameState) raises -> InlineArray[Int8, OBSERVATION_SIZE]:
    if state.token_count > TOKEN_SLOT_COUNT:
        raise Error("token count exceeds RL observation capacity")

    var observation = InlineArray[Int8, OBSERVATION_SIZE](fill=0)

    for index in range(state.token_count):
        observation[index] = state.pieces[index]

    observation[TOKEN_SLOT_COUNT] = state.current_piece
    observation[TOKEN_SLOT_COUNT + 1] = Int8(1 if state.holding_piece else 0)
    observation[TOKEN_SLOT_COUNT + 2] = state.held_piece
    observation[TOKEN_SLOT_COUNT + 3] = Int8(
        1 if state.held_can_convert else 0
    )
    return observation


def get_canonical_observation(
    state: GameState,
) raises -> InlineArray[Int8, OBSERVATION_SIZE]:
    if state.token_count > TOKEN_SLOT_COUNT:
        raise Error("token count exceeds RL observation capacity")

    var observation = InlineArray[Int8, OBSERVATION_SIZE](fill=0)

    if state.token_count > 0:
        var start_idx = 0
        var found_highest = False
        for index in range(state.token_count):
            if state.pieces[index] == state.highest_atom:
                start_idx = index
                found_highest = True
                break

        if not found_highest:
            raise Error("highest atom missing from canonical observation")

        for offset in range(state.token_count):
            observation[offset] = state.pieces[
                (start_idx + offset) % state.token_count
            ]

    observation[TOKEN_SLOT_COUNT] = state.current_piece
    observation[TOKEN_SLOT_COUNT + 1] = Int8(1 if state.holding_piece else 0)
    observation[TOKEN_SLOT_COUNT + 2] = state.held_piece
    observation[TOKEN_SLOT_COUNT + 3] = Int8(
        1 if state.held_can_convert else 0
    )
    return observation
