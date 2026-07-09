"""
Statistical distribution helpers.
All functions return a non-negative integer count drawn from the
configured distribution, clamped to [min, max].
"""

import numpy as np
from typing import Any


class Distributions:
    def __init__(self, seed: int):
        self.rng = np.random.default_rng(seed)

    def sample(self, config: dict[str, Any]) -> int:
        """
        Draw a single integer sample from the distribution described by config.
        Supported dists: negative_binomial, lognormal, zipf, beta (returns float).
        """
        dist = config["dist"]

        if dist == "negative_binomial":
            val = self.rng.negative_binomial(config["n"], config["p"])

        elif dist == "lognormal":
            val = int(self.rng.lognormal(config["mean"], config["sigma"]))

        elif dist == "zipf":
            # numpy zipf can return very large values; clamp aggressively
            val = int(self.rng.zipf(config["a"]))

        elif dist == "beta":
            # Returns a float in (0, 1) — used for rates (CTR, CVR, etc.)
            return float(self.rng.beta(config["a"], config["b"]))

        else:
            raise ValueError(f"Unknown distribution: {dist}")

        lo = config.get("min", 0)
        hi = config.get("max", 10_000)
        return int(np.clip(val, lo, hi))

    def bernoulli(self, p: float) -> bool:
        """Return True with probability p."""
        return bool(self.rng.random() < p)

    def randint(self, lo: int, hi: int) -> int:
        """Uniform integer in [lo, hi]."""
        return int(self.rng.integers(lo, hi + 1))

    def uniform(self, lo: float, hi: float) -> float:
        """Uniform float in [lo, hi]."""
        return float(self.rng.uniform(lo, hi))

    def choice(self, options: list) -> Any:
        """Pick one item uniformly at random."""
        return options[int(self.rng.integers(0, len(options)))]

    def choices(self, options: list, k: int) -> list:
        """Pick k items uniformly at random (with replacement)."""
        indices = self.rng.integers(0, len(options), size=k)
        return [options[i] for i in indices]

    def sample_count(self, config: dict[str, Any]) -> int:
        """Convenience alias — always returns an int >= 0."""
        return self.sample(config)

    def random_float(self, lo: float, hi: float, decimals: int = 2) -> float:
        return round(self.uniform(lo, hi), decimals)
