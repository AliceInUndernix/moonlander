"""Raw mode: stroke RA*U to see your raw steno instead of words.

What it does:
  RA*U once   -> every dictionary is switched off except dotterel-raw.json,
                 so each stroke comes out as raw steno (-T instead of "the").
  RA*U again  -> every dictionary goes back on or off exactly as it was.

dotterel-raw.json holds only that one stroke. It has to stay on, otherwise
there would be no stroke left to switch raw mode off again.

How Plover finds it: setup.cfg registers raw_toggle() as the command
DOTTEREL_RAW, and dotterel-raw.json maps RA*U to {PLOVER:DOTTEREL_RAW}.
"""

from plover import log

RAW_NAME = "dotterel-raw.json"

# Which dictionaries were on before raw mode: {path: on/off}.
# Kept in memory only, so it is forgotten when Plover closes.
_saved = None


def _is_raw(d):
    """True for the dotterel-raw.json dictionary itself."""
    path = d.path.replace("\\", "/")
    return path.endswith("/" + RAW_NAME) or path.endswith(":" + RAW_NAME)


def raw_toggle(engine, cmdline=""):
    global _saved
    dicts = list(engine.config["dictionaries"])

    if not any(_is_raw(d) for d in dicts):
        log.warning("Dotterel raw mode: %s is not in the dictionary list", RAW_NAME)
        return

    others = [d for d in dicts if not _is_raw(d)]
    # We are in raw mode if we switched it on, or (after Plover was
    # restarted in raw mode) if every other dictionary is off.
    in_raw = _saved is not None or (others and not any(d.enabled for d in others))

    if in_raw:
        # Switch off: put every dictionary back as it was. If Plover was
        # restarted meanwhile we don't know how it was, so switch all on.
        saved = _saved or {}
        new = [d.replace(enabled=saved.get(d.path, True)) for d in dicts]
        _saved = None
    else:
        # Switch on: remember how it was, then leave only dotterel-raw.json on.
        _saved = {d.path: d.enabled for d in dicts}
        new = [d.replace(enabled=_is_raw(d)) for d in dicts]

    engine.config = {"dictionaries": new}
