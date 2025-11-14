import pydantic.version

PYDANTIC_VERSION = pydantic.version.version_short()


def assert_equal_ignore_key(expected, actual, ignore_keys):
    def deep_remove_keys(d, keys_to_ignore):
        if isinstance(d, dict):
            return {k: deep_remove_keys(v, keys_to_ignore) for k, v in d.items() if k not in keys_to_ignore}
        if isinstance(d, list):
            return [deep_remove_keys(i, keys_to_ignore) for i in d]
        return d

    stripped_expected = deep_remove_keys(expected, ignore_keys)
    stripped_actual = deep_remove_keys(actual, ignore_keys)

    assert stripped_expected == stripped_actual, f"Expected {stripped_expected}, but got {stripped_actual}"
