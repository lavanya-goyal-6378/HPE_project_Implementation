"""
=========================================================
Simple Forwarding Engine
=========================================================
"""

import time
import signal
import subprocess


from cache import (
    snapshot_baseline,
    forwarding_table,
    learn_new_mac,
    update_existing_mac,
    unknown_unicast
)

from config import ENGINE_INTERVAL

from models import (
    run_models,
    expire_entries,
    eviction_check
)

from reporter import reporting_phase


running = True


# Statistics

unicast_count = 0
flood_count = 0


# =========================================================
# Unknown MAC Pool
#
# Each MAC has a different tx_count representing
# how active that host is on the network.
#
# Low  tx -> low activity -> low TTL  -> expires ~6  cycles
# Mid  tx -> mid activity -> mid TTL  -> expires ~8  cycles
# High tx -> high activity -> high TTL -> expires ~12 cycles
#
# This is how the mathematical TTL model naturally
# produces different lifetimes without any randomness.
# The table stays optimized: inactive entries are removed
# early, active entries stay longer. Flood events appear
# only when an entry expires, then drop back to 0 after
# re-learning. Table size reduces over time as low-activity
# MACs age out and are not immediately re-learned.
# =========================================================

UNKNOWN_MAC_POOL = [

    # (mac,              switch,   port, initial_tx)
    ("aa:bb:cc:dd:ee:01", "g0_s0", 1,  2),   # very low activity  -> TTL ~31s -> expires ~6  cycles
    ("aa:bb:cc:dd:ee:02", "g0_s1", 2,  2),   # very low activity  -> TTL ~31s -> expires ~6  cycles
    ("aa:bb:cc:dd:ee:03", "g0_s0", 3,  5),   # low activity       -> TTL ~41s -> expires ~8  cycles
    ("aa:bb:cc:dd:ee:04", "g1_s0", 1,  5),   # low activity       -> TTL ~41s -> expires ~8  cycles
    ("aa:bb:cc:dd:ee:05", "g0_s1", 4,  10),  # medium activity    -> TTL ~50s -> expires ~10 cycles
    ("aa:bb:cc:dd:ee:06", "g1_s0", 2,  10),  # medium activity    -> TTL ~50s -> expires ~10 cycles
    ("aa:bb:cc:dd:ee:07", "g1_s1", 3,  20),  # high activity      -> TTL ~60s -> expires ~12 cycles
    ("aa:bb:cc:dd:ee:08", "g1_s1", 4,  50),  # very high activity -> TTL  60s -> expires ~12 cycles

]




def stop_engine(sig, frame):

    global running

    running = False

    print("\nStopping Engine...")




def get_ovs_bridges():

    try:

        output = subprocess.check_output(
            [
                "ovs-vsctl",
                "list-br"
            ],
            text=True
        )

        bridges = output.splitlines()

        print(
            "Detected Bridges:",
            bridges
        )

        return bridges


    except Exception as e:

        print(
            "Bridge discovery failed:",
            e
        )

        return []




def read_ovs_fdb():

    switches = get_ovs_bridges()

    entries = []

    for sw in switches:

        try:

            output = subprocess.check_output(
                [
                    "ovs-appctl",
                    "fdb/show",
                    sw
                ],
                text=True
            )

            for line in output.splitlines():

                parts = line.split()

                if len(parts) >= 4:

                    try:

                        port = int(parts[0])

                        mac = parts[2].lower()

                        entries.append(
                            (mac, sw, port)
                        )

                    except ValueError:

                        continue

        except Exception as e:

            print("FDB error", sw, e)

    return entries




def sync_fdb():

    fdb = read_ovs_fdb()

    for mac, switch, port in fdb:

        if mac not in forwarding_table:

            learn_new_mac(mac, switch, port, 0)

        else:

            update_existing_mac(mac, switch, port, 0)




def analyze_forwarding():

    global unicast_count
    global flood_count

    unicast_count = 0
    flood_count = 0

    print("\n--- Traffic Analysis ---")


    # =========================
    # UNICAST FORWARDING + FLOOD
    #
    # For each MAC in the pool:
    #
    # KNOWN -> forward, and update tx_count so
    #          the TTL model sees continued activity.
    #          Active MACs keep a HIGH TTL and stay
    #          in the table longer (table optimization).
    #
    # UNKNOWN -> flood this cycle (TTL expired and
    #            entry was removed by expire_entries),
    #            then re-learn with its original tx_count
    #            so the TTL model assigns the correct
    #            lifetime again on the next run_models().
    #
    # Low-activity MACs expire sooner -> more frequent
    # brief flood spikes for those MACs.
    # High-activity MACs stay long -> rarely flood.
    # This is the table optimization: only entries that
    # deserve a place in the table keep their place.
    # =========================

    for mac, switch, port, initial_tx in UNKNOWN_MAC_POOL:

        if mac in forwarding_table:

            data = forwarding_table[mac]

            unicast_count += 1

            print(
                "[UNICAST FORWARD]",
                mac,
                "=>",
                data["switch"],
                "port",
                data["port"],
                "| tx:", data.get("tx_count", 0)
            )

            # Update with its characteristic tx_count.
            # High tx -> high TTL -> stays in table longer.
            # Low  tx -> low  TTL -> expires sooner.
            # update_existing_mac(
            #     mac,
            #     switch,
            #     port,
            #     data.get("last_tx", 0) + initial_tx
            # )

        else:

            # TTL expired -> entry was removed -> flood
            flood_count += 1

            unknown_unicast(mac)

            print(
                "[UNKNOWN UNICAST FLOOD]",
                mac,
                "Flooding... (TTL expired, re-learning)"
            )

            # Re-learn with original tx_count so TTL
            # model assigns the correct lifetime again
            learn_new_mac(mac, switch, port, initial_tx)


    print("\nTraffic Summary:")

    print("Forwarded :", unicast_count)

    print("Flooded   :", flood_count)




def engine_cycle():

    print("\n--- Engine Cycle ---")

    sync_fdb()

    # Recalculate TTL, forwarding score, priority
    # for every entry based on its current tx_count.
    # Low-tx entries get lower TTL here.
    run_models()

    # Remove entries whose age has exceeded their TTL.
    # Low-tx MACs expire first (shorter TTL from run_models).
    expire_entries()

    # Remove lowest-priority entries if table exceeds capacity.
    eviction_check()

    print(
        "\nForwarding Entries:",
        len(forwarding_table)
    )

    for mac, data in forwarding_table.items():

        print(
            mac,
            "=>",
            data["switch"],
            "port",
            data["port"],
            "| TTL:", round(data.get("ttl", 0), 1),
            "| tx:", data.get("tx_count", 0)
        )

    analyze_forwarding()

    reporting_phase()

    print("\n--- Flood Reduction Statistics ---")

    print("Unicast Forwarded         :", unicast_count)

    print("Unknown Unicast Flood Events:", flood_count)

    print("Table Size                :", len(forwarding_table))




def start_engine():

    signal.signal(signal.SIGINT, stop_engine)

    signal.signal(signal.SIGTERM, stop_engine)

    print("Starting Simple Forwarding Engine...")

    snapshot_baseline()

    # Pool MACs start unknown.
    # Cycle 1: all 8 flood and are learned with
    # their respective tx_counts.
    # run_models() then assigns each a different TTL.
    # Low-tx MACs expire after ~6 cycles,
    # high-tx MACs after ~12 cycles.

    while running:

        engine_cycle()

        time.sleep(ENGINE_INTERVAL)




if __name__ == "__main__":

    start_engine()