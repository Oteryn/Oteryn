def positive_id(value):
    """Accept positive integer IDs, but never booleans or coerced strings."""
    return type(value) is int and value > 0
