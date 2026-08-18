"""Shared lightweight Section container used by both the aisc and en modules."""

from __future__ import annotations


class Section:
    """A generic structural-section property bag.

    Properties are exposed both as attributes (``sec.Ix``) and as a plain
    dict (``sec.as_dict()``). Nothing here assumes a particular unit system
    -- check ``sec.units`` / the source module's docstring for what you're
    getting back (AISC data is imperial: in, in^2, in^3, in^4; EN data is
    cm-based: cm, cm^2, cm^3, cm^4, matching how each source publishes it).
    """

    __slots__ = ("designation", "family", "standard", "units", "source", "_props")

    def __init__(self, designation: str, family: str, standard: str,
                 units: str, source: str, properties: dict):
        self.designation = designation
        self.family = family
        self.standard = standard
        self.units = units
        self.source = source
        self._props = dict(properties)

    def __getattr__(self, name):
        try:
            return self._props[name]
        except KeyError:
            raise AttributeError(
                f"{self.designation!r} ({self.standard}/{self.family}) has no "
                f"property {name!r}. Available: {sorted(self._props)}"
            ) from None

    def __getitem__(self, key):
        return self._props[key]

    def get(self, key, default=None):
        return self._props.get(key, default)

    def as_dict(self) -> dict:
        return dict(self._props)

    def __repr__(self):
        return f"<Section {self.standard}:{self.family} {self.designation} ({self.units})>"
