"""Protobuf-style variable-length integer encoding.

A varint stores an unsigned integer seven bits at a time. Each byte carries
seven payload bits in the low positions and a continuation bit in the high
position. The final byte has its continuation bit clear. This makes small
numbers take one byte and larger numbers take more, which is useful for
length-prefixed records and sparse identifiers.

We accept any non-negative Python ``int``. Negative values are rejected
rather than wrapped because a two's-complement varint has no fixed width and
would need an arbitrary-precision convention that protobuf does not define.
"""

from __future__ import annotations

__all__ = ["encode", "decode"]


# The continuation bit is the most significant bit of each byte.
_CONTINUATION_BIT = 0x80
# The payload mask keeps the low seven bits of each byte.
_PAYLOAD_MASK = 0x7F


def encode(value: int) -> bytes:
    """Return the protobuf-style varint encoding of ``value``.

    ``value`` must be a non-negative integer. The result is a ``bytes``
    object whose length is between one and ten bytes for values that fit in
    64 bits, and longer only for values that exceed that range.

    Raises ``TypeError`` if ``value`` is not an integer and ``ValueError``
    if it is negative.
    """
    if not isinstance(value, int):
        raise TypeError(f"value must be an int, got {type(value).__name__}")
    if value < 0:
        raise ValueError("value must be non-negative")

    out = bytearray()
    while True:
        # Take the low seven bits. If anything remains above them, set the
        # continuation bit so the decoder knows to keep reading.
        chunk = value & _PAYLOAD_MASK
        value >>= 7
        if value:
            out.append(chunk | _CONTINUATION_BIT)
        else:
            out.append(chunk)
            break
    return bytes(out)


def decode(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode a varint from ``data`` starting at ``offset``.

    Returns a ``(value, length)`` tuple, where ``length`` is the number of
    bytes consumed. The caller can advance ``offset`` by ``length`` to read
    the next value from the same buffer.

    ``data`` may be any object that supports indexing and slicing, such as
    ``bytes``, ``bytearray``, or ``memoryview``. ``offset`` must be a
    non-negative integer within the buffer.

    Raises ``TypeError`` for unsupported input types, ``ValueError`` for a
    bad offset, ``IndexError`` if the buffer ends before the varint is
    complete, and ``ValueError`` if the varint is longer than ten bytes
    (the maximum for a 64-bit value).
    """
    if not isinstance(offset, int):
        raise TypeError(f"offset must be an int, got {type(offset).__name__}")
    if offset < 0:
        raise ValueError("offset must be non-negative")

    try:
        length = len(data)
    except TypeError as exc:
        raise TypeError(
            f"data must support len(), got {type(data).__name__}"
        ) from exc

    if offset > length:
        raise ValueError("offset is past the end of the buffer")

    value = 0
    shift = 0
    consumed = 0
    while True:
        if offset + consumed >= length:
            raise IndexError("buffer ended before the varint was complete")
        byte = data[offset + consumed]
        if not isinstance(byte, int):
            # memoryview yields ints, but a generic sequence might not.
            raise TypeError("data elements must be integers")
        consumed += 1
        value |= (byte & _PAYLOAD_MASK) << shift
        if not (byte & _CONTINUATION_BIT):
            break
        shift += 7
        if consumed >= 10:
            # A 64-bit value needs at most ten bytes. More than that means
            # the stream is malformed or the number does not fit.
            raise ValueError("varint is longer than ten bytes")
    return value, consumed
