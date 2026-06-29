import subprocess
import re

SWITCHES = [
    "g0s0",
    "g0s1",
    "g1s0",
    "g1s1",
    "g2s0",
    "g2s1"
]


class FDBMonitor:

    def __init__(self, blacklist=None):

        self.blacklist = blacklist if blacklist else set()

        self.last_seen = {sw: {} for sw in SWITCHES}

        self.flap_counts = {}

    def read_fdb(self):

        result = {sw: {} for sw in SWITCHES}

        for sw in SWITCHES:

            output = None

            try:

                output = subprocess.check_output(
                    f"sudo ovs-appctl fdb/show {sw}",
                    shell=True,
                    text=True
                )

                print(f"\nSWITCH = {sw}")
                print(output)

                for line in output.splitlines():

                    match = re.match(
                        r"\s*(\d+)\s+\d+\s+([0-9a-f:]{17})\s+(\d+)",
                        line.lower()
                    )

                    if match:

                        port = int(match.group(1))
                        mac = match.group(2)
                        age = int(match.group(3))

                        # Hide quarantined MACs
                        if mac in self.blacklist:
                            continue

                        result[sw][mac] = (port, age)

            except Exception as e:

                print(f"\n===== {sw} =====")
                print(f"Error: {e}")

                if output is not None:
                    print(output)

        return result

    def update(self):

        current = self.read_fdb()

        for sw in SWITCHES:

            for mac, (port, age) in current[sw].items():

                if mac not in self.flap_counts:
                    self.flap_counts[mac] = 0

                prev_port = self.last_seen[sw].get(mac)

                if prev_port is None:

                    self.last_seen[sw][mac] = port

                elif prev_port != port:

                    self.flap_counts[mac] += 1

                    print(
                        f"\n[FLAP]"
                        f"\nSWITCH: {sw}"
                        f"\nMAC: {mac}"
                        f"\nFROM port: {prev_port}"
                        f"\nTO port:   {port}"
                    )

                    self.last_seen[sw][mac] = port

        return self.flap_counts