"""Spawn entry points delegating to ``GameState`` (Mojo ``spawn.mojo`` port)."""

from __future__ import annotations

from .game_state import GameState


def spawn_piece(state: GameState) -> None:
    state.spawn_piece()


def spawn_initial_board(state: GameState) -> None:
    state.spawn_initial_board()
