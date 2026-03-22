from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import gymnasium as gym
import numpy as np

from web.bridge import NucleoGame


TOKEN_SLOT_COUNT = 60
OBSERVATION_SIZE = 64
MAX_ACTIONS = 65


try:
    from lzero.envs import BaseEnv, BaseEnvTimestep
except ImportError:
    class BaseEnv:  # type: ignore[no-redef]
        pass

    @dataclass
    class BaseEnvTimestep:  # type: ignore[no-redef]
        obs: dict[str, Any]
        reward: float
        done: bool
        info: dict[str, Any]


def encode_observation(state: dict[str, Any]) -> np.ndarray:
    observation = np.zeros(OBSERVATION_SIZE, dtype=np.int8)
    pieces = state["pieces"]

    if len(pieces) > TOKEN_SLOT_COUNT:
        raise ValueError("token count exceeds RL observation capacity")

    start_index = 0
    if pieces:
        highest_atom = state["highest_atom"]
        start_index = pieces.index(highest_atom)

    for offset, token in enumerate(pieces):
        observation[offset] = np.int8(
            pieces[(start_index + offset) % len(pieces)]
        )

    observation[TOKEN_SLOT_COUNT] = np.int8(state["current_piece"])
    observation[TOKEN_SLOT_COUNT + 1] = np.int8(
        1 if state["holding_piece"] else 0
    )
    observation[TOKEN_SLOT_COUNT + 2] = np.int8(state["held_piece"])
    observation[TOKEN_SLOT_COUNT + 3] = np.int8(
        1 if state["held_can_convert"] else 0
    )
    return observation


def encode_action_mask(mask: list[bool]) -> np.ndarray:
    if len(mask) > MAX_ACTIONS:
        raise ValueError("action mask exceeds RL action capacity")

    padded = np.zeros(MAX_ACTIONS, dtype=bool)
    padded[: len(mask)] = np.array(mask, dtype=bool)
    return padded


class NucleoLightZeroEnv(BaseEnv):
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self.game = NucleoGame(seed=seed)
        self.action_space = gym.spaces.Discrete(MAX_ACTIONS)
        self.observation_space = gym.spaces.Box(
            low=-4,
            high=127,
            shape=(OBSERVATION_SIZE,),
            dtype=np.int8,
        )

    def reset(self) -> dict[str, Any]:
        state = self.game.reset()
        return {
            "observation": encode_observation(state),
            "action_mask": encode_action_mask(self.game.legal_actions()),
            "to_play": -1,
        }

    def step(self, action: int) -> tuple[dict[str, Any], int, bool, dict[str, Any]] | BaseEnvTimestep:
        state, reward, done, info = self.game.step(int(action))
        observation = {
            "observation": encode_observation(state),
            "action_mask": encode_action_mask(self.game.legal_actions()),
            "to_play": -1,
        }
        info = {**info, "state": state}

        if BaseEnvTimestep.__module__ != __name__:
            return BaseEnvTimestep(observation, reward, done, info)

        return observation, reward, done, info
