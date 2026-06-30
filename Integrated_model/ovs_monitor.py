"""
=========================================================
OVS Monitoring Module
=========================================================
"""

import re
import subprocess

from config import NUM_GROUPS, SWITCHES_PER_GROUP

from cache import (
    learn_new_mac,
    update_existing_mac
)
from utils import log_event


# =========================================================
# Switch List
# =========================================================

SWITCHES = [
    f"s{i}"
    for i in range(
        1,
        (NUM_GROUPS * SWITCHES_PER_GROUP) + 1
    )
]


# =========================================================
# OVS Helpers
# =========================================================

def get_fdb(switch):
    """
    Return OVS forwarding database output.
    """

    try:

        return subprocess.check_output(
            [
                "ovs-appctl",
                "fdb/show",
                switch,
            ],
            text=True,
        )

    except Exception:
        return ""


def get_tx_stats(switch):
    """
    Return TX packet counters.

    Returns:
        {port: tx_packets}
    """

    stats = {}

    try:

        output = subprocess.check_output(
            [
                "ovs-ofctl",
                "dump-ports",
                switch,
            ],
            text=True,
        )

    except Exception:

        return stats

    current_port = None

    for line in output.splitlines():

        port_match = re.search(
            r"port\s+(\d+):",
            line,
        )

        if port_match:

            current_port = int(
                port_match.group(1)
            )

            continue

        tx_match = re.search(
            r"tx pkts=(\d+)",
            line,
        )

        if tx_match and current_port is not None:

            stats[current_port] = int(
                tx_match.group(1)
            )

    return stats


# =========================================================
# Synchronize OVS FDB
# =========================================================

def sync_fdb():
    """
    Read OVS FDBs and synchronize
    forwarding cache state.
    """

    observed = set()

    for switch in SWITCHES:

        port_stats = get_tx_stats(
            switch
        )

        fdb = get_fdb(
            switch
        )

        for line in fdb.splitlines():

            match = re.search(
                r"^\s*(\d+)\s+\d+\s+([0-9a-f:]{17})\s+(\d+)",
                line,
                re.IGNORECASE,
            )

            if not match:
                continue

            port = int(
                match.group(1)
            )

            mac = (
                match.group(2)
                .lower()
            )

            tx_packets = port_stats.get(
                port,
                0,
            )

            observed.add(mac)

            if mac not in forwarding_table:

                learn_new_mac(
                    mac,
                    switch,
                    port,
                    tx_packets,
                )

            else:

                update_existing_mac(
                    mac,
                    switch,
                    port,
                    tx_packets,
                )

    #
    # Detect disappeared entries
    #
    for mac in list(
        forwarding_table.keys()
    ):

        if mac not in observed:

            unknown_unicast(mac)

            log_event(
                f"MAC removed from OVS: {mac}"
            )