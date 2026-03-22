from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers import first_legal_action
from rl.lightzero_env import MAX_ACTIONS, OBSERVATION_SIZE, NucleoLightZeroEnv


def main() -> None:
    env = NucleoLightZeroEnv(seed=101)

    reset_payload = env.reset()
    assert reset_payload["observation"].shape == (OBSERVATION_SIZE,)
    assert reset_payload["action_mask"].shape == (MAX_ACTIONS,)
    assert reset_payload["to_play"] == -1

    action = first_legal_action(reset_payload["action_mask"].tolist())
    next_payload, reward, done, info = env.step(action)

    assert next_payload["observation"].shape == (OBSERVATION_SIZE,)
    assert next_payload["action_mask"].shape == (MAX_ACTIONS,)
    assert isinstance(reward, int | float)
    assert isinstance(done, bool)
    assert "state" in info


if __name__ == "__main__":
    main()
