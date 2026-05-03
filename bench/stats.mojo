from std.math import sqrt


def mean(values: List[Float64]) -> Float64:
    if len(values) == 0:
        return 0.0

    var total = 0.0
    for value in values:
        total += value

    return total / Float64(len(values))


def min_value(values: List[Float64]) -> Float64:
    var current_min = values[0]
    for value in values:
        if value < current_min:
            current_min = value

    return current_min


def max_value(values: List[Float64]) -> Float64:
    var current_max = values[0]
    for value in values:
        if value > current_max:
            current_max = value

    return current_max


def sorted_copy(values: List[Float64]) -> List[Float64]:
    var copied = values.copy()

    for index in range(1, len(copied)):
        var current_value = copied[index]
        var position = index

        while position > 0 and copied[position - 1] > current_value:
            copied[position] = copied[position - 1]
            position -= 1

        copied[position] = current_value

    return copied^


def median(values: List[Float64]) -> Float64:
    var ordered = sorted_copy(values)
    var middle = len(ordered) // 2

    if len(ordered) % 2 == 1:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2.0


def standard_deviation(values: List[Float64]) -> Float64:
    if len(values) == 0:
        return 0.0

    var average = mean(values)
    var variance = 0.0

    for value in values:
        var delta = value - average
        variance += delta * delta

    variance /= Float64(len(values))
    return sqrt(variance)
