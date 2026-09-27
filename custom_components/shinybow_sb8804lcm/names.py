"""Channel labels independent of numeric hardware addresses."""


def channel_name(options, kind, number):
    """Return a configured label or the original default."""
    return options.get(f"{kind}_{number}", "").strip() or f"{kind.title()} {number}"


def input_options(options):
    """Keep numeric input order so labels never change routing addresses."""
    return ["Off", *[channel_name(options, "input", i) for i in range(1, 9)]]


def normalize_names(values):
    """Trim names, reset blank values, and reject ambiguous input labels."""
    names = {
        f"{kind}_{i}": channel_name(values, kind, i)
        for kind in ("input", "output") for i in range(1, 9)
    }
    labels = [value.casefold() for value in input_options(names)]
    if len(set(labels)) != len(labels):
        raise ValueError("Input names must be unique and cannot be Off")
    return names
