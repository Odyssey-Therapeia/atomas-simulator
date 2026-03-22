from nucleo.actions import legal_actions as engine_legal_actions, step as engine_step
from nucleo.game_state import GameState

from observation import OBSERVATION_SIZE, get_canonical_observation


comptime MAX_ACTIONS: Int = 65


struct NucleoEnv(Movable, Writable):
    var state: GameState

    def __init__(out self, game_seed: Int = -1):
        self.state = GameState(game_seed)

    def reset(mut self, game_seed: Int = -1) raises -> InlineArray[
        Int8, OBSERVATION_SIZE
    ]:
        if game_seed >= 0:
            self.state = GameState(game_seed)
        else:
            self.state.reset()

        return get_canonical_observation(self.state)

    def step(mut self, action: Int) raises -> Tuple[
        InlineArray[Int8, OBSERVATION_SIZE], Int, Bool, Int
    ]:
        if action < 0 or action >= MAX_ACTIONS:
            raise Error("action index out of bounds for RL action space")

        var result = engine_step(self.state, action)
        return (
            get_canonical_observation(self.state),
            result[0],
            result[1],
            self.state.score,
        )

    def legal_actions(self) raises -> InlineArray[Bool, MAX_ACTIONS]:
        var padded = InlineArray[Bool, MAX_ACTIONS](fill=False)
        var mask = engine_legal_actions(self.state)

        if len(mask) > MAX_ACTIONS:
            raise Error("action mask exceeds RL action capacity")

        for index in range(len(mask)):
            padded[index] = mask[index]

        return padded

    def observation_space(self) -> Tuple[Int, Int, Int]:
        return (OBSERVATION_SIZE, -4, 127)

    def action_space(self) -> Int:
        return MAX_ACTIONS
