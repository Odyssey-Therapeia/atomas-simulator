"""Authoritative gameplay state, spawn logic, and reset (Mojo ``game_state.mojo`` port)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .constants import (
    BLACK_PLUS,
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
    token_count: int = 0
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
        self.reset()

    def reset(self) -> None:
        """Clear transient fields, re-seed RNG, build opening board, spawn first hand piece."""
        self.pieces = []
        self.token_count = 0
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
            self._rng = random.Random()

        self.spawn_initial_board()
        self.spawn_piece()

    def regular_spawn_bounds(self) -> tuple[int, int]:
        """Inclusive bounds for uniform regular-atom spawn."""
        highest_value = int(self.highest_atom)
        minimum_regular = 1
        if highest_value > 4:
            minimum_regular = highest_value - 4

        maximum_regular = 1
        if highest_value > 1:
            maximum_regular = highest_value - 1

        return (minimum_regular, maximum_regular)

    def pick_straggler_spawn(self, minimum_regular: int) -> int:
        """Pity spawn of a low atom already on the ring; ``EMPTY`` if none or roll fails."""
        stragglers: list[int] = []
        for index in range(self.token_count):
            token = self.pieces[index]
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
        if spawned_piece == PLUS:
            self.moves_since_plus = 0
        else:
            self.moves_since_plus += 1

        if spawned_piece == MINUS:
            self.moves_since_minus = 0
        else:
            self.moves_since_minus += 1

    def spawn_piece(self) -> None:
        """Set ``current_piece`` from spawn tables and pity logic."""
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

    def randint(self, lower: int, upper: int) -> int:
        """Expose bounded integer sampling without leaking direct RNG access."""
        return self._rng.randint(lower, upper)

    def spawn_initial_board(self) -> None:
        """Six atoms in ``[1, 3]``; recompute ``atom_count`` and ``highest_atom``."""
        self.pieces = [int(self._rng.randint(1, 3)) for _ in range(6)]
        self.token_count = len(self.pieces)
        self.atom_count = self.token_count
        self.highest_atom = HYDROGEN
        for index in range(self.token_count):
            token = self.pieces[index]
            if token > self.highest_atom:
                self.highest_atom = token
