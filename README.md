# tiny-variable-length-integer-varint

Encode and decode non-negative integers as protobuf-style base-128 varints.

```python
from tiny_variable_length_integer_varint import decode, encode

encoded = encode(300)          # b'\xac\x02'
value, length = decode(encoded)  # (300, 2)

# Read from a stream by advancing the offset yourself.
buffer = encoded + encode(7)
first, n = decode(buffer, offset=0)
second, m = decode(buffer, offset=n)
assert (first, second) == (300, 7)
```

## Why this exists

Length-prefixed formats need a compact integer encoding that does not fix a
width. A varint uses one byte for values below 128 and grows only as needed,
which keeps small records small while still representing 64-bit identifiers.
The trade-off is that decoding is sequential: you cannot jump to the middle
of a varint without reading the bytes before it, and you must know where one
value ends before you can parse the next. This library therefore returns the
number of bytes consumed rather than assuming the whole buffer is one value.

## The awkward edge

Negative integers are rejected. Protobuf varints are unsigned; a negative
value has no natural finite representation without choosing a two's-complement
width. If you need signed values, apply a zigzag transform before encoding and
reverse it after decoding. The decoder also refuses varints longer than ten
bytes, which is the maximum needed for a 64-bit value, so a corrupt stream
raises ``ValueError`` instead of consuming memory without bound.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

