def calculate_eviction_score(
    age,
    tx_count,
    flap_count,
    age_max=300
):

    age_term = age / age_max

    tx_term = 1 / max(tx_count, 1)

    flap_term = flap_count

    score = (
        0.4 * age_term
        + 0.3 * tx_term
        + 0.3 * flap_term
    )

    return round(score, 4)