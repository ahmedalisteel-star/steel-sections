"""
Japanese hot-rolled shapes to JIS G 3192: wide-flange H shapes and channels.

Steel to JIS G 3101 / G 3106 turns up constantly on Gulf and Asian jobs and
neither upstream table in this package covers it, so these come from the
DBMSC catalogue -- see :mod:`steel_sections.dbmsc` for the source and the
accuracy caveat.

H shapes are keyed by their full rolled size, ``H<h>x<b>x<tw>x<tf>``, because
one nominal series (e.g. "300 x 300") covers five different rollings that
share a nominal size but not a single dimension in common.  Channels keep
the catalogue's own ``<h>x<b>x<t1>`` designation.

Units: cm-based throughout (lengths cm, A cm^2, I cm^4, W cm^3, i cm,
mass kg/m), matching ``steel_sections.en``.  The
catalogue publishes I, i and the elastic modulus for these families; there
is no plastic modulus or torsion column to transcribe.

Usage
-----
>>> import steel_sections as ss
>>> h = ss.jis.H("H300x300x10x15")
>>> h.A, h.Iy, h.Wel_y             # cm^2, cm^4, cm^3
(119.8, 20400.0, 1360.0)
>>> ss.jis.C("C200x80x7.5").Iy     # cm^4
1950.0
>>> ss.jis.available_h()[:2]
['H100x50x5x7', 'H100x100x6x8']
"""

from __future__ import annotations

from . import dbmsc
from ._common import Section


def H(designation: str) -> Section:
    """JIS wide-flange H shape, e.g. ``H("H400x400x13x21")``.

    ``H`` prefix optional; ``"300x300x10x15"`` resolves the same row.
    """
    return dbmsc.section("JIS_H", designation)


def C(designation: str) -> Section:
    """JIS channel, e.g. ``C("C200x80x7.5")`` (depth x width x web, mm)."""
    return dbmsc.section("JIS_C", designation)


#: JIS channels are also commonly written "[200x80x7.5"; keep an alias.
Channel = C


def available_h() -> list[str]:
    return dbmsc.available("JIS_H")


def available_c() -> list[str]:
    return dbmsc.available("JIS_C")
