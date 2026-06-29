# mac_switch_model2.py

"""
Model 2 : Flood Suppression Engine

This model decides whether flooding should be
allowed or suppressed based on:

1. MAC confidence (P_seen)
2. Table occupancy
3. Traffic load
"""

import time

class MACEntry:

    def __init__(self,mac, port):
        self.mac = mac
        self.port = port

         # Number of times MAC seen
        self.seen_count = 0

        # Time when MAC learned
        self.learned_time = time.time()

    def increase_seen_count(self):

        self.seen_count += 1

    def calculate_p_seen(self):

        #MAC confidence probability
        #Higher seen count = higher confidence
        return min(self.seen_count / 10, 1.0)

class DragonflySwitch:

    def __init__(self, capacity=1000):

        # MAC table
        self.mac_table = {}

        # Maximum MAC entries
        self.capacity = capacity

        # Current packets per second
        self.current_pps = 0

        # Maximum traffic supported
        self.max_pps = 100

        self.packet_counter = 0
        self.window_start = time.time()

        # Weights
        self.weights = [0.5, 0.3, 0.2]

    def evaluate_flood_suppression(
        self,
        p_seen,
        occupied
    ):
        """
        Formula:

        FloodScore(mac) =
            w1 * P_seen
          + w2 * (1 - P_table_full)
          + w3 * (1 - P_high_traffic)
        """

        w1, w2, w3 = self.weights
        
        # Table pressure
        p_table_full = occupied / self.capacity

        # Traffic pressure
        p_high_traffic = self.current_pps / self.max_pps

        # Flood score
        flood_score = (
            (w1 * p_seen)
            + (w2 * (1 - p_table_full))
            + (w3 * (1 - p_high_traffic))
        )

        # Decision
        action = (
            "FLOOD ALLOWED"
            if flood_score > 0.55
            else "SUPPRESS FLOOD"
        )

        return round(flood_score, 4), action

    def learn_mac(self, mac, port):
        print(f"\nLearning MAC: {mac} on Port: {port}", flush=True)
    

        if mac in self.mac_table:

            entry = self.mac_table[mac]

            # MAC seen again
            entry.increase_seen_count()

            # Update port if changed
            entry.port = port

        else:

            # Learn new MAC
            self.mac_table[mac] = MACEntry(mac, port)

    def packet_observed(self, mac):

        now = time.time()
        self.packet_counter += 1
        elapsed = now - self.window_start

        if elapsed >= 1:
            self.current_pps = self.packet_counter / elapsed

            self.packet_counter = 0
            self.window_start = now

        if mac in self.mac_table:
            self.mac_table[mac].increase_seen_count()

            

    def show_mac_table(self):

        print("\n========== MAC TABLE ==========\n")

        occupied = len(self.mac_table)
        print("Occupied Entries :", occupied)
        print("Capacity          :", self.capacity)
        print("Current PPS       :", round(self.current_pps, 2))
        print("Max PPS           :", self.max_pps)
        
        for mac, entry in self.mac_table.items():

            p_seen = entry.calculate_p_seen()

            flood_score, action = (
                self.evaluate_flood_suppression(
                    p_seen=p_seen,
                    occupied=occupied
                )
            )

            print(f"MAC Address    : {mac}")
            print(f"Port           : {entry.port}")
            print(f"Seen Count     : {entry.seen_count}")
            print(f"P_seen         : {round(p_seen, 2)}")
            print(f"Flood Score    : {flood_score}")
            print(f"Decision       : {action}")

