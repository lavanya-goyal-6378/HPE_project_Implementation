import time

from eviction_scoring_engine import (
    calculate_eviction_score
)


class MACEntry:

    def __init__(self, mac, port, tx_count):

        self.mac = mac
        self.port = port

        self.tx_count = tx_count
        self.flap_count = 0
        self.last_seen = time.time()


class MACTableManager:

    def __init__(self):

        self.mac_table = {}

        self.MAX_MAC_ENTRIES = 10

    def learn_mac(self, mac, port, tx_count):

        now = time.time()

        if mac in self.mac_table:

            entry = self.mac_table[mac]

            if entry.port != port:

                entry.flap_count += 1

                print(
                    f"\n[FLAP] "
                    f"{mac} "
                    f"{entry.port}->{port}"
                )

                entry.port = port

            entry.tx_count = tx_count

            entry.last_seen = now

        else:

            if len(self.mac_table) >= self.MAX_MAC_ENTRIES:

                self.evict_entry()

            self.mac_table[mac] = MACEntry(
                mac,
                port,
                tx_count
            )

    def evict_entry(self):

        now = time.time()

        victim = None

        highest_score = -1

        print("\n===== EVICTION =====")

        for mac, entry in self.mac_table.items():

            age = now - entry.last_seen

            score = calculate_eviction_score(
                age,
                entry.tx_count,
                entry.flap_count
            )

            print(
                f"{mac} | "
                f"TX={entry.tx_count} | "
                f"FLAPS={entry.flap_count} | "
                f"SCORE={score}"
            )

            if score > highest_score:

                highest_score = score

                victim = mac

        print(f"\nEVICTING {victim}")

        del self.mac_table[victim]

    def show(self):

        print("\n===== MAC TABLE =====")

        for e in self.mac_table.values():

            print(
                f"{e.mac} | "
                f"Port={e.port} | "
                f"TX={e.tx_count} | "
                f"Flaps={e.flap_count}"
            )