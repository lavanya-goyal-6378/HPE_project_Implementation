"""
=========================================================
Forwarding Models
models.py
=========================================================

Responsibilities:

1. Dynamic TTL calculation
2. Forwarding stability score
3. Priority calculation
4. TTL expiration
5. Priority eviction
"""

from config import (
    ENABLE_EVICTION,
    UNICAST_TABLE_CAPACITY
)


from utils import (
    age,
    calculate_dynamic_ttl,
    calculate_forwarding_score,
    calculate_priority,
    ttl_expired,
    lowest_priority_entry,
    log_event
)


from cache import (
    store_mac,
    remove_mac,
    store_engine_stats
)


from state import (
    forwarding_table,
    engine_stats
)



# =========================================================
# Run Models
# =========================================================


def run_models():
    """
    Apply mathematical models
    to every forwarding entry.
    """

    occupied = len(
        forwarding_table
    )


    current_pps = sum(

        entry.get(
            "tx_count",
            0
        )

        for entry in forwarding_table.values()

    )


    for mac, entry in list(
        forwarding_table.items()
    ):


        entry.setdefault(
            "total_tx",
            0
        )


        entry["total_tx"] += entry.get(
            "tx_count",
            0
        )



        entry_age = age(
            entry["last_seen"]
        )



        ttl = calculate_dynamic_ttl(

            tx_count=entry.get(
                "tx_count",
                0
            ),

            flap_count=entry.get(
                "flap_count",
                0
            ),

            occupied=occupied,

            table_capacity=
            UNICAST_TABLE_CAPACITY

        )



        score = calculate_forwarding_score(

            ttl=ttl,

            occupied=occupied,

            current_pps=current_pps,

            table_capacity=
            UNICAST_TABLE_CAPACITY

        )



        priority = calculate_priority(

            age=entry_age,

            ttl=ttl,

            tx_count=entry.get(
                "tx_count",
                0
            ),

            flap_count=entry.get(
                "flap_count",
                0
            ),

            forwarding_score=score

        )



        entry["ttl"] = ttl

        entry["forwarding_score"] = score

        entry["priority"] = priority



        store_mac(mac)



        print(

            f"{mac}"

            f" | SW={entry['switch']}"

            f" | P={entry['port']}"

            f" | TX={entry.get('tx_count',0)}"

            f" | TOTAL={entry['total_tx']}"

            f" | TTL={ttl:.2f}"

            f" | Score={score:.2f}"

            f" | Priority={priority:.2f}"

            f" | Flaps={entry.get('flap_count',0)}"

        )


    store_engine_stats()




# =========================================================
# TTL Expiration
# =========================================================


def expire_entries():

    """
    Remove expired MAC entries.
    """


    expired = []


    for mac, entry in list(
        forwarding_table.items()
    ):


        if ttl_expired(

            entry.get(
                "last_seen",
                0
            ),

            entry.get(
                "ttl",
                0
            )

        ):

            expired.append(mac)



    for mac in expired:


        log_event(

            f"TTL Expired -> {mac}"

        )


        remove_mac(mac)


        forwarding_table.pop(
            mac,
            None
        )


        engine_stats[
            "mac_expired"
        ] += 1



    if expired:

        store_engine_stats()





# =========================================================
# Priority Eviction
# =========================================================


def eviction_check():

    """
    Remove lowest-value entries
    when table is full.
    """


    if not ENABLE_EVICTION:

        return



    while len(forwarding_table) > UNICAST_TABLE_CAPACITY:



        victim = lowest_priority_entry(

            forwarding_table

        )



        if victim is None:

            break



        log_event(

            f"Evicted -> {victim}"

        )



        remove_mac(victim)



        forwarding_table.pop(

            victim,

            None

        )



        engine_stats[
            "mac_evicted"
        ] += 1



    store_engine_stats()