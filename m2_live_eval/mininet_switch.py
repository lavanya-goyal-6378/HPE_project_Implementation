from dragonfly import topology
from mininet.cli import CLI

from scapy.all import sniff
from scapy.layers.l2 import Ether

import threading
import time

from mac_switch import DragonflySwitch


# -----------------------------
# Create Model 2 Switch
# -----------------------------
dragon = DragonflySwitch()

# -----------------------------
# Packet Observer
# -----------------------------
def process_packet(pkt):

    if Ether in pkt:

        src_mac = pkt[Ether].src

        dragon.packet_observed(src_mac)


def start_sniffer():

    sniff(
        iface="g0_s0-eth1",
        prn=process_packet,
        store=False
    )


# -----------------------------
# Start Dragonfly
# -----------------------------
net = topology()
net.start()

print("\nMININET NETWORK STARTED")
print("-----------------------\n")

for sw in net.switches:
    sw.cmd(
        f'ovs-vsctl set-fail-mode {sw.name} standalone'
    )

# -----------------------------
# Hosts
# -----------------------------
h1 = net.get('g0_s0_h1')
h2 = net.get('g0_s1_h1')
h4 = net.get('g1_s1_h1')

# -----------------------------
# MAC Addresses
# -----------------------------
h1_mac = h1.MAC()
h2_mac = h2.MAC()
h4_mac = h4.MAC()

print("H1:", h1_mac)
print("H2:", h2_mac)
print("H4:", h4_mac)

# -----------------------------
# Learn MACs once
# -----------------------------
dragon.learn_mac(h1_mac, 1)
dragon.learn_mac(h2_mac, 2)
dragon.learn_mac(h4_mac, 3)

print("\nINITIAL MAC TABLE")
dragon.show_mac_table()

# -----------------------------
# Start Packet Monitoring
# -----------------------------
sniffer_thread = threading.Thread(
    target=start_sniffer,
    daemon=True
)

sniffer_thread.start()

time.sleep(2)
# -----------------------------
# Scenario 1: Stable Host
# -----------------------------
print("\nSCENARIO 1 : STABLE HOST")
print("------------------------")

# h1 continuously talks to h2
h1.cmd(
    f"ping -i 1 {h2.IP()} > /dev/null 2>&1 &"
)

print("Started continuous traffic:")
print(f"{h1.name} --> {h2.name}")

time.sleep(20)

print("\nMAC TABLE AFTER STABLE TRAFFIC")

dragon.show_mac_table()
print("\nEXPERIMENT 2 : HIGH TRAFFIC")
print("---------------------------")

h1.cmd(
    f"ping -f {h2.IP()} > /dev/null 2>&1 &"
)

print(f"{h1.name} flooding {h2.name}")

time.sleep(10)

print("\nMAC TABLE AFTER HIGH TRAFFIC")
dragon.show_mac_table()

h1.cmd("pkill ping")


# -----------------------------
# Scenario 2: New Host Appears
# -----------------------------
print("\nSCENARIO 2 : NEW HOST")
print("---------------------")

# h4 was silent until now
print(f"{h4.name} starts communicating")

h4.cmd(
    f"ping -c 5 {h2.IP()}"
)

time.sleep(5)


# -----------------------------
# Final Results
# -----------------------------
print("\nFINAL MAC TABLE")
dragon.show_mac_table()

# -----------------------------
# CLI
# -----------------------------
CLI(net)

# -----------------------------
# Stop Network
# -----------------------------
net.stop()

print("\nNETWORK STOPPED")