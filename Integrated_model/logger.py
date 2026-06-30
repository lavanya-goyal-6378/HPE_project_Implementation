"""
=========================================================
Demo Logger
logger.py
=========================================================

Writes two files every engine cycle:

1. logs/engine_demo.log
   Human-readable structured log.
   Shows every cycle: table state, per-MAC details,
   forwarding/flood events, engine statistics.
   Easy to read during a live demo.

2. logs/engine_demo.csv
   Machine-readable CSV.
   One row per cycle — used for Grafana, Excel,
   or any post-demo analysis.
   Columns:
       cycle, timestamp, datetime,
       table_size, unicast_forwarded, flooded,
       mac_learned, mac_updated, mac_expired, mac_evicted,
       unknown_unicast_events,
       avg_ttl, avg_priority, avg_forwarding_score

=========================================================
"""

import csv
import os
import time

from config import LOG_DIR
from state import forwarding_table, engine_stats


# =========================================================
# File Paths
# =========================================================

DEMO_LOG = os.path.join(LOG_DIR, "engine_demo.log")
DEMO_CSV = os.path.join(LOG_DIR, "engine_demo.csv")

CSV_COLUMNS = [
    "cycle",
    "timestamp",
    "datetime",
    "table_size",
    "unicast_forwarded",
    "flooded",
    "mac_learned",
    "mac_updated",
    "mac_expired",
    "mac_evicted",
    "unknown_unicast_events",
    "avg_ttl",
    "avg_priority",
    "avg_forwarding_score",
]

# Incremented once per call to write_cycle_log()
_cycle_counter = 0


# =========================================================
# Setup — call once at engine start
# =========================================================

def setup_logger():
    """
    Create the logs/ directory and write the CSV header.
    Call this once from start_engine() before the main loop.
    """

    os.makedirs(LOG_DIR, exist_ok=True)

    # Write CSV header (overwrite any previous run)
    with open(DEMO_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()

    # Write log file header (overwrite any previous run)
    with open(DEMO_LOG, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("  SDN Intelligent Forwarding Engine — Demo Log\n")
        f.write(f"  Started: {_now_str()}\n")
        f.write("=" * 60 + "\n\n")

    print(f"[LOGGER] Log  -> {DEMO_LOG}")
    print(f"[LOGGER] CSV  -> {DEMO_CSV}")


# =========================================================
# Main cycle writer — call from reporting_phase()
# =========================================================

def write_cycle_log(unicast_forwarded, flooded):
    """
    Append one cycle's data to both the log file and the CSV.

    Parameters
    ----------
    unicast_forwarded : int
        Number of MACs forwarded as unicast this cycle.
    flooded : int
        Number of unknown-unicast flood events this cycle.
    """

    global _cycle_counter
    _cycle_counter += 1

    now      = time.time()
    now_str  = _now_str()
    entries  = len(forwarding_table)

    # ---- Per-entry averages ----
    if entries > 0:
        avg_ttl   = round(sum(e.get("ttl",   0) for e in forwarding_table.values()) / entries, 2)
        avg_pri   = round(sum(e.get("priority", 0) for e in forwarding_table.values()) / entries, 4)
        avg_score = round(sum(e.get("forwarding_score", 0) for e in forwarding_table.values()) / entries, 4)
    else:
        avg_ttl = avg_pri = avg_score = 0.0

    # =========================================================
    # 1. Human-readable log
    # =========================================================
    with open(DEMO_LOG, "a") as f:

        f.write(f"\n{'─' * 60}\n")
        f.write(f"  CYCLE {_cycle_counter:>4}   |   {now_str}\n")
        f.write(f"{'─' * 60}\n")

        # Table summary
        f.write(f"  Table Size          : {entries}\n")
        f.write(f"  Unicast Forwarded   : {unicast_forwarded}\n")
        f.write(f"  Unknown Unicast Flood: {flooded}\n")
        f.write(f"  Avg TTL             : {avg_ttl:.2f} s\n")
        f.write(f"  Avg Priority Score  : {avg_pri:.4f}\n")
        f.write(f"  Avg Forwarding Score: {avg_score:.4f}\n")

        # Cumulative engine stats
        f.write(f"\n  --- Cumulative Engine Stats ---\n")
        f.write(f"  MAC Learned         : {engine_stats['mac_learned']}\n")
        f.write(f"  MAC Updated         : {engine_stats['mac_updated']}\n")
        f.write(f"  TTL Expired         : {engine_stats['mac_expired']}\n")
        f.write(f"  Entries Evicted     : {engine_stats['mac_evicted']}\n")
        f.write(f"  Unknown Unicast (Σ) : {engine_stats['unknown_unicast_events']}\n")

        # Per-MAC detail table
        if forwarding_table:
            f.write(f"\n  --- Forwarding Table ---\n")
            f.write(
                f"  {'MAC':<19} {'Switch':<8} {'Port':>4} "
                f"{'TX':>5} {'TTL':>6} {'Priority':>9} {'Score':>7} {'Flaps':>6}\n"
            )
            f.write(f"  {'─'*19} {'─'*8} {'─'*4} {'─'*5} {'─'*6} {'─'*9} {'─'*7} {'─'*6}\n")

            for mac, e in forwarding_table.items():
                f.write(
                    f"  {mac:<19} {e.get('switch',''):<8} {e.get('port',0):>4} "
                    f"{e.get('tx_count',0):>5} {e.get('ttl',0):>6.1f} "
                    f"{e.get('priority',0):>9.4f} {e.get('forwarding_score',0):>7.4f} "
                    f"{e.get('flap_count',0):>6}\n"
                )
        else:
            f.write(f"\n  [Table is empty this cycle]\n")

        f.write("\n")

    # =========================================================
    # 2. CSV row
    # =========================================================
    row = {
        "cycle":                  _cycle_counter,
        "timestamp":              round(now, 3),
        "datetime":               now_str,
        "table_size":             entries,
        "unicast_forwarded":      unicast_forwarded,
        "flooded":                flooded,
        "mac_learned":            engine_stats["mac_learned"],
        "mac_updated":            engine_stats["mac_updated"],
        "mac_expired":            engine_stats["mac_expired"],
        "mac_evicted":            engine_stats["mac_evicted"],
        "unknown_unicast_events": engine_stats["unknown_unicast_events"],
        "avg_ttl":                avg_ttl,
        "avg_priority":           avg_pri,
        "avg_forwarding_score":   avg_score,
    }

    with open(DEMO_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(row)


# =========================================================
# Helper
# =========================================================

def _now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
