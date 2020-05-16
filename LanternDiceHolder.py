#!/usr/bin/env python3
from solid import *
from solid.utils import *
import pathlib
import math

use("rounded/roundCornersCube.scad")

VISUALISE = True

SQ = 16

PATTERNS = [
    [
        """Plus
       .X.
       XXX
       .X.
    """,
        """T
       X.
       XX
       X.
    """,
        """L
       XX
       X.
       X.
    """,
        """Straight
       X
       X
       X
    """,
    ],
    [
        """C
       XX
       X.
       XX
    """,
        """Square
       XX
       XX
    """,
        """Zig
       .X
       XX
       X.
    """,
        """Small-L
       .X
       XX
    """,
    ],
]

STACK_H = 14.5
WALL = 2
COVER_H = 0.6
COVER_EDGE = 1

TRAY_W = 136
TRAY_D = 52
TRAY_H = STACK_H + WALL

HOLD_LEFT = 0
HOLD_CENTER = 1

FINGER_W = 20

C_EXTRA_SPACING = 1


def charcount(txt, c):
    ret = 0
    while txt.startswith(c):
        ret += 1
        txt = txt[1:]
    return ret, txt


def genshape(txt):
    lines = txt.split()
    linei = 0
    maxwidth = 0
    bits = []
    shapename = None
    blanking_square = translate([-COVER_EDGE / 2, -COVER_EDGE / 2, -COVER_EDGE / 2])(
        cube([SQ + COVER_EDGE, SQ + COVER_EDGE, STACK_H])
    )
    cover_blankers = []
    for line in lines:
        if shapename is None:
            shapename = line.strip()
            continue
        linei += 1
        offset, line = charcount(line, ".")
        width, line = charcount(line, "X")
        rightoffset, line = charcount(line, ".")
        if shapename == "C" and linei == 1:
            backdst = linei * SQ + C_EXTRA_SPACING
            depth = SQ + C_EXTRA_SPACING
        elif shapename == "C" and linei == 3:
            backdst = linei * SQ
            depth = SQ + C_EXTRA_SPACING
        else:
            backdst = linei * SQ
            depth = SQ
        linecube = back(backdst)(
            right(offset * SQ)(cube([width * SQ, depth, STACK_H + 1]))
        )
        maxwidth = max((offset + width), maxwidth)
        bits.append(linecube)
        if offset:
            covercube = back(linei * SQ)(
                translate([-COVER_EDGE / 2, -COVER_EDGE / 2, -0.1])(
                    cube([offset * SQ + COVER_EDGE, SQ + COVER_EDGE, COVER_H + 1])
                )
            )
            cover_blankers.append(covercube)
        if rightoffset:
            covercube = back(linei * SQ)(
                translate(
                    [-COVER_EDGE / 2 + (offset + width) * SQ, -COVER_EDGE / 2, -0.1]
                )(cube([rightoffset * SQ + COVER_EDGE, SQ + COVER_EDGE, COVER_H + 1]))
            )
            cover_blankers.append(covercube)

    fullcovercube = back(linei * SQ)(
        translate([COVER_EDGE / 2, COVER_EDGE / 2, 0])(
            cube([SQ * (maxwidth) - COVER_EDGE, linei * SQ - COVER_EDGE, COVER_H])
        )
    )
    cover = fullcovercube - union()(*cover_blankers)
    if offset == rightoffset:
        hold = HOLD_CENTER
    elif offset < rightoffset:
        hold = HOLD_LEFT
    else:
        raise ValueError("Offset unexpected")
    ret = forward(linei * SQ)(union()(*bits))

    return (
        ret,
        {
            "width": maxwidth * SQ,
            "height": linei * SQ,
            "holdpos": hold,
            "name": shapename,
            "cover": forward(linei * SQ)(cover),
        },
    )


def gencuts(count):
    cut = translate([-CUT_W / 2, -FOOT_D / 2, (FOOT_H - CUT_H) / 2])(
        cube([CUT_W, CUT_D, CUT_H])
    )
    angle = math.degrees(math.asin(CUT_SPACE / (FOOT_D / 2)))
    offset = (angle * (count - 1)) / 2
    o = rotate([0, 0, offset])(cut)
    for i in range(count - 1):
        o += rotate([0, 0, offset - (angle * (i + 1))])(cut)
    return o


def gentray(pattern):
    tray = roundedCube([TRAY_W, TRAY_D, TRAY_H], 3, True)
    allparts = []
    total_w = 0
    max_d = 0
    inserts = []
    for parttxt in pattern:
        part, info = genshape(parttxt)
        total_w += info["width"]
        max_d = max(max_d, info["height"])
        allparts.append((part, info))
        inserts.append(info)
    spacing = (TRAY_W - total_w) / 5
    if spacing < 1.4:
        raise ValueError("Shape spacing is too small! %s" % spacing)
    bottom_spacing = (TRAY_D - max_d) / 2
    nextspace = spacing
    for part, info in allparts:
        tray = tray - forward(bottom_spacing)(up(WALL)(right(nextspace)(part)))
        if info["holdpos"] == HOLD_LEFT:
            fx = nextspace + (SQ / 2)
        elif info["holdpos"] == HOLD_CENTER:
            fx = nextspace + (info["width"] / 2)

        finger = cylinder(d=FINGER_W, h=TRAY_H + 1)
        if info["name"] == "Straight":
            finger = forward(TRAY_D / 2)(right(TRAY_W)(finger))
        elif info["name"] == "Zig":
            finger = right(nextspace + FINGER_W / 2)(finger)
        else:
            finger = right(fx)(finger)
        tray = tray - finger
        print(info["name"], spacing, nextspace, fx, total_w)
        nextspace += spacing + info["width"]
    return tray, inserts


def main():
    # shape, dimensions = genshape(PATTERNS[1][0])
    # saveasscad(shape, "-test")
    # saveasscad(dimensions["cover"] + shape.set_modifier("#"), "-A")
    # saveasscad(gentray(PATTERNS_A), "-A")
    # saveasscad(gentray(PATTERNS_B), "-B")
    for t in range(2):
        tray, inserts = gentray(PATTERNS[t])
        saveasscad(tray, "-{}".format(t))
        for insert in inserts:
            saveasscad(insert["cover"], "-cover-{}".format(insert["name"]))


def saveasscad(obj, extra=""):
    fn = pathlib.Path(__file__)
    outfn = fn.parent / (fn.stem + extra + ".scad")
    scad_render_to_file(obj, outfn, file_header="$fn = 250;\n")


if __name__ == "__main__":
    main()
