"""Variable-length integer encoding.

This package exposes :func:`encode` and :func:`decode` for protobuf-style
base-128 varints. The public API is intentionally tiny: encode an integer
to a bytes object, decode one from a byte buffer, and report how many bytes
were consumed so callers can continue reading a stream.
"""

from .core import decode, encode

__all__ = ["encode", "decode"]
