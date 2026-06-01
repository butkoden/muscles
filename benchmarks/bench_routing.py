from __future__ import annotations

import time

from muscles.core import Itinerary


def run() -> dict:
    router = Itinerary()

    class _DefaultRule:
        name = "default"

        @staticmethod
        def is_match(path, route):
            return path == route

        @staticmethod
        def compile(value):
            return str(value)

    class _VarRule:
        name = "var"

        @staticmethod
        def is_match(path, route):
            return True

        @staticmethod
        def compile(value):
            return str(value)

    router.add_rule(_DefaultRule())
    router.add_rule(_VarRule())

    def _handler(*args, **kwargs):
        return True

    for i in range(1000):
        router.add(f"/api/v1/items/{i}", key=f"api.v1.items.{i}", method="GET", handler=_handler)

    start = time.perf_counter()
    for i in range(1000):
        router.match_with_params(f"/api/v1/items/{i}")
    elapsed = time.perf_counter() - start

    return {
        "routing_match_iterations": 1000,
        "elapsed_seconds": elapsed,
        "per_request_ms": (elapsed / 1000) * 1000,
    }


if __name__ == "__main__":
    print(run())
