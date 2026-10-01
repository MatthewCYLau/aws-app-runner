from collections import OrderedDict
from functools import wraps


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def contains(self, key):
        return key in self.cache


def lru_cache_custom(maxsize: int = 128):
    """Decorator factory that wraps a function with a custom LRUCache."""
    cache = LRUCache(capacity=maxsize)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a hashable cache key from positional and keyword arguments
            key = (args, tuple(sorted(kwargs.items())))

            if cache.contains(key):
                return cache.get(key)

            # Compute and store result on cache miss
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result

        # Expose cache instance on wrapper function for inspection/clearing
        wrapper.cache = cache
        return wrapper

    return decorator
