from mininet.net import Mininet


def build_dragonfly():

    net = Mininet(controller=None)

    # -------------------------
    # GROUP 0
    # -------------------------

    g0_s0 = net.addSwitch("g0_s0")
    g0_s1 = net.addSwitch("g0_s1")

    # -------------------------
    # GROUP 1
    # -------------------------

    g1_s0 = net.addSwitch("g1_s0")
    g1_s1 = net.addSwitch("g1_s1")

    # -------------------------
    # GROUP 2
    # -------------------------

    g2_s0 = net.addSwitch("g2_s0")
    g2_s1 = net.addSwitch("g2_s1")

    # -------------------------
    # HOSTS
    # -------------------------

    h1 = net.addHost("g0_s0_h1")
    h2 = net.addHost("g0_s1_h1")

    h3 = net.addHost("g1_s0_h1")
    h4 = net.addHost("g1_s1_h1")

    h5 = net.addHost("g2_s0_h1")
    h6 = net.addHost("g2_s1_h1")

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
    # LOCAL LINKS
    # -------------------------

    net.addLink(g0_s0, g0_s1)
    net.addLink(g1_s0, g1_s1)
    net.addLink(g2_s0, g2_s1)

    # -------------------------
    # GLOBAL LINKS
    # -------------------------

    net.addLink(g0_s0, g1_s0)
    net.addLink(g1_s0, g2_s0)
    net.addLink(g2_s0, g0_s0)

    return net