from pathlib import Path
import sys

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from web.server import app


def first_legal_action(mask: list[bool]) -> int:
    for index, is_legal in enumerate(mask):
        if is_legal:
            return index
    raise AssertionError("expected at least one legal action")


def main() -> None:
    client = TestClient(app)

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert "Nucleo" in root_response.text

    reset_response = client.post("/api/reset")
    assert reset_response.status_code == 200
    reset_state = reset_response.json()
    assert len(reset_state["pieces"]) == 6
    assert reset_state["atom_count"] == 6

    legal_actions_response = client.get("/api/legal-actions")
    assert legal_actions_response.status_code == 200
    legal_actions = legal_actions_response.json()["legal_actions"]
    action = first_legal_action(legal_actions)

    step_response = client.post("/api/step", json={"action": action})
    assert step_response.status_code == 200
    step_payload = step_response.json()
    assert "state" in step_payload
    assert "reward" in step_payload
    assert "done" in step_payload

    state_response = client.get("/api/state")
    assert state_response.status_code == 200
    current_state = state_response.json()
    assert "pieces" in current_state
    assert "current_piece" in current_state


if __name__ == "__main__":
    main()
