from std.os import abort
from std.python import Python, PythonObject
from std.python.bindings import PythonModuleBuilder

from nucleo.actions import legal_actions, step
from nucleo.game_state import GameState


def pieces_to_python(pieces: List[Int8]) raises -> PythonObject:
    var py_pieces = Python.list()

    for token in pieces:
        py_pieces.append(Int(token))

    return py_pieces


def mask_to_python(mask: List[Bool]) raises -> PythonObject:
    var py_mask = Python.list()

    for item in mask:
        py_mask.append(item)

    return py_mask


def state_to_python(state: GameState) raises -> PythonObject:
    var payload = Python.dict()
    payload["pieces"] = pieces_to_python(state.pieces)
    payload["atom_count"] = state.atom_count
    payload["current_piece"] = Int(state.current_piece)
    payload["score"] = state.score
    payload["move_count"] = state.move_count
    payload["highest_atom"] = Int(state.highest_atom)
    payload["holding_piece"] = state.holding_piece
    payload["held_piece"] = Int(state.held_piece)
    payload["held_can_convert"] = state.held_can_convert
    payload["is_terminal"] = state.is_terminal
    payload["moves_since_plus"] = state.moves_since_plus
    payload["moves_since_minus"] = state.moves_since_minus
    payload["rng_seed"] = state.rng_seed
    return payload


struct PythonGame(Movable, Writable):
    var state: GameState

    def __init__(out self):
        self.state = GameState()

    def __init__(out self, game_seed: Int):
        self.state = GameState(game_seed)

    @staticmethod
    def py_init(args: PythonObject, kwargs: PythonObject) raises -> PythonGame:
        if len(args) == 1:
            return Self(Int(py=args[0]))

        return Self()

    @staticmethod
    def reset_py(
        self_ptr: UnsafePointer[Self, MutAnyOrigin]
    ) raises -> PythonObject:
        self_ptr[].state.reset()
        return state_to_python(self_ptr[].state)

    @staticmethod
    def step_py(
        self_ptr: UnsafePointer[Self, MutAnyOrigin], action: PythonObject
    ) raises -> PythonObject:
        var result = step(self_ptr[].state, Int(py=action))
        var payload = Python.dict()
        payload["state"] = state_to_python(self_ptr[].state)
        payload["reward"] = result[0]
        payload["done"] = result[1]
        return payload

    @staticmethod
    def legal_actions_py(
        self_ptr: UnsafePointer[Self, MutAnyOrigin]
    ) raises -> PythonObject:
        return mask_to_python(legal_actions(self_ptr[].state))

    @staticmethod
    def get_state_py(
        self_ptr: UnsafePointer[Self, MutAnyOrigin]
    ) raises -> PythonObject:
        return state_to_python(self_ptr[].state)


@export
def PyInit_python_module() -> PythonObject:
    try:
        var module_builder = PythonModuleBuilder("python_module")
        _ = (
            module_builder.add_type[PythonGame]("Game")
            .def_py_init[PythonGame.py_init]()
            .def_method[PythonGame.reset_py]("reset")
            .def_method[PythonGame.step_py]("step")
            .def_method[PythonGame.legal_actions_py]("legal_actions")
            .def_method[PythonGame.get_state_py]("get_state")
        )
        return module_builder.finalize()
    except error:
        abort(String("failed to create python_module module: ", error))
