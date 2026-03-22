"""Authoritative gameplay state, spawn logic, and reset (Mojo ``game_state.mojo`` port)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .constants import (
    BLACK_PLUS_SCORE_GATE,
    BLACK_PLUS_SPAWN_RATE,
    EMPTY,
    HYDROGEN,
    MINUS,
    MINUS_SPAWN_RATE,
    NEUTRINO,
    NEUTRINO_SCORE_GATE,
    NEUTRINO_SPAWN_RATE,
    PLUS,
    PLUS_SPAWN_RATE,
)


@dataclass
class GameState:
    """Circular merge game state; field names mirror the Mojo ``GameState`` struct."""

    rng_seed: int = -1
    pieces: list[int] = field(default_factory=list)
    atom_count: int = 0
    current_piece: int = EMPTY
    score: int = 0
    move_count: int = 0
    highest_atom: int = HYDROGEN
    holding_piece: bool = False
    held_piece: int = EMPTY
    held_can_convert: bool = False
    is_terminal: bool = False
    moves_since_plus: int = 0
    moves_since_minus: int = 0
    _rng: random.Random = field(default_factory=random.Random, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """
        Initialize the instance after dataclass construction by creating the internal RNG and resetting transient game state.
        
        This sets the private `_rng` to a new random.Random instance and then invokes `reset()` to clear transient fields, seed or recreate the RNG as appropriate, build the initial board, and select the first spawned piece.
        """
        object.__setattr__(self, "_rng", random.Random())
        self.reset()

    def reset(self) -> None:
        """
        Reset the game state to initial startup conditions.
        
        Clears transient gameplay fields (ring pieces, counters, score, move/hold/terminal flags), reseeds or recreates the internal RNG according to `rng_seed` (seeds when `rng_seed >= 0`, otherwise replaces the RNG), then builds the initial six-token board and selects the first spawn piece.
        """
        self.pieces = []
        self.atom_count = 0
        self.current_piece = EMPTY
        self.score = 0
        self.move_count = 0
        self.highest_atom = HYDROGEN
        self.holding_piece = False
        self.held_piece = EMPTY
        self.held_can_convert = False
        self.is_terminal = False
        self.moves_since_plus = 0
        self.moves_since_minus = 0

        if self.rng_seed >= 0:
            self._rng.seed(self.rng_seed)
        else:
            object.__setattr__(self, "_rng", random.Random())

        self.spawn_initial_board()
        self.spawn_piece()

    def regular_spawn_bounds(self) -> tuple[int, int]:
        """
        Compute inclusive lower and upper bounds for uniform regular-atom spawning based on the current highest atom.
        
        Returns:
            bounds (tuple[int, int]): A pair (minimum_regular, maximum_regular) giving the inclusive minimum and maximum regular atom values.
        """
        highest_value = int(self.highest_atom)
        minimum_regular = 1
        if highest_value > 4:
            minimum_regular = highest_value - 4

        maximum_regular = 1
        if highest_value > 1:
            maximum_regular = highest_value - 1

        return (minimum_regular, maximum_regular)

    def pick_straggler_spawn(self, minimum_regular: int) -> int:
        """
        Selects a low-value atom already present on the ring as a "pity" spawn; returns EMPTY if none qualify or the pity roll fails.
        
        Parameters:
            minimum_regular (int): Inclusive lower bound for regular spawn values; tokens with value less than this are considered stragglers.
        
        Returns:
            int: A randomly chosen straggler token value from the ring, or `EMPTY` if no stragglers exist, `atom_count` is zero or negative, or the pity roll does not succeed.
        """
        stragglers: list[int] = []
        for token in self.pieces:
            if token > 0 and int(token) < minimum_regular:
                stragglers.append(token)

        if len(stragglers) == 0 or self.atom_count <= 0:
            return EMPTY

        pity_threshold = 1.0 / float(self.atom_count)
        if self._rng.random() >= pity_threshold:
            return EMPTY

        straggler_idx = self._rng.randint(0, len(stragglers) - 1)
        return stragglers[straggler_idx]

    def update_spawn_counters(self, spawned_piece: int) -> None:
        """
        Update internal spawn timers after a piece is spawned.
        
        Resets `moves_since_plus` to 0 when `spawned_piece` equals `PLUS`, otherwise increments it;
        resets `moves_since_minus` to 0 when `spawned_piece` equals `MINUS`, otherwise increments it.
        
        Parameters:
            spawned_piece (int): The token value that was spawned (e.g., `PLUS`, `MINUS`) used to update the counters.
        """
        if spawned_piece == PLUS:
            self.moves_since_plus = 0
        else:
            self.moves_since_plus += 1

        if spawned_piece == MINUS:
            self.moves_since_minus = 0
        else:
            self.moves_since_minus += 1

    def spawn_piece(self) -> None:
        """
        Choose and assign the next piece to spawn, then update spawn counters.
        
        Selects `current_piece` by priority: force `PLUS` if five moves have passed since the last plus; force `HYDROGEN` when `highest_atom` is hydrogen or lower; otherwise perform a special-roll selection that can yield `PLUS`, `MINUS`, `BLACK_PLUS`, or `NEUTRINO` subject to spawn-rate thresholds and score gates. If the roll falls through, perform a regular spawn within bounds computed from `highest_atom`, with a "pity" mechanic that may reuse a lower-value token already on the ring. After selection, updates internal spawn counters to reflect the chosen piece.
        """
        if self.moves_since_plus >= 5:
            self.current_piece = PLUS
            self.update_spawn_counters(PLUS)
            return

        if self.highest_atom <= HYDROGEN:
            self.current_piece = HYDROGEN
            self.update_spawn_counters(HYDROGEN)
            return

        special_roll = self._rng.random()
        minus_threshold = PLUS_SPAWN_RATE + MINUS_SPAWN_RATE
        black_plus_threshold = minus_threshold + BLACK_PLUS_SPAWN_RATE
        neutrino_threshold = black_plus_threshold + NEUTRINO_SPAWN_RATE

        if special_roll < PLUS_SPAWN_RATE:
            self.current_piece = PLUS
        elif special_roll < minus_threshold:
            self.current_piece = MINUS
        elif special_roll < black_plus_threshold and self.score > BLACK_PLUS_SCORE_GATE:
            self.current_piece = BLACK_PLUS
        elif special_roll < neutrino_threshold and self.score > NEUTRINO_SCORE_GATE:
            self.current_piece = NEUTRINO
        else:
            bounds = self.regular_spawn_bounds()
            pity_piece = self.pick_straggler_spawn(bounds[0])

            if pity_piece > 0:
                self.current_piece = pity_piece
            else:
                self.current_piece = int(self._rng.randint(bounds[0], bounds[1]))

        self.update_spawn_counters(self.current_piece)

    def spawn_initial_board(self) -> None:
        """
        Create an initial six-token board by sampling each atom uniformly from 1 to 3 and update atom_count and highest_atom.
        
        After creation, atom_count is set to the number of pieces and highest_atom is set to the maximum token value present (at minimum HYDROGEN).
        """
        self.pieces = [int(self._rng.randint(1, 3)) for _ in range(6)]
        self.atom_count = len(self.pieces)
        self.highest_atom = HYDROGEN
        for token in self.pieces:
            if token > self.highest_atom:
                self.highest_atom = token
