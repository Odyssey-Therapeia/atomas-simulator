from std.random import random_float64, random_si64, seed


comptime MAX_RING_SIZE: Int = 18

comptime EMPTY: Int8 = 0
comptime HYDROGEN: Int8 = 1
comptime PLUS: Int8 = -1
comptime MINUS: Int8 = -2
comptime BLACK_PLUS: Int8 = -3

comptime PLUS_SPAWN_RATE: Float64 = 0.17
comptime MINUS_SPAWN_RATE: Float64 = 0.05
comptime BLACK_PLUS_SPAWN_RATE: Float64 = 0.02


struct GameState(Writable):
    var ring: InlineArray[Int8, MAX_RING_SIZE]
    var ring_size: Int
    var current_piece: Int8
    var score: Int
    var move_count: Int
    var highest_element: Int8
    var holding_absorbed: Bool
    var absorbed_element: Int8
    var is_terminal: Bool

    def __init__(out self):
        seed()
        self.ring = InlineArray[Int8, MAX_RING_SIZE](fill=EMPTY)
        self.ring_size = 0
        self.current_piece = HYDROGEN
        self.score = 0
        self.move_count = 0
        self.highest_element = HYDROGEN
        self.holding_absorbed = False
        self.absorbed_element = EMPTY
        self.is_terminal = False

    def reset(mut self):
        self.ring = InlineArray[Int8, MAX_RING_SIZE](fill=EMPTY)
        self.ring_size = 0
        self.current_piece = HYDROGEN
        self.score = 0
        self.move_count = 0
        self.highest_element = HYDROGEN
        self.holding_absorbed = False
        self.absorbed_element = EMPTY
        self.is_terminal = False

    def spawn_piece(mut self):
        if self.highest_element <= HYDROGEN:
            self.current_piece = HYDROGEN
            return

        var special_roll = random_float64()
        var minus_threshold = PLUS_SPAWN_RATE + MINUS_SPAWN_RATE
        var black_plus_threshold = minus_threshold + BLACK_PLUS_SPAWN_RATE

        if special_roll < PLUS_SPAWN_RATE:
            self.current_piece = PLUS
            return

        if special_roll < minus_threshold:
            self.current_piece = MINUS
            return

        if special_roll < black_plus_threshold:
            self.current_piece = BLACK_PLUS
            return

        var highest_value = Int(self.highest_element)
        var minimum_regular = 1
        if highest_value > 4:
            minimum_regular = highest_value - 4

        var maximum_regular = 1
        if highest_value > 1:
            maximum_regular = highest_value - 1

        var regular_piece = random_si64(
            Int64(minimum_regular), Int64(maximum_regular)
        )
        self.current_piece = Int8(regular_piece)

    def write_to(self, mut writer: Some[Writer]):
        writer.write(
            "GameState(ring=",
            self.ring,
            ", ring_size=",
            self.ring_size,
            ", current_piece=",
            self.current_piece,
            ", score=",
            self.score,
            ", move_count=",
            self.move_count,
            ", highest_element=",
            self.highest_element,
            ", holding_absorbed=",
            self.holding_absorbed,
            ", absorbed_element=",
            self.absorbed_element,
            ", is_terminal=",
            self.is_terminal,
            ")",
        )
