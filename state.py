"""
=========================================================
Unified Intelligent Forwarding Engine
Shared Runtime State

Stores global forwarding cache state.

Imported by:
    cache.py
    models.py
    ovs_monitor.py
    reporter.py

=========================================================
"""


# =========================================================
# Forwarding Table
# =========================================================

#
# Main optimized forwarding cache
#
# Key:
#     MAC Address
#
# Value:
#
# {
#     switch,
#     port,
#     tx_count,
#     last_tx,
#     flap_count,
#     ttl,
#     forwarding_score,
#     priority,
#     last_seen
# }
#

forwarding_table = {}



# =========================================================
# Engine Statistics
# =========================================================

engine_stats = {


    #
    # New MAC learned
    #
    "mac_learned": 0,


    #
    # Existing MAC refreshed
    #
    "mac_updated": 0,


    #
    # TTL based removal
    #
    "mac_expired": 0,


    #
    # Capacity based removal
    #
    "mac_evicted": 0,


    #
    # Destination MAC missing
    #
    "unknown_unicast_events": 0

}



# =========================================================
# State Reset Helper
# =========================================================

def reset_state():
    """
    Clear forwarding state.

    Useful for starting
    a new experiment.
    """


    forwarding_table.clear()


    engine_stats.clear()


    engine_stats.update({

        "mac_learned": 0,

        "mac_updated": 0,

        "mac_expired": 0,

        "mac_evicted": 0,

        "unknown_unicast_events": 0

    })



# =========================================================
# State Snapshot
# =========================================================

def get_state():

    """
    Return complete runtime state.
    """


    return {

        "forwarding_table": forwarding_table,

        "engine_stats": engine_stats

    }