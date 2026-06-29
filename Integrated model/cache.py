"""
=========================================================
Cache Management
Redis Storage + Forwarding Table Management
=========================================================
"""

import json
import re
import subprocess

from config import *

from redis_client import get_redis

from utils import (
    log_event,
    current_time
)

from state import (
    forwarding_table,
    engine_stats
)


# =========================================================
# Redis
# =========================================================

r = get_redis()



# =========================================================
# OVS Helper
# =========================================================

def get_fdb(switch):
    """
    Read OVS forwarding database.
    """

    try:

        output = subprocess.check_output(

            [
                "ovs-appctl",
                "fdb/show",
                switch
            ],

            text=True

        )

        return output


    except Exception:

        return ""



# =========================================================
# Redis Helpers
# =========================================================

def store_mac(mac):
    """
    Store forwarding entry in Redis.
    """

    if mac not in forwarding_table:

        return


    r.set(

        MAC_PREFIX + mac,

        json.dumps(
            forwarding_table[mac]
        )

    )



def remove_mac(mac):
    """
    Delete forwarding entry.
    """

    r.delete(

        MAC_PREFIX + mac

    )



def store_engine_stats():
    """
    Save statistics.
    """

    r.set(

        STATS_PREFIX + "engine",

        json.dumps(
            engine_stats
        )

    )



# =========================================================
# Baseline Snapshot
# =========================================================
def snapshot_baseline():
    """
    Save original OVS MAC table.
    """

    print("\nCreating baseline snapshot...\n")

    total = 0


    switches = []

    for g in range(NUM_GROUPS):

        for s in range(SWITCHES_PER_GROUP):

            switches.append(
                f"g{g}_s{s}"
            )


    for switch in switches:


        fdb = get_fdb(switch)


        for line in fdb.splitlines():

            match = re.search(
                r'^\s*(\d+)\s+\d+\s+([0-9a-f:]{17})',
                line,
                re.I
            )


            if not match:
                continue


            port = int(match.group(1))

            mac = match.group(2).lower()


            snapshot = {

                "switch": switch,

                "port": port,

                "timestamp": current_time()

            }


            r.set(

                SNAPSHOT_PREFIX + mac,

                json.dumps(snapshot)

            )


            total += 1


    print(
        f"[BASELINE] {total} MAC entries saved."
    )


    log_event(
        f"Baseline snapshot created ({total} entries)"
    )
# =========================================================
# Unknown Unicast
# =========================================================

def unknown_unicast(mac):
    """
    Handle unknown destination MAC.
    """

    engine_stats[

        "unknown_unicast_events"

    ] += 1



    log_event(

        f"Unknown Unicast -> {mac}"

    )


    store_engine_stats()



# =========================================================
# MAC Learning
# =========================================================

def learn_new_mac(
        mac,
        switch,
        port,
        tx_packets
):

    """
    Learn new MAC.
    """


    forwarding_table[mac] = {


        "switch": switch,


        "port": port,


        "tx_count": tx_packets,


        "last_tx": tx_packets,


        "flap_count": 0,


        "ttl": TTL_BASE,


        "forwarding_score": 0.0,


        "priority": 0.0,


        "last_seen": current_time()


    }



    engine_stats["mac_learned"] += 1



    store_mac(mac)



    log_event(

        f"LEARNED {mac} -> {switch}:{port}"

    )



# =========================================================
# MAC Update
# =========================================================

def update_existing_mac(
        mac,
        switch,
        port,
        tx_packets
):

    """
    Update existing MAC.
    """


    entry = forwarding_table[mac]



    if (

        entry["switch"] != switch

        or

        entry["port"] != port

    ):


        entry["flap_count"] += 1



        log_event(

            f"MAC FLAP {mac} "

            f"{entry['switch']}:{entry['port']} "

            f"-> {switch}:{port}"

        )



    delta = max(

        tx_packets - entry["last_tx"],

        0

    )


    entry["tx_count"] = delta


    entry["last_tx"] = tx_packets


    entry["switch"] = switch


    entry["port"] = port


    # entry["last_seen"] = current_time()



    engine_stats["mac_updated"] += 1



    store_mac(mac)



# =========================================================
# Cache Statistics
# =========================================================

def cache_statistics():

    entries = len(
        forwarding_table
    )



    if entries == 0:


        stats = {


            "entries": 0,


            "average_ttl": 0,


            "average_priority": 0,


            "average_forwarding_score": 0,


            "expired": engine_stats["mac_expired"],


            "evicted": engine_stats["mac_evicted"]


        }



    else:


        stats = {


            "entries": entries,


            "average_ttl": round(

                sum(

                    e.get(
                        "ttl",
                        0
                    )

                    for e in forwarding_table.values()

                )

                / entries,

                2

            ),



            "average_priority": round(

                sum(

                    e.get(
                        "priority",
                        0
                    )

                    for e in forwarding_table.values()

                )

                / entries,

                2

            ),


            "average_forwarding_score": round(

                sum(

                    e.get(
                        "forwarding_score",
                        0
                    )

                    for e in forwarding_table.values()

                )

                / entries,

                2

            ),



            "expired": engine_stats["mac_expired"],


            "evicted": engine_stats["mac_evicted"]


        }



    r.set(

        STATS_PREFIX + "forwarding",

        json.dumps(stats)

    )


    return stats