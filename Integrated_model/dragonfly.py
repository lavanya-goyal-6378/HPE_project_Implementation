"""
Dragonfly Topology
"""

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import setLogLevel, info

import threading
import time
import subprocess

from engine import start_engine


#
# Create Topology
#

def create_network():

    net = Mininet(
        controller=None
    )


    # -------------------------
    # Switches
    # -------------------------

    g0_s0 = net.addSwitch("g0_s0")
    g0_s1 = net.addSwitch("g0_s1")

    g1_s0 = net.addSwitch("g1_s0")
    g1_s1 = net.addSwitch("g1_s1")

    g2_s0 = net.addSwitch("g2_s0")
    g2_s1 = net.addSwitch("g2_s1")


    # -------------------------
    # Hosts
    # -------------------------

    hosts = []

    for name, sw in [

        ("g0_s0_h1", g0_s0),
        ("g0_s1_h1", g0_s1),

        ("g1_s0_h1", g1_s0),
        ("g1_s1_h1", g1_s1),

        ("g2_s0_h1", g2_s0),
        ("g2_s1_h1", g2_s1)

    ]:

        h = net.addHost(name)

        net.addLink(h, sw)

        hosts.append(h)


    # -------------------------
    # Local group links
    # -------------------------

    net.addLink(g0_s0, g0_s1)

    net.addLink(g1_s0, g1_s1)

    net.addLink(g2_s0, g2_s1)


    # -------------------------
    # Dragonfly global links
    # -------------------------

    net.addLink(g0_s0, g1_s0)

    net.addLink(g1_s0, g2_s0)


    return net



#
# Configure OVS
#

def configure_switches(net):

    print("\n[!] Configuring switches...")

    for sw in net.switches:

        sw.cmd(
            f"ovs-vsctl set-fail-mode {sw.name} standalone"
        )

        sw.cmd(
            f"ovs-vsctl set Bridge {sw.name} stp_enable=true"
        )

        # normal L2 forwarding
        sw.cmd(
            f"ovs-ofctl add-flow {sw.name} "
            "priority=0,actions=normal"
        )



#
# Main
#

def run_network():

    net = create_network()

    info("\n*** Starting Network\n")

    net.start()

    configure_switches(net)

    # Let OVS bridges fully initialise before
    # the engine starts reading them
    time.sleep(2)

    print("\n[+] Testing connectivity\n")

    net.pingAll()

    print("\n[+] Dragonfly Ready\n")

    # Start the forwarding engine in background
    # AFTER net.start() so OVS bridges exist
    # and sync_fdb() finds real entries
    engine_thread = threading.Thread(
        target=start_engine,
        daemon=True
    )

    engine_thread.start()

    print("\n[+] Forwarding Engine Started\n")


    CLI(net)

    net.stop()



if __name__ == "__main__":

    setLogLevel("info")

    run_network()