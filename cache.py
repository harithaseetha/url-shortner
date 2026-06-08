from datetime import datetime
from threading import Lock
from typing import Optional


"""A tiny thread-safe in-memory TTL cache.
"""


class SimpleCache:
    """Simple TTL cache with a lock to make operations thread-safe.

    Args:
        ttl_seco    nds: Number of seconds an entry lives in cache before expiring.
        max_items: Maximum number of items to keep; oldest entries are evicted
            when the limit is reached.
    """

    def __init__(self, ttl_seconds: int = 60, max_items: int = 1000):
        self.ttl = ttl_seconds
        self.max = max_items
        self.store: dict = {}
        self.lock = Lock()

    def get(self, key: str) -> Optional[str]:
        """Return the value for ``key`` or ``None`` if missing/expired.

        The method obtains a lock to make reads safe with concurrent writers.
        If an item is expired it is removed and ``None`` is returned.
        """
        with self.lock:
            item = self.store.get(key)
            if not item:
                return None
            value, ts = item
            if datetime.now().timestamp() - ts > self.ttl:
                # expired; remove from cache
                del self.store[key]
                return None
            return value


    # Store a tuple of (value, insertion_time).
    # We use time.time() for a compact float timestamp in seconds.
    def set(self, key: str, value: str) -> None:
        """Store ``value`` under ``key`` with current timestamp.

        If the cache is at capacity, evict the oldest entry (by insertion
        timestamp). This is a simple eviction policy suitable for a demo.
        """
        with self.lock:
            if len(self.store) >= self.max:
                oldest_entry = min(self.store.items(), key=lambda x: x[1][1])[0]
                del self.store[oldest_entry]
            self.store[key] = (value, datetime.now().timestamp())
