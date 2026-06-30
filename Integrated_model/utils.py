"""
=========================================================
Unified Intelligent Forwarding Engine
Utility Functions
utils.py
=========================================================

Contains:

1. Dynamic TTL Model
2. Forwarding Stability Score
3. Priority Model
4. JSON Helpers
5. Logging
6. Time Helpers
=========================================================
"""


import os
import json
import math
import time


from config import *



# =========================================================
# Logging Setup
# =========================================================

os.makedirs(
    LOG_DIR,
    exist_ok=True
)



def log_event(message):

    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime()
    )


    with open(
        EVENT_LOG,
        "a"
    ) as f:

        f.write(
            f"[{timestamp}] {message}\n"
        )




def log_engine(message):

    timestamp = time.strftime(
        "%Y-%m-%d %H:%M:%S",
        time.localtime()
    )


    with open(
        ENGINE_LOG,
        "a"
    ) as f:

        f.write(
            f"[{timestamp}] {message}\n"
        )



# =========================================================
# JSON Helpers
# =========================================================


def save_json(filename, data):

    with open(
        filename,
        "w"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )




def load_json(filename):

    if not os.path.exists(filename):

        return {}


    try:

        with open(filename) as f:

            return json.load(f)


    except Exception:

        return {}



# =========================================================
# Dynamic TTL Model
# =========================================================


def calculate_dynamic_ttl(
    tx_count,
    flap_count,
    occupied,
    table_capacity
):


    if tx_count > 0:

        activity = (

            1 +

            math.log(
                1 + tx_count
            )

        )

    else:

        activity = 1



    stability = (

        1 /

        (1 + flap_count)

    )



    occupancy = (

        occupied /

        max(
            table_capacity,
            1
        )

    )



    pressure = max(

        0.1,

        1 - occupancy

    )



    ttl = (

        TTL_BASE *

        ALPHA *

        activity *

        stability *

        pressure

    )



    ttl = max(
        10,
        ttl
    )


    ttl = min(
        ttl,
        TTL_MAX
    )


    return round(
        ttl,
        2
    )



# =========================================================
# Forwarding Stability Score
# =========================================================


def calculate_forwarding_score(
    ttl,
    occupied,
    current_pps,
    table_capacity
):


    ttl_score = min(

        ttl /

        max(TTL_MAX,1),

        1

    )



    table_score = min(

        occupied /

        max(table_capacity,1),

        1

    )



    traffic_score = min(

        current_pps /

        max(MAX_PPS,1),

        1

    )



    score = (

        0.5 * ttl_score

        +

        0.3 * (1 - table_score)

        +

        0.2 * traffic_score

    )



    return round(
        score,
        4
    )



# =========================================================
# Priority Model
# =========================================================


def calculate_priority(
    age,
    ttl,
    tx_count,
    flap_count,
    forwarding_score
):


    ttl = max(
        ttl,
        1
    )


    tx_count = max(
        tx_count,
        1
    )



    priority = (

        0.3 *

        (age / ttl)


        +

        0.2 *

        (1 / tx_count)


        +

        0.3 *

        flap_count


        +

        0.2 *

        (1 - forwarding_score)

    )



    return round(
        priority,
        4
    )



# =========================================================
# Time Helpers
# =========================================================


def current_time():

    return time.time()



def age(last_seen):

    return (

        current_time()

        -

        last_seen

    )



# =========================================================
# TTL Expiry
# =========================================================


def ttl_expired(
    last_seen,
    ttl
):

    return (

        current_time()

        -

        last_seen

    ) >= ttl



# =========================================================
# Eviction Helper
# =========================================================


def lowest_priority_entry(table):


    if not table:

        return None



    return max(

        table,

        key=lambda k:

        table[k].get(

            "priority",

            0

        )

    )