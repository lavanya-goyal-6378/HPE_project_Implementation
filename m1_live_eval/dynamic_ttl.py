
#first we are creating a mac entry object to store information like tx_count
# flap_count and ttl to be stored in mac table 

import time
import math

import math


def calculate_dynamic_ttl(
    tx_count, flap_count, occupied, capacity=1000, ttl_base=300, alpha=0.5
):
    """Computes dynamic TTL for an entry.

    Formula: TTL(mac) = TTL_base * alpha * F_activity * F_stability * F_pressure
    """
    # 1. Activity Factor (Higher tx_count -> stays longer)
    if tx_count >= 16:
        f_activity = 1 + math.log(1 + tx_count)
    else:
        f_activity = 1
    
    # 2. Stability Factor (Flapping MAC -> shrinks fast)
    f_stability = 1 / (1 + flap_count)

    # 3. Table Pressure Factor (Full table -> shrinks to free space)
    occupancy_ratio = occupied / capacity
    f_pressure = 1 - occupancy_ratio

    # Composite TTL Calculation
    ttl = ttl_base * alpha * f_activity * f_stability * f_pressure

    return round(ttl, 2)



if __name__ == "__main__":

    switch = DragonflySwitch()

    #case 1 : Active and stable mac
    for i in range(30):
        switch.learn_mac(
            mac = "AA:BB:CC:DD",
            port =1
        )
    
    ports = [1,2,3,1,4,2]
    
    for p in ports:

        switch.learn_mac(
            mac = "11:22:33:44", 
            port =p
        )
    switch.show_mac_table()

