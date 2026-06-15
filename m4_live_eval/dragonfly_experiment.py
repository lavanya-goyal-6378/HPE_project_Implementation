from dragonfly_topology import build_dragonfly, install_normal_flows
from ovs_fdb_monitor import FDBMonitor
from zscore_detector import calculate_zscores

import subprocess
import time


STP_CONVERGENCE_WAIT = 15

# Quarantined MACs
QUARANTINED_MACS = set()

SWITCHES = [
    "g0s0",
    "g0s1",
    "g1s0",
    "g1s1",
    "g2s0",
    "g2s1"
]


def quarantine_mac(mac):

    if mac in QUARANTINED_MACS:
        return

    print("\n===================================")
    print("[QUARANTINE ACTION]")
    print(f"Blocking MAC: {mac}")
    print("===================================\n")

    for sw in SWITCHES:

        subprocess.call(
            f"sudo ovs-ofctl add-flow {sw} dl_src={mac},actions=drop",
            shell=True
        )

    QUARANTINED_MACS.add(mac)


def run():

    net = build_dragonfly()

    net.start()

    print("\n===== MODEL 4 STARTED =====\n")

    print("[*] Installing NORMAL flows on all switches...")
    install_normal_flows(net)

    print(f"[*] Waiting {STP_CONVERGENCE_WAIT}s for STP to converge...")
    time.sleep(STP_CONVERGENCE_WAIT)

    print("[*] Running pingAll to seed the FDB tables...")
    net.pingAll()

    monitor = FDBMonitor(QUARANTINED_MACS)

    try:

        while True:

            flap_counts = monitor.update()

            print("\nFlap Counts:")
            print(flap_counts)

            zscores = calculate_zscores(flap_counts)

            print("\nZ-Scores:")
            print(zscores)

            for mac, z in zscores.items():

                # Require both:
                # 1. High Z-score
                # 2. At least 3 flaps
                if z > 2 and flap_counts[mac] >= 3:

                    print("\n====================")
                    print("[ALERT]")
                    print(f"MAC = {mac}")
                    print(f"Flaps = {flap_counts[mac]}")
                    print(f"Z-score = {z}")
                    print("====================\n")

                    quarantine_mac(mac)

            print("\n===== QUARANTINED MACS =====")

            if len(QUARANTINED_MACS) == 0:
                print("None")

            for mac in QUARANTINED_MACS:
                print(mac)

            time.sleep(5)

    except KeyboardInterrupt:

        print("\nStopping network...")

        net.stop()


if __name__ == "__main__":

    run()