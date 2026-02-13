"""16-bit shift register with probabilistic feedback.

Adapted from Music Thing Modular's Turing Machine by Tom Whitwell.
Creates looping sequences that gradually mutate — not random, not fixed, but evolving.
"""

import random


class TuringRegister:
    """16-bit shift register with probabilistic feedback.

    The bottom `length` bits form a circular loop. On each step:
    1. Read the feedback bit (bit 0 — the bit about to fall off the right end)
    2. Maybe flip it (based on probability)
    3. Shift the loop portion (bits 0 through length-1) right by 1
    4. Write feedback bit to the MSB of the loop (bit length-1)
    5. Upper bits (above the loop) are preserved unchanged
    6. Output the bottom 8 bits (0-255)

    This creates a loop of exactly `length` steps when probability=0.
    """

    def __init__(self, seed=None, length=8):
        self.register = seed if seed is not None else random.getrandbits(16)
        self.length = max(2, min(16, length))
        self.probability = 0.0  # 0.0=locked, 1.0=fully random

    def step(self) -> int:
        """Advance one clock step. Returns current 8-bit output value (0-255)."""
        loop_mask = (1 << self.length) - 1
        loop_bits = self.register & loop_mask

        # 1. Read feedback bit (bit 0 — falls off the right end)
        feedback_bit = loop_bits & 1

        # 2. Probabilistic flip
        if random.random() < self.probability:
            feedback_bit ^= 1

        # 3. Shift loop right by 1
        loop_bits >>= 1

        # 4. Write feedback to MSB of loop
        loop_bits |= (feedback_bit << (self.length - 1))

        # 5. Combine with preserved upper bits
        self.register = (self.register & ~loop_mask) | loop_bits
        self.register &= 0xFFFF

        return self.register & 0xFF

    def get_scale_degree(self, num_degrees=7) -> int:
        """Map the current 8-bit output to a scale degree index."""
        return (self.register & 0xFF) % num_degrees

    def get_state(self) -> int:
        """Return the full 16-bit register value (for save/restore)."""
        return self.register

    def set_state(self, state: int):
        """Restore a saved register state."""
        self.register = state & 0xFFFF

    def set_probability(self, p: float):
        """Set mutation probability. 0.0=locked, 1.0=random."""
        self.probability = max(0.0, min(1.0, p))

    def set_length(self, length: int):
        """Set loop length (2-16)."""
        self.length = max(2, min(16, length))
