from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from web.bridge import NucleoGame


app = FastAPI(title="Nucleo API")
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
    state, reward, done, info = game.step(request.action)
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
