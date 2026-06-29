"""
=========================================================
Unified Intelligent Forwarding Engine
Redis Client
=========================================================

This module provides a single Redis connection that is
shared across the entire project.

Modules using this file:
    - forwarding_engine.py
    - multicast_engine.py
    - dragonfly.py
    - compare.py
"""

import redis

from config import (
    REDIS_HOST,
    REDIS_PORT
)

# Singleton Redis client
_redis_client = None


def get_redis():
    """
    Returns a singleton Redis connection.

    Returns
    -------
    redis.Redis
        Connected Redis client.
    """

    global _redis_client

    if _redis_client is None:

        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        # Verify connection
        try:
            _redis_client.ping()
            print("[REDIS] Connected successfully.")

        except redis.ConnectionError:
            raise RuntimeError(
                "Unable to connect to Redis.\n"
                "Start Redis first:\n"
                "redis-server --daemonize yes"
            )

    return _redis_client


def clear_project_keys():
    """
    Removes only this project's Redis keys.

    Useful before starting a new experiment.
    """

    r = get_redis()

    prefixes = (
        "mac:*",
        "multicast:*",
        "snapshot:*",
        "stats:*"
    )

    for pattern in prefixes:

        keys = r.keys(pattern)

        if keys:
            r.delete(*keys)

    print("[REDIS] Project keys cleared.")