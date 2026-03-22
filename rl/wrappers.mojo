def linear_reward(raw_reward: Int) -> Float64:
    return Float64(raw_reward)


def shaped_reward(raw_reward: Int, atom_delta: Int) -> Float64:
    var value = Float64(raw_reward)

    if atom_delta < 0:
        value += 0.1
    elif atom_delta > 0:
        value -= 0.1

    return value


def normalized_reward(value: Float64) -> Float64:
    var scaled = value / 32.0

    if scaled > 1.0:
        return 1.0

    if scaled < -1.0:
        return -1.0

    return scaled
