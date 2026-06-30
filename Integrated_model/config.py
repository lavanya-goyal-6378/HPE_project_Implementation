"""
=========================================================
Unified Intelligent Forwarding Engine
Configuration
=========================================================
"""


# =========================================================
# Redis
# =========================================================

REDIS_HOST = "localhost"

REDIS_PORT = 6379



# =========================================================
# Engine
# =========================================================

ENGINE_INTERVAL = 5



# =========================================================
# Table Capacity
# =========================================================

UNICAST_TABLE_CAPACITY = 512



# =========================================================
# TTL Models
# =========================================================
# TTL_BASE = 30 (seconds)
# Set to 30s for demonstration purposes (industry default is 300s).
# At 300s with a 5s cycle, expiry takes 60 cycles (~5 mins)
# which is too long for a live demo. The mathematical model
# is identical — only the timescale changes.
TTL_BASE = 30

TTL_MAX = 60


ALPHA = 0.5



# =========================================================
# Forwarding Score
# =========================================================

MAX_PPS = 1000



# =========================================================
# Priority
# =========================================================

PRIORITY_THRESHOLD = 1.5



# =========================================================
# Eviction
# =========================================================

ENABLE_EVICTION = True



# =========================================================
# Unknown Unicast
# =========================================================

UNKNOWN_UNICAST_THRESHOLD = 0.40



# =========================================================
# Multicast
# =========================================================

MULTICAST_EVENT_CHANNEL = "multicast_events"

MULTICAST_RESULT_KEY = "multicast_results"



# =========================================================
# Logging
# =========================================================

LOG_DIR = "logs"


EVENT_LOG = f"{LOG_DIR}/events.log"


ENGINE_LOG = f"{LOG_DIR}/engine.log"



# =========================================================
# Redis Keys
# =========================================================

MAC_PREFIX = "mac:"

SNAPSHOT_PREFIX = "snapshot:"

STATS_PREFIX = "stats:"

# FIX: separate prefixes so cache and stats
# do not overwrite each other in Redis
MULTICAST_PREFIX = "multicast:cache:"

MULTICAST_STATS_PREFIX = "multicast:stats:"



# =========================================================
# Dragonfly Topology
# =========================================================

NUM_GROUPS = 2


SWITCHES_PER_GROUP = 3


HOSTS_PER_SWITCH = 2


LINK_BW = 1000


LINK_DELAY = "1ms"



# =========================================================
# Derived Values
#
# FIX: generate switch names from NUM_GROUPS and
# SWITCHES_PER_GROUP so the list always matches
# the topology constants above.
#
# FIX: generate host names properly instead of
# repeating the switch list with * HOSTS_PER_SWITCH.
# =========================================================

SWITCHES = [
    f"g{g}_s{s}"
    for g in range(NUM_GROUPS)
    for s in range(SWITCHES_PER_GROUP)
]

HOSTS = [
    f"g{g}_s{s}_h{h}"
    for g in range(NUM_GROUPS)
    for s in range(SWITCHES_PER_GROUP)
    for h in range(1, HOSTS_PER_SWITCH + 1)
]