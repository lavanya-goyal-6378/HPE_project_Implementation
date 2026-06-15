import math


def calculate_zscores(flap_counts):

    if len(flap_counts) < 2:
        return {}

    values = list(flap_counts.values())

    mean = sum(values) / len(values)

    variance = sum(
        (x - mean) ** 2
        for x in values
    ) / len(values)

    std = math.sqrt(variance)

    scores = {}

    for mac, count in flap_counts.items():

        if std == 0:
            z = 0
        else:
            z = (count - mean) / std

        scores[mac] = round(z, 3)

    return scores