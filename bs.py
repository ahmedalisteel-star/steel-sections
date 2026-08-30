"""
British-designation hot-rolled shapes: UB, UC, UBP, PFC, RSC.

These five families are the ones a UK/Gulf-market job specifies by their
BS 4-1 serial size ("457 x 191 x 67") while the dimensions themselves are
now published in EN 10365.  Neither ``steelpy`` (AISC only) nor
``eurocodepy`` (IPE/HE and hollow sections only) carries them, so the
properties here come from the DBMSC catalogue -- see
:mod:`steel_sections.dbmsc` for the source, the units and the accuracy
caveat that applies to all of them.

Units: cm-based throughout -- lengths cm, A cm^2, I cm^4, W cm^3, i cm,
torsion constant IT cm^4, warping constant Iw cm^6, mass kg/m -- the same
convention as ``steel_sections.en``. So ``UB("457x191x67").h`` is 45.34, not
453.4.

Usage
-----
>>> import steel_sections as ss
>>> ub = ss.bs.UB("457x191x67")
>>> ub.Iy, ub.Wpl_y, ub.A          # cm^4, cm^3, cm^2
(29380.0, 1471.0, 85.5)
>>> ss.bs.UC("203x203x60").iz      # cm
5.2
>>> ss.bs.PFC("430x100x64").Iy     # cm^4
21870.0
>>> ss.bs.available_ub()[:3]
['1016x305x487', '1016x305x438', '1016x305x393']

Designations may be written with or without the family prefix and with or
without spaces: ``"457x191x67"``, ``"UB 457 x 191 x 67"`` and
``"ub457X191X67"`` are the same lookup.
"""

from __future__ import annotations

from . import dbmsc
from ._common import Section


def UB(designation: str) -> Section:
    """Universal beam, e.g. ``UB("457x191x67")`` (depth x width x kg/m)."""
    return dbmsc.section("UB", designation)


def UC(designation: str) -> Section:
    """Universal column, e.g. ``UC("203x203x60")``."""
    return dbmsc.section("UC", designation)


def UBP(designation: str) -> Section:
    """Universal bearing pile with wide flanges, e.g. ``UBP("305x305x149")``."""
    return dbmsc.section("UBP", designation)


def PFC(designation: str) -> Section:
    """Parallel flange channel, e.g. ``PFC("300x90x41")``.

    The catalogue page that carries the major-axis second moment of area is
    over-printed and unreadable for every row, so ``Iy`` is reconstructed
    from the two published quantities that pin it down -- ``iy**2 * A`` and
    ``Wel_y * h/2`` -- which agree to better than 1% on every size.
    """
    return dbmsc.section("PFC", designation)


def RSC(designation: str) -> Section:
    """Rolled steel channel, e.g. ``RSC("305x102")`` (depth x width, mm)."""
    return dbmsc.section("RSC", designation)


def available_ub() -> list[str]:
    return dbmsc.available("UB")


def available_uc() -> list[str]:
    return dbmsc.available("UC")


def available_ubp() -> list[str]:
    return dbmsc.available("UBP")


def available_pfc() -> list[str]:
    return dbmsc.available("PFC")


def available_rsc() -> list[str]:
    return dbmsc.available("RSC")
