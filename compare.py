"""
=========================================================
Experiment Comparison Report
compare.py
=========================================================

Responsibilities

1. Compare baseline vs optimized forwarding table
2. Measure unicast optimization
3. Measure multicast optimization
4. Generate final experiment report
=========================================================
"""


import json


from redis_client import get_redis


from config import *



# =========================================================
# Redis
# =========================================================

r = get_redis()



# =========================================================
# Results
# =========================================================

baseline_table = {}

current_table = {}

multicast_statistics = {}

comparison = {}



# =========================================================
# Redis JSON Loader
# =========================================================

def load_json(key):

    data = r.get(key)


    if data is None:

        return None



    if isinstance(data, bytes):

        data = data.decode()



    try:

        return json.loads(data)


    except Exception:

        return None



# =========================================================
# Load Baseline
# =========================================================

def load_baseline():

    global baseline_table


    baseline_table = {}



    for key in r.keys(

        SNAPSHOT_PREFIX + "*"

    ):


        value = load_json(key)


        if value is None:

            continue



        if isinstance(key, bytes):

            key = key.decode()



        mac = key.replace(

            SNAPSHOT_PREFIX,

            ""

        )


        baseline_table[mac] = value



    print(

        f"[COMPARE] Baseline Entries: "

        f"{len(baseline_table)}"

    )



# =========================================================
# Load Optimized Cache
# =========================================================

def load_current_table():

    global current_table


    current_table = {}



    for key in r.keys(

        MAC_PREFIX + "*"

    ):


        value = load_json(key)


        if value is None:

            continue



        if isinstance(key, bytes):

            key = key.decode()



        mac = key.replace(

            MAC_PREFIX,

            ""

        )


        current_table[mac] = value



    print(

        f"[COMPARE] Current Entries: "

        f"{len(current_table)}"

    )



# =========================================================
# Load Multicast Stats
# =========================================================

def load_multicast():

    global multicast_statistics



    multicast_statistics = load_json(

        MULTICAST_STATS_PREFIX + "stats"

    )



    if multicast_statistics is None:


        multicast_statistics = {}

        print(

            "[COMPARE] No multicast statistics"

        )


    else:

        print(

            "[COMPARE] Multicast statistics loaded"

        )



# =========================================================
# Initialize
# =========================================================

def initialize():

    print()

    print("==============================")

    print(" Experiment Comparison ")

    print("==============================")



    load_baseline()

    load_current_table()

    load_multicast()



# =========================================================
# Unicast Analysis
# =========================================================

def compare_unicast():

    baseline = len(

        baseline_table

    )


    optimized = len(

        current_table

    )


    removed = max(

        baseline - optimized,

        0

    )



    if baseline == 0:

        reduction = 0


    else:

        reduction = round(

            (

                removed /

                baseline

            )

            *

            100,

            2

        )



    comparison.update({

        "baseline_entries": baseline,

        "optimized_entries": optimized,

        "removed_entries": removed,

        "table_reduction": reduction

    })



def ttl_statistics():

    values = [

        entry.get("ttl",0)

        for entry in current_table.values()

    ]


    comparison["average_ttl"] = (

        round(

            sum(values)/len(values),

            2

        )

        if values

        else 0

    )



def priority_statistics():

    values = [

        entry.get("priority",0)

        for entry in current_table.values()

    ]



    comparison["average_priority"] = (

        round(

            sum(values)/len(values),

            2

        )

        if values

        else 0

    )



def forwarding_statistics():

    values = [

        entry.get(

            "forwarding_score",

            0

        )

        for entry in current_table.values()

    ]



    comparison["average_forwarding_score"] = (

        round(

            sum(values)/len(values),

            2

        )

        if values

        else 0

    )



def unicast_efficiency():

    baseline = comparison.get(

        "baseline_entries",

        0

    )


    optimized = comparison.get(

        "optimized_entries",

        0

    )


    if baseline == 0:

        value = 0


    else:

        value = round(

            (

                optimized /

                baseline

            )

            *

            100,

            2

        )



    comparison["unicast_efficiency"] = value



def analyze_unicast():

    compare_unicast()

    ttl_statistics()

    priority_statistics()

    forwarding_statistics()

    unicast_efficiency()



# =========================================================
# Final Report
# =========================================================

def generate_report():

    report = {


        "unicast": comparison,


        "multicast": multicast_statistics

    }



    r.set(

        STATS_PREFIX + "comparison",

        json.dumps(report)

    )



    return report



# =========================================================
# Print
# =========================================================

def print_report():

    print()

    print("========== UNICAST ==========")


    for key,value in comparison.items():

        print(

            f"{key:<25}: {value}"

        )


    print("=============================")



# =========================================================
# Main
# =========================================================

def run_comparison():

    initialize()

    analyze_unicast()

    report = generate_report()

    print_report()


    return report



if __name__ == "__main__":

    run_comparison()