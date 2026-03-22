from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from web.bridge import NucleoGame


app = FastAPI(title="Nucleo API")
# This API currently keeps a single in-memory game instance for a single local
# player session. Concurrent clients will share state until session management
# is added.
game = NucleoGame()
STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class StepRequest(BaseModel):
    action: int


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/reset")
def reset_game() -> dict[str, object]:
    return game.reset()


@app.post("/api/step")
def step_game(request: StepRequest) -> dict[str, object]:
    if request.action < 0:
        raise HTTPException(status_code=400, detail="action must be non-negative")

    legal_actions = game.legal_actions()
    if request.action >= len(legal_actions):
        raise HTTPException(
            status_code=400,
            detail=f"action {request.action} is out of range for the current state",
        )
    if not legal_actions[request.action]:
        raise HTTPException(
            status_code=400,
            detail=f"action {request.action} is illegal for the current state",
        )

    try:
        state, reward, done, info = game.step(request.action)
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {
        "state": state,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/api/state")
def get_state() -> dict[str, object]:
    return game.get_state()


@app.get("/api/legal-actions")
def get_legal_actions() -> dict[str, list[bool]]:
    return {"legal_actions": game.legal_actions()}
