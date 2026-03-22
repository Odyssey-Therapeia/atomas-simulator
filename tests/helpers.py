def first_legal_action(mask: list[bool]) -> int:
    """Return the first legal action index from a boolean mask."""
    for index, is_legal in enumerate(mask):
        if is_legal:
            return index
    raise AssertionError("expected at least one legal action")
