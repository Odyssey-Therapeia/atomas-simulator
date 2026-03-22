"""Spawn entry points delegating to ``GameState`` (Mojo ``spawn.mojo`` port)."""

from __future__ import annotations

from .game_state import GameState


def spawn_piece(state: GameState) -> None:
    """
    Spawn a new piece on the provided game state.
    """
    state.spawn_piece()


def spawn_initial_board(state: GameState) -> None:
    """
    Spawn the initial board configuration on the provided GameState.
    
    Parameters:
        state (GameState): The GameState instance to modify by spawning the initial board.
    """
    state.spawn_initial_board()
