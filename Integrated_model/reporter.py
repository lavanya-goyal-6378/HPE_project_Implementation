"""
=========================================================
Reporting and Statistics
=========================================================
"""

import json

from config import STATS_PREFIX

from state import (
    forwarding_table,
    engine_stats,
)

from cache import (
    cache_statistics,
    r,
)

from utils import (
    current_time,
    log_event,
)

from logger import write_cycle_log


# =========================================================
# Console Statistics
# =========================================================

def print_engine_statistics():
    """
    Print engine statistics after each cycle.
    """

    stats = cache_statistics()

    print("\n================ FORWARDING ENGINE ================")

    print(
        f"Active Entries        : {stats['entries']}"
    )

    print(
        f"Average TTL           : "
        f"{stats['average_ttl']:.2f}"
    )

    print(
        f"Average Priority      : "
        f"{stats['average_priority']:.2f}"
    )

    print(
        f"Forwarding Score      : "
        f"{stats['average_forwarding_score']:.2f}"
    )

    print(
        f"MAC Learned           : "
        f"{engine_stats['mac_learned']}"
    )

    print(
        f"MAC Updated           : "
        f"{engine_stats['mac_updated']}"
    )

    print(
        f"TTL Expired           : "
        f"{engine_stats['mac_expired']}"
    )

    print(
        f"Entries Evicted       : "
        f"{engine_stats['mac_evicted']}"
    )

    print(
        "==================================================\n"
    )


# =========================================================
# Redis Snapshot
# =========================================================

def update_forwarding_snapshot():
    """
    Store current forwarding table snapshot.
    """

    snapshot = {
        "entries": len(forwarding_table),
        "timestamp": current_time(),
        "table": forwarding_table,
    }

    r.set(
        STATS_PREFIX + "snapshot",
        json.dumps(snapshot),
    )


# =========================================================
# Engine Health
# =========================================================

def update_engine_health():
    """
    Store engine heartbeat.
    """

    heartbeat = {
        "running": True,
        "last_cycle": current_time(),
        "entries": len(forwarding_table),
    }

    r.set(
        STATS_PREFIX + "health",
        json.dumps(heartbeat),
    )


# =========================================================
# Cycle Logging
# =========================================================

def log_cycle():
    """
    Log one completed engine cycle.
    """

    log_event(
        f"Cycle Complete | "
        f"Entries={len(forwarding_table)} "
        f"Learned={engine_stats['mac_learned']} "
        f"Updated={engine_stats['mac_updated']} "
        f"Expired={engine_stats['mac_expired']} "
        f"Evicted={engine_stats['mac_evicted']}"
    )


# =========================================================
# Export Results
# =========================================================

def export_results():
    """
    Store experiment results.
    """

    report = {
        "timestamp": current_time(),
        "engine_statistics": engine_stats,
        "cache_statistics": cache_statistics(),
        "forwarding_table_size": len(
            forwarding_table
        ),
    }

    r.set(
        STATS_PREFIX + "report",
        json.dumps(report),
    )


# =========================================================
# Reporting Phase
# =========================================================

def reporting_phase(unicast_forwarded=0, flooded=0):
    """
    Execute all reporting tasks.
    """

    update_forwarding_snapshot()

    update_engine_health()

    export_results()

    print_engine_statistics()

    log_cycle()

    # Write demo log file and CSV row for this cycle
    write_cycle_log(unicast_forwarded, flooded)