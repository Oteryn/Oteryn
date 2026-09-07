def positive_id(value):
    """Accept positive integer IDs, but never booleans or coerced strings."""
    return isinstance(value, int) and value > 0
