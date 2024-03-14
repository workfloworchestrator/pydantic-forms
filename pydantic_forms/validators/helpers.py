def remove_empty_items(v: list) -> list:
    """Remove Falsy values from list.

    Sees dicts with all Falsy values as Falsy.
    This is used to allow people to submit list fields which are "empty" but are not really empty like:
    `[{}, None, {name:"", email:""}]`

    Example:
    -------
        >>> remove_empty_items([{}, None, [], {"a":""}])
        []

    """
    if v:
        return list(filter(lambda i: bool(i) and (not isinstance(i, dict) or any(i.values())), v))
    return v
