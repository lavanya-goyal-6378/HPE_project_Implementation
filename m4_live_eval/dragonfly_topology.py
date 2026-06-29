from mininet.net import Mininet
from mininet.node import OVSSwitch
import time
import subprocess


def install_normal_flows(net):
    """
    Install a NORMAL action flow on every switch so OVS runs in
    MAC-learning mode and populates the FDB table.
    Without this, fdb/show always returns empty.
    """
    for sw in net.switches:
        subprocess.call(
            f"sudo ovs-ofctl add-flow {sw.name} priority=1,actions=NORMAL",
            shell=True
        )


def build_dragonfly():

    # FIX 1: Use OVSSwitch with stp=True to prevent broadcast storms
    # caused by the loops in the dragonfly global ring topology.
    net = Mininet(
        controller=None,
        switch=OVSSwitch
    )

    # -------------------------
    # GROUP 0
    # -------------------------

    g0_s0 = net.addSwitch("g0s0", stp=True)
    g0_s1 = net.addSwitch("g0s1", stp=True)

    # -------------------------
    # GROUP 1
    # -------------------------

    g1_s0 = net.addSwitch("g1s0", stp=True)
    g1_s1 = net.addSwitch("g1s1", stp=True)

    # -------------------------
    # GROUP 2
    # -------------------------

    g2_s0 = net.addSwitch("g2s0", stp=True)
    g2_s1 = net.addSwitch("g2s1", stp=True)

    # -------------------------
    # HOSTS
    # -------------------------

    h1 = net.addHost("g0s0h1")
    h2 = net.addHost("g0s1h1")

    h3 = net.addHost("g1s0h1")
    h4 = net.addHost("g1s1h1")

    h5 = net.addHost("g2s0h1")
    h6 = net.addHost("g2s1h1")

    # -------------------------
    # HOST LINKS
    # -------------------------

    net.addLink(h1, g0_s0)
    net.addLink(h2, g0_s1)

    net.addLink(h3, g1_s0)
    net.addLink(h4, g1_s1)

    net.addLink(h5, g2_s0)
    net.addLink(h6, g2_s1)

    # -------------------------
    # LOCAL LINKS (intra-group)
    # -------------------------

    net.addLink(g0_s0, g0_s1)
    net.addLink(g1_s0, g1_s1)
    net.addLink(g2_s0, g2_s1)

    # -------------------------
    # GLOBAL LINKS (inter-group)
    # -------------------------

    # s0 ring: g0 -> g1 -> g2 -> g0
    net.addLink(g0_s0, g1_s0)
    net.addLink(g1_s0, g2_s0)
    net.addLink(g2_s0, g0_s0)

    # s1 ring: g0 -> g1 -> g2 -> g0
    net.addLink(g0_s1, g1_s1)
    net.addLink(g1_s1, g2_s1)
    net.addLink(g2_s1, g0_s1)
    return net

if __name__ == "__main__":
    net = build_dragonfly()
    net.start()
    install_normal_flows(net)
    print("Waiting for STP convergence...")
    time.sleep(15)
    net.pingAll()

    from mininet.cli import CLI
    CLI(net)

    net.stop()
        