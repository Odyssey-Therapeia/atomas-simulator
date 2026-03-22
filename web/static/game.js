const canvas = document.getElementById("game-canvas");
const context = canvas.getContext("2d");
const resetButton = document.getElementById("reset-button");
const messageBox = document.getElementById("message-box");

const scoreValue = document.getElementById("score-value");
const movesValue = document.getElementById("moves-value");
const atomsValue = document.getElementById("atoms-value");
const highestValue = document.getElementById("highest-value");

const center = { x: canvas.width / 2, y: canvas.height / 2 };
const ringRadius = 240;
const atomRadius = 34;
const gapRadius = 12;

let gameState = null;
let legalActions = [];
let interactiveAtoms = [];
let interactiveGaps = [];
let centerAction = null;

const TOKEN_LABELS = {
  [-1]: "+",
  [-2]: "-",
  [-3]: "B+",
  [-4]: "N",
};

const TOKEN_COLORS = {
  [-1]: "#ef4444",
  [-2]: "#f59e0b",
  [-3]: "#111827",
  [-4]: "#e2e8f0",
};

function tokenLabel(value) {
  return TOKEN_LABELS[value] ?? String(value);
}

function tokenColor(value) {
  if (value in TOKEN_COLORS) {
    return TOKEN_COLORS[value];
  }

  const palette = ["#38bdf8", "#22c55e", "#a78bfa", "#f97316", "#facc15"];
  return palette[Math.abs(value) % palette.length];
}

function gapCount() {
  return gameState && gameState.pieces.length > 0 ? gameState.pieces.length : 1;
}

function isSelectMode() {
  return (
    gameState &&
    !gameState.holding_piece &&
    (gameState.current_piece === -2 || gameState.current_piece === -4)
  );
}

function convertActionIndex() {
  return gapCount();
}

function pointForRingIndex(index, total, radius = ringRadius) {
  const angle = -Math.PI / 2 + (index * (2 * Math.PI)) / total;
  return {
    x: center.x + Math.cos(angle) * radius,
    y: center.y + Math.sin(angle) * radius,
  };
}

function pointForGapIndex(index, total) {
  const angle = -Math.PI / 2 + ((index - 0.5) * (2 * Math.PI)) / total;
  return {
    x: center.x + Math.cos(angle) * ringRadius,
    y: center.y + Math.sin(angle) * ringRadius,
  };
}

function setMessage(text) {
  messageBox.textContent = text;
}

function updateStats() {
  scoreValue.textContent = String(gameState.score);
  movesValue.textContent = String(gameState.move_count);
  atomsValue.textContent = String(gameState.atom_count);
  highestValue.textContent = String(gameState.highest_atom);
}

function drawCircle(x, y, radius, fillStyle, strokeStyle = "#94a3b8") {
  context.beginPath();
  context.arc(x, y, radius, 0, Math.PI * 2);
  context.fillStyle = fillStyle;
  context.fill();
  context.lineWidth = 2;
  context.strokeStyle = strokeStyle;
  context.stroke();
}

function drawLabel(text, x, y, color = "#f8fafc", font = "600 18px Inter") {
  context.fillStyle = color;
  context.font = font;
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, x, y);
}

function renderBoard() {
  context.clearRect(0, 0, canvas.width, canvas.height);
  interactiveAtoms = [];
  interactiveGaps = [];
  centerAction = null;

  drawCircle(center.x, center.y, ringRadius + 58, "rgba(30, 41, 59, 0.28)", "rgba(148, 163, 184, 0.16)");

  if (!gameState) {
    return;
  }

  const pieces = gameState.pieces;
  const totalPieces = pieces.length;

  if (totalPieces > 0) {
    for (let index = 0; index < totalPieces; index += 1) {
      const point = pointForRingIndex(index, totalPieces);
      const value = pieces[index];
      drawCircle(point.x, point.y, atomRadius, tokenColor(value));
      drawLabel(tokenLabel(value), point.x, point.y, value === -3 ? "#f8fafc" : "#0f172a");
      interactiveAtoms.push({ x: point.x, y: point.y, radius: atomRadius, action: index });
    }
  }

  const totalGaps = gapCount();
  for (let index = 0; index < totalGaps; index += 1) {
    const isLegal = legalActions[index];
    const point = totalPieces === 0 ? center : pointForGapIndex(index, totalGaps);
    drawCircle(
      point.x,
      point.y,
      gapRadius,
      isLegal ? "rgba(125, 211, 252, 0.85)" : "rgba(51, 65, 85, 0.45)",
      "rgba(148, 163, 184, 0.2)"
    );
    interactiveGaps.push({ x: point.x, y: point.y, radius: gapRadius * 1.6, action: index, legal: Boolean(isLegal) });
  }

  drawCircle(center.x, center.y, 62, tokenColor(gameState.current_piece), "rgba(248, 250, 252, 0.35)");
  drawLabel(tokenLabel(gameState.current_piece), center.x, center.y, gameState.current_piece === -3 ? "#f8fafc" : "#0f172a", "700 24px Inter");

  if (gameState.holding_piece && gameState.held_can_convert && legalActions.length > gapCount()) {
    centerAction = convertActionIndex();
    context.beginPath();
    context.arc(center.x, center.y, 76, 0, Math.PI * 2);
    context.strokeStyle = "rgba(244, 114, 182, 0.85)";
    context.lineWidth = 3;
    context.stroke();
    drawLabel("tap to +", center.x, center.y + 84, "#f9a8d4", "600 14px Inter");
  }

  if (gameState.is_terminal) {
    context.fillStyle = "rgba(15, 23, 42, 0.72)";
    context.fillRect(0, 0, canvas.width, canvas.height);
    drawLabel("Game Over", center.x, center.y - 24, "#f8fafc", "700 40px Inter");
    drawLabel(`Score ${gameState.score}`, center.x, center.y + 24, "#cbd5e1", "600 20px Inter");
  }
}

async function fetchState() {
  try {
    const [stateResponse, legalResponse] = await Promise.all([
      fetch("/api/state"),
      fetch("/api/legal-actions"),
    ]);

    if (!stateResponse.ok || !legalResponse.ok) {
      throw new Error(
        `Failed to load state (${stateResponse.status}) or legal actions (${legalResponse.status})`
      );
    }

    const statePayload = await stateResponse.json();
    const legalPayload = await legalResponse.json();
    gameState = statePayload;
    legalActions = legalPayload.legal_actions;
    updateStats();
    renderBoard();
  } catch (error) {
    console.error("Failed to fetch game state", error);
    setMessage(`Failed to load current state: ${error.message}`);
    renderBoard();
  }
}

async function resetGame() {
  const response = await fetch("/api/reset", { method: "POST" });
  gameState = await response.json();
  const legalResponse = await fetch("/api/legal-actions");
  legalActions = (await legalResponse.json()).legal_actions;
  updateStats();
  setMessage("New game ready. Click a gap to place the current piece.");
  renderBoard();
}

async function playAction(action) {
  try {
    const response = await fetch("/api/step", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ action }),
    });

    const payload = await response.json();
    if (!response.ok) {
      const detail = payload?.detail ?? "request failed";
      throw new Error(detail);
    }

    gameState = payload.state;
    legalActions = payload.info.legal_actions;
    updateStats();

    if (gameState.is_terminal) {
      setMessage(`Game over. Final score: ${gameState.score}.`);
    } else if (gameState.holding_piece && gameState.held_can_convert) {
      setMessage("You are holding an absorbed atom. Click a gap to place it or click the center to convert it into a Plus.");
    } else if (isSelectMode()) {
      setMessage("Select an atom on the ring.");
    } else {
      setMessage(`Reward: ${payload.reward}. Choose the next action.`);
    }
  } catch (error) {
    console.error("Failed to apply action", error);
    setMessage(`Failed to apply action: ${error.message}`);
  } finally {
    renderBoard();
  }
}

function hitTest(actionTargets, x, y) {
  return actionTargets.find((target) => {
    const dx = target.x - x;
    const dy = target.y - y;
    return Math.sqrt(dx * dx + dy * dy) <= target.radius;
  });
}

canvas.addEventListener("click", async (event) => {
  if (!gameState || gameState.is_terminal) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (event.clientX - rect.left) * scaleX;
  const y = (event.clientY - rect.top) * scaleY;

  if (centerAction !== null) {
    const dx = center.x - x;
    const dy = center.y - y;
    if (Math.sqrt(dx * dx + dy * dy) <= 62) {
      await playAction(centerAction);
      return;
    }
  }

  if (isSelectMode()) {
    const atomTarget = hitTest(interactiveAtoms, x, y);
    if (atomTarget) {
      await playAction(atomTarget.action);
    }
    return;
  }

  const gapTarget = hitTest(interactiveGaps.filter((target) => target.legal), x, y);
  if (gapTarget) {
    await playAction(gapTarget.action);
  }
});

resetButton.addEventListener("click", () => {
  resetGame().catch((error) => {
    setMessage(`Failed to reset: ${error.message}`);
  });
});

resetGame().catch((error) => {
  setMessage(`Failed to load game: ${error.message}`);
});
