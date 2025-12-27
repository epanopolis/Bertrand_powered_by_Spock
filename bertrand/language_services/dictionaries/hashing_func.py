import math

def canonical_string(obj, _seen=None):
    """
    Deterministic, *hashable* canonical form for any Python object.

    - Dicts: keys/values canonicalized; items sorted by canonicalized-key repr
    - Sets/frozensets: order-independent via sort of canonicalized elems
    - Tuples/lists: order preserved, tagged to distinguish list vs tuple
    - Floats: normalize -0.0 -> 0.0; NaN/Inf canonicalized
    - Cycles: replaced by a stable ('CYCLE',) sentinel
    - Always returns a structure built only from hashables (tuples, strings,
      ints, floats, bools, None), so it can be used as a dict key.
    """
    if _seen is None:
        _seen = set()

    def _freeze(x):
        # Simple primitives (already hashable, but we tag to avoid collisions across types)
        if x is None:
            return ('none', None)
        if isinstance(x, bool):
            return ('bool', bool(x))
        if isinstance(x, int):
            return ('int', int(x))
        if isinstance(x, float):
            # normalize -0.0 -> 0.0
            if x == 0.0:
                x = 0.0
            if math.isnan(x):
                return ('float', 'NaN')
            if math.isinf(x):
                return ('float', 'Infinity' if x > 0 else '-Infinity')
            return ('float', float(x))
        if isinstance(x, str):
            return ('str', x)
        if isinstance(x, bytes):
            # bytes are hashable; tag to distinguish from str
            return ('bytes', x)

        # Container/cyclic detection
        if isinstance(x, (list, tuple, set, frozenset, dict)):
            oid = id(x)
            if oid in _seen:
                return ('CYCLE',)
            _seen.add(oid)

        # Sequences
        if isinstance(x, (list, tuple)):
            tag = 'tuple' if isinstance(x, tuple) else 'list'
            return (tag, tuple(_freeze(v) for v in x))

        # Sets (order-independent)
        if isinstance(x, (set, frozenset)):
            elems = tuple(sorted((_freeze(v) for v in x), key=repr))
            tag = 'frozenset' if isinstance(x, frozenset) else 'set'
            return (tag, elems)

        # Dicts (order-independent by key)
        if isinstance(x, dict):
            items = [(_freeze(k), _freeze(v)) for k, v in x.items()]
            items.sort(key=lambda kv: repr(kv[0]))
            return ('dict', tuple(items))

        # Objects with state
        if hasattr(x, '__dict__'):
            return ('object', type(x).__name__, _freeze(vars(x)))
        if hasattr(x, '__slots__'):
            slots = tuple(getattr(x, s, None) for s in x.__slots__)
            return ('object', type(x).__name__, _freeze(slots))

        # Fallback: stable repr
        return ('repr', repr(x))

    return _freeze(obj)


def object_hash64(obj) -> int:
    """Convenience: canonicalize then FNV-1a hash of its repr (deterministic)."""
    canon = canonical_string(obj)
    return fnv1a_64_from_string(repr(canon))


def object_hash64_hex(obj) -> str:
    """Hex string form (fixed 16 hex digits)."""
    return f"{object_hash64(obj):016x}"
