"""
Generic / parametric sections that have no single universal designation
standard: solid round bar ("rod"), solid rectangular/flat bar, and
cold-formed lipped C ("cee") and Z ("zed") sections.

Cold-formed member sizes are manufacturer- and project-specific (unlike
hot-rolled IPE/UPN/W-shapes there is no one settled international
designation table), so these are always built parametrically from
dimensions you provide, using the sectionproperties finite-element engine
(https://github.com/robbievanleeuwen/section-properties, MIT).

All results here are **nominal gross section properties** -- straight
geometric integration of the full cross-section. They are NOT the
"effective section" properties used in cold-formed design per AISI S100 /
EN 1993-1-3, which require a separate local-buckling / effective-width
reduction that this module does not perform.

Units: whatever units you pass in for dimensions determine the property
units, e.g. mm in -> mm^2, mm^3, mm^4 out.
"""

from __future__ import annotations

import math
import warnings

from ._common import Section

_UNITS_NOTE = "matches whatever length unit you passed in (length, length^2, length^3, length^4)"


def _analyze(geometry, mesh_size: float):
    from sectionproperties.analysis import Section as SPSection

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        geometry.create_mesh(mesh_sizes=[mesh_size])
        sec = SPSection(geometry)
        sec.calculate_geometric_properties()
        sec.calculate_warping_properties()
    return sec.section_props


def rod(diameter: float) -> Section:
    """Solid round bar. Closed-form -- no meshing needed.

    >>> rod(20).A       # mm^2, for diameter in mm
    314.159...
    """
    d = diameter
    A = math.pi * d ** 2 / 4
    I = math.pi * d ** 4 / 64
    r = math.sqrt(I / A)
    J = math.pi * d ** 4 / 32
    Wel = I / (d / 2)
    Wpl = d ** 3 / 6
    props = {"d": d, "A": A, "Ix": I, "Iy": I, "rx": r, "ry": r,
             "J": J, "Wel": Wel, "Wpl": Wpl, "Zplastic": Wpl}
    return Section(designation=f"ROD{d:g}", family="ROD", standard="generic",
                    units=_UNITS_NOTE, source="closed-form", properties=props)


def flat_bar(width: float, thickness: float) -> Section:
    """Solid rectangular / flat bar. Closed-form -- no meshing needed.

    >>> flat_bar(100, 10).A     # mm^2
    1000.0
    """
    b, t = width, thickness
    A = b * t
    Ix = b * t ** 3 / 12   # bending about the strong (in-plane) axis
    Iy = t * b ** 3 / 12
    props = {
        "b": b, "t": t, "A": A,
        "Ix": Ix, "rx": math.sqrt(Ix / A), "Wel_x": Ix / (t / 2),
        "Iy": Iy, "ry": math.sqrt(Iy / A), "Wel_y": Iy / (b / 2),
        "J": _rect_torsion_constant(b, t),
    }
    return Section(designation=f"FB{width:g}x{thickness:g}", family="FLAT_BAR",
                    standard="generic", units=_UNITS_NOTE, source="closed-form",
                    properties=props)


def _rect_torsion_constant(b: float, t: float) -> float:
    """St. Venant torsion constant for a solid rectangle (b >= t), Roark's approximation."""
    if t > b:
        b, t = t, b
    ratio = b / t
    beta = 1.0 / 3.0 - 0.21 * (t / b) * (1 - (t / b) ** 4 / 12.0) if ratio >= 1 else 1.0 / 3.0
    return beta * b * t ** 3


def cold_formed_cee(d: float, b: float, lip: float, t: float, r_out: float = None,
                     n_r: int = 8) -> Section:
    """Parametric cold-formed lipped C ("cee") section.

    d    -- overall web depth
    b    -- overall flange width
    lip  -- lip length
    t    -- material thickness
    r_out -- outer corner radius (defaults to 2*t if omitted, a common
             cold-forming rule of thumb -- check your mill's actual
             tooling radius for anything but a rough estimate)

    Returns NOMINAL gross properties only (see module docstring for the
    effective-width caveat).
    """
    if r_out is None:
        r_out = 2 * t
    from sectionproperties.pre.library import steel_sections as ss_lib
    geom = ss_lib.cee_section(d=d, b=b, l=lip, t=t, r_out=r_out, n_r=n_r)
    props = _analyze(geom, mesh_size=t ** 2 / 2)
    computed = {
        "d": d, "b": b, "lip": lip, "t": t, "r_out": r_out,
        "A": props.area, "Ix": props.ixx_c, "Iy": props.iyy_c,
        "rx": props.rx_c, "ry": props.ry_c, "J": props.j,
        "cx": props.cx, "cy": props.cy,
    }
    return Section(designation=f"CEE{d:g}x{b:g}x{t:g}", family="COLD_FORMED_C",
                    standard="generic", units=_UNITS_NOTE,
                    source="sectionproperties (MIT), nominal gross properties",
                    properties=computed)


def cold_formed_zed(d: float, b_left: float, b_right: float, lip: float, t: float,
                     r_out: float = None, n_r: int = 8) -> Section:
    """Parametric cold-formed lipped Z ("zed") section.

    d              -- overall web depth
    b_left, b_right -- flange widths on each side (equal for a symmetric Z)
    lip            -- lip length
    t              -- material thickness
    r_out          -- outer corner radius (defaults to 2*t)

    Returns NOMINAL gross properties only (see module docstring).
    """
    if r_out is None:
        r_out = 2 * t
    from sectionproperties.pre.library import steel_sections as ss_lib
    geom = ss_lib.zed_section(d=d, b_l=b_left, b_r=b_right, l=lip, t=t, r_out=r_out, n_r=n_r)
    props = _analyze(geom, mesh_size=t ** 2 / 2)
    computed = {
        "d": d, "b_left": b_left, "b_right": b_right, "lip": lip, "t": t, "r_out": r_out,
        "A": props.area, "Ix": props.ixx_c, "Iy": props.iyy_c,
        "Ixy": props.ixy_c, "Iu_max": props.i11_c, "Iv_min": props.i22_c,
        "rx": props.rx_c, "ry": props.ry_c, "J": props.j,
        "cx": props.cx, "cy": props.cy,
    }
    return Section(designation=f"ZED{d:g}x{b_left:g}_{b_right:g}x{t:g}", family="COLD_FORMED_Z",
                    standard="generic", units=_UNITS_NOTE,
                    source="sectionproperties (MIT), nominal gross properties",
                    properties=computed)
