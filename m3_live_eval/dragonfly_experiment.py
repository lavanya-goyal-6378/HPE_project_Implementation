from mininet.cli import CLI

from dragonfly_topology import build_dragonfly
from mac_table_manager import MACTableManager

import time


# ---------------------------------------
# REAL TX COUNT
# ---------------------------------------

def get_tx_count(host):

    return int(
        host.cmd(
            f"cat /sys/class/net/{host.name}-eth0/statistics/tx_packets"
        ).strip()
    )


# ---------------------------------------
# GET HOST'S ATTACHED SWITCH + PORT
# ---------------------------------------

def get_switch_and_port(host):

    intf = host.intfList()[0]

    link = intf.link

    if link.intf1.node == host:

        switch_intf = link.intf2

    else:

        switch_intf = link.intf1

    switch_name = switch_intf.node.name

    port = int(
        switch_intf.name.split("eth")[-1]
    )

    return switch_name, port


# ---------------------------------------
# MAIN
# ---------------------------------------

def run():

    net = build_dragonfly()

    net.start()

    # Standalone MAC learning
    for sw in net.switches:

        sw.cmd(
            f"ovs-vsctl set-fail-mode {sw.name} standalone"
        )

    manager = MACTableManager()

    # Increase capacity initially
    manager.MAX_MAC_ENTRIES = 10

    # ----------------------------------
    # HOST REFERENCES
    # ----------------------------------

    h1 = net.get("g0_s0_h1")
    h2 = net.get("g0_s1_h1")

    h3 = net.get("g1_s0_h1")
    h4 = net.get("g1_s1_h1")

    h5 = net.get("g2_s0_h1")
    h6 = net.get("g2_s1_h1")

    # ----------------------------------
    # GENERATE REAL TRAFFIC
    # ----------------------------------

    print("\n===== GENERATING TRAFFIC =====\n")

    h1.cmd(f"ping -c 50 {h6.IP()}")

    h3.cmd(f"ping -c 10 {h2.IP()}")

    h5.cmd(f"ping -c 2 {h4.IP()}")

    # ----------------------------------
    # LEARN ALL HOSTS
    # ----------------------------------

    print("\n===== LEARNING HOSTS =====\n")

    for host in net.hosts:

        tx_count = get_tx_count(host)

        switch_name, port = get_switch_and_port(host)

        print(
            f"Host={host.name} | "
            f"MAC={host.MAC()} | "
            f"Switch={switch_name} | "
            f"Port={port} | "
            f"TX={tx_count}"
        )

        manager.learn_mac(
            host.MAC(),
            port,
            tx_count
        )

    manager.show()

    # ----------------------------------
    # AGE ENTRIES
    # ----------------------------------

    print("\nWaiting 10 seconds...\n")

    time.sleep(10)

    # ----------------------------------
    # EMULATE FLAPPING
    # ----------------------------------

    print("\n===== FLAP EMULATION =====\n")

    tx = get_tx_count(h5)

    manager.learn_mac(
        h5.MAC(),
        20,
        tx
    )

    manager.learn_mac(
        h5.MAC(),
        30,
        tx
    )

    manager.show()

    # ----------------------------------
    # NOW REDUCE TABLE SIZE
    # ----------------------------------

    manager.MAX_MAC_ENTRIES = 6

    # ----------------------------------
    # TRIGGER EVICTION
    # ----------------------------------

    print("\n===== EVICTION TEST =====\n")

    manager.learn_mac(
        "00:00:00:00:99:99",
        99,
        1
    )

    manager.show()

    print("\n===== ENTERING CLI =====\n")

    CLI(net)

    net.stop()


if __name__ == "__main__":

    run()