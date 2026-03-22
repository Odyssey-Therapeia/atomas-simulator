from std.random import random_float64, random_si64, seed


comptime MAX_ATOMS: Int = 18

comptime EMPTY: Int8 = 0
comptime HYDROGEN: Int8 = 1
comptime PLUS: Int8 = -1
comptime MINUS: Int8 = -2
comptime BLACK_PLUS: Int8 = -3
comptime NEUTRINO: Int8 = -4

comptime PLUS_SPAWN_RATE: Float64 = 0.17
comptime MINUS_SPAWN_RATE: Float64 = 0.05
comptime BLACK_PLUS_SPAWN_RATE: Float64 = 0.0125
comptime NEUTRINO_SPAWN_RATE: Float64 = 0.0167

comptime BLACK_PLUS_SCORE_GATE: Int = 750
comptime NEUTRINO_SCORE_GATE: Int = 1500


struct GameState(Movable, Writable):
    var pieces: List[Int8]
    var atom_count: Int
    var current_piece: Int8
    var score: Int
    var move_count: Int
    var highest_atom: Int8
    var holding_piece: Bool
    var held_piece: Int8
    var held_can_convert: Bool
    var is_terminal: Bool
    var moves_since_plus: Int
    var moves_since_minus: Int
    var rng_seed: Int

    def __init__(out self, game_seed: Int = -1):
        self.pieces = []
        self.atom_count = 0
        self.current_piece = HYDROGEN
        self.score = 0
        self.move_count = 0
        self.highest_atom = HYDROGEN
        self.holding_piece = False
        self.held_piece = EMPTY
        self.held_can_convert = False
        self.is_terminal = False
        self.moves_since_plus = 0
        self.moves_since_minus = 0
        self.rng_seed = game_seed
        self.reset()

    def reset(mut self):
        self.pieces = []
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
            seed(a=self.rng_seed)
        else:
            seed()

        self.spawn_initial_board()
        self.spawn_piece()

    def regular_spawn_bounds(self) -> Tuple[Int, Int]:
        var highest_value = Int(self.highest_atom)
        var minimum_regular = 1

        if highest_value > 4:
            minimum_regular = highest_value - 4

        var maximum_regular = 1
        if highest_value > 1:
            maximum_regular = highest_value - 1

        return (minimum_regular, maximum_regular)

    def pick_straggler_spawn(self, minimum_regular: Int) -> Int8:
        var stragglers: List[Int8] = []

        for token in self.pieces:
            if token > 0 and Int(token) < minimum_regular:
                stragglers.append(token)

        if len(stragglers) == 0 or self.atom_count <= 0:
            return EMPTY

        var pity_threshold = 1.0 / Float64(self.atom_count)
        if random_float64() >= pity_threshold:
            return EMPTY

        var straggler_idx = Int(random_si64(0, Int64(len(stragglers) - 1)))
        return stragglers[straggler_idx]

    def update_spawn_counters(mut self, spawned_piece: Int8):
        if spawned_piece == PLUS:
            self.moves_since_plus = 0
        else:
            self.moves_since_plus += 1

        if spawned_piece == MINUS:
            self.moves_since_minus = 0
        else:
            self.moves_since_minus += 1

    def spawn_piece(mut self):
        if self.moves_since_plus >= 5:
            self.current_piece = PLUS
            self.update_spawn_counters(PLUS)
            return

        if self.highest_atom <= HYDROGEN:
            self.current_piece = HYDROGEN
            self.update_spawn_counters(HYDROGEN)
            return

        var special_roll = random_float64()
        var minus_threshold = PLUS_SPAWN_RATE + MINUS_SPAWN_RATE
        var black_plus_threshold = minus_threshold + BLACK_PLUS_SPAWN_RATE
        var neutrino_threshold = black_plus_threshold + NEUTRINO_SPAWN_RATE

        if special_roll < PLUS_SPAWN_RATE:
            self.current_piece = PLUS
        elif special_roll < minus_threshold:
            self.current_piece = MINUS
        elif (
            special_roll < black_plus_threshold
            and self.score > BLACK_PLUS_SCORE_GATE
        ):
            self.current_piece = BLACK_PLUS
        elif (
            special_roll < neutrino_threshold
            and self.score > NEUTRINO_SCORE_GATE
        ):
            self.current_piece = NEUTRINO
        else:
            var bounds = self.regular_spawn_bounds()
            var pity_piece = self.pick_straggler_spawn(bounds[0])

            if pity_piece > 0:
                self.current_piece = pity_piece
            else:
                self.current_piece = Int8(
                    random_si64(Int64(bounds[0]), Int64(bounds[1]))
                )

        self.update_spawn_counters(self.current_piece)

    def spawn_initial_board(mut self):
        self.pieces = []

        for _ in range(6):
            self.pieces.append(Int8(random_si64(1, 3)))

        self.atom_count = len(self.pieces)
        self.highest_atom = HYDROGEN

        for token in self.pieces:
            if token > self.highest_atom:
                self.highest_atom = token

    def write_to(self, mut writer: Some[Writer]):
        writer.write(
            "GameState(pieces=",
            self.pieces,
            ", atom_count=",
            self.atom_count,
            ", current_piece=",
            self.current_piece,
            ", score=",
            self.score,
            ", move_count=",
            self.move_count,
            ", highest_atom=",
            self.highest_atom,
            ", holding_piece=",
            self.holding_piece,
            ", held_piece=",
            self.held_piece,
            ", held_can_convert=",
            self.held_can_convert,
            ", is_terminal=",
            self.is_terminal,
            ", moves_since_plus=",
            self.moves_since_plus,
            ", moves_since_minus=",
            self.moves_since_minus,
            ", rng_seed=",
            self.rng_seed,
            ")",
        )
