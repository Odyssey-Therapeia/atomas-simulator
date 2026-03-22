from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import gymnasium as gym
import numpy as np
import numpy.typing as npt

from web.bridge import NucleoGame


TOKEN_SLOT_COUNT = 36
OBSERVATION_SIZE = 40
MAX_ACTIONS = 37

Int8Array: TypeAlias = npt.NDArray[np.int8]
BoolArray: TypeAlias = npt.NDArray[np.bool_]
StateValue: TypeAlias = list[int] | int | bool
StateDict: TypeAlias = dict[str, StateValue]
ObservationValue: TypeAlias = Int8Array | BoolArray | int
ObservationDict: TypeAlias = dict[str, ObservationValue]
InfoValue: TypeAlias = list[bool] | int | StateDict
InfoDict: TypeAlias = dict[str, InfoValue]


try:
    from lzero.envs import BaseEnv, BaseEnvTimestep

    HAS_LIGHTZERO = True
except ImportError:
    HAS_LIGHTZERO = False

    class BaseEnv:  # type: ignore[no-redef]
        pass

    @dataclass
    class BaseEnvTimestep:  # type: ignore[no-redef]
        obs: ObservationDict
        reward: float
        done: bool
        info: InfoDict


StepTuple: TypeAlias = tuple[ObservationDict, int, bool, InfoDict]
StepResult: TypeAlias = BaseEnvTimestep | StepTuple


def assert_rl_contract(observation: Int8Array, action_mask: BoolArray) -> None:
    """Assert the fixed LightZero observation and action-mask contract."""
    assert observation.ndim == 1, (
        f"expected observation ndim=1, got {observation.ndim}"
    )
    assert observation.shape == (OBSERVATION_SIZE,), (
        f"expected observation shape {(OBSERVATION_SIZE,)}, got {observation.shape}"
    )
    assert observation.dtype == np.int8, (
        f"expected observation dtype {np.int8}, got {observation.dtype}"
    )
    assert action_mask.ndim == 1, (
        f"expected action mask ndim=1, got {action_mask.ndim}"
    )
    assert action_mask.shape == (MAX_ACTIONS,), (
        f"expected action mask shape {(MAX_ACTIONS,)}, got {action_mask.shape}"
    )
    assert action_mask.dtype == np.bool_, (
        f"expected action mask dtype {np.bool_}, got {action_mask.dtype}"
    )


def encode_observation(state: StateDict) -> Int8Array:
    """Encode engine state into the fixed-size LightZero observation tensor.

    Args:
        state: Normalized game state returned by the web bridge.

    Returns:
        A `np.ndarray` of shape `(OBSERVATION_SIZE,)` with token slots followed
        by held-piece metadata.

    Raises:
        ValueError: If the token count exceeds the observation capacity or the
            reported highest atom is not present in the piece list.
    """
    observation = np.zeros(OBSERVATION_SIZE, dtype=np.int8)
    pieces = state["pieces"]

    if len(pieces) > TOKEN_SLOT_COUNT:
        raise ValueError("token count exceeds RL observation capacity")

    start_index = 0
    if pieces:
        highest_atom = state["highest_atom"]
        if highest_atom not in pieces:
            raise ValueError(
                "highest_atom is missing from pieces while encoding observation: "
                f"highest_atom={highest_atom}, len(pieces)={len(pieces)}, state={state}"
            )
        start_index = pieces.index(highest_atom)

    for offset, _token in enumerate(pieces):
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


def encode_action_mask(mask: list[bool]) -> BoolArray:
    """Pad a dynamic legal-action mask to the LightZero action size.

    Args:
        mask: Dynamic legal-action mask produced by the engine.

    Returns:
        A boolean `np.ndarray` of shape `(MAX_ACTIONS,)`.

    Raises:
        ValueError: If the mask exceeds the padded LightZero action capacity.
    """
    if len(mask) > MAX_ACTIONS:
        raise ValueError(
            "action mask exceeds RL action capacity: "
            f"len(mask)={len(mask)}, MAX_ACTIONS={MAX_ACTIONS}"
        )

    padded = np.zeros(MAX_ACTIONS, dtype=bool)
    padded[: len(mask)] = np.array(mask, dtype=bool)
    return padded


class NucleoLightZeroEnv(BaseEnv):
    """LightZero-compatible wrapper around the Nucleo game engine."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the environment and its fixed observation/action spaces.

        Args:
            seed: Optional deterministic seed forwarded to the underlying game.
        """
        self.seed = seed
        self.game = NucleoGame(seed=seed)
        self.action_space = gym.spaces.Discrete(MAX_ACTIONS)
        self.observation_space = gym.spaces.Box(
            low=-4,
            high=127,
            shape=(OBSERVATION_SIZE,),
            dtype=np.int8,
        )

    def reset(self) -> ObservationDict:
        """Reset the environment and return the initial LightZero observation.

        Returns:
            A dict containing the encoded observation, padded action mask, and
            `to_play` marker expected by LightZero.
        """
        state = self.game.reset()
        observation = encode_observation(state)
        action_mask = encode_action_mask(self.game.legal_actions())
        assert_rl_contract(observation, action_mask)
        return {
            "observation": observation,
            "action_mask": action_mask,
            "to_play": -1,
        }

    def step(self, action: int) -> StepResult:
        """Apply one action and return the next LightZero timestep payload.

        Args:
            action: Padded action index to send to the underlying game engine.

        Returns:
            A `BaseEnvTimestep` when LightZero is installed; otherwise a raw
            `(observation, reward, done, info)` tuple for local smoke tests.

        Raises:
            ValueError: If observation or action-mask encoding detects invalid
                backend state.
        """
        state, reward, done, info = self.game.step(int(action))
        encoded_observation = encode_observation(state)
        action_mask = encode_action_mask(self.game.legal_actions())
        assert_rl_contract(encoded_observation, action_mask)
        observation: ObservationDict = {
            "observation": encoded_observation,
            "action_mask": action_mask,
            "to_play": -1,
        }
        info = {**info, "state": state}

        if HAS_LIGHTZERO:
            return BaseEnvTimestep(observation, reward, done, info)

        return observation, reward, done, info
