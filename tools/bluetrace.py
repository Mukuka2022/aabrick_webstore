"""Trace the floor off the blue, and rebuild the scenes from it.

Mukuka painted the floors a flat blue, which turns tracing from a judgement
into a measurement: a pixel is floor if it is that blue, and the outline is
where the blue stops. No running means, no spike filing, no arguing with a
cupboard that happens to be the colour of a floor.

The blue is also what carries the light. The engine shades each tile by the
floor's own luminance against its mean, so a floor that is one flat colour
everywhere leaves pure lighting behind: every shadow under a sofa, every pool
of light from a window, with nothing of the old floor's own pattern mixed in.
That is why the tiles sit in the room rather than on top of it.
"""

import io
import json
import os

from PIL import Image, ImageDraw, ImageFilter

SRC = "/mnt/c/Users/HC COMPUTER STORE/Local Sites/visualiser-rooms"
OUT = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/blue")
APPIMG = os.environ.get(
    "AAB_SCENE_OUT",
    "/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"
    "/public/images")

# file, id, label, how far back the furthest floor is in metres
ROOMS = [
    # file, id, label, how far back the furthest floor is in metres. The
    # depths are the ones written into the prompts the rooms were generated
    # from, so the camera follows from the room rather than from a guess.
    #
    # Two of the nine that came in are not here. The second kitchen was lit
    # by strips under its wall units, which wash coral down the cabinet
    # fronts until a fifth of its wall mask lands on the dishwasher and the
    # oak, against three per cent for this one. The second ensuite and the
    # shower room traced perfectly well; Mukuka did not want them.
    ("Coral and Navy Modern Bathroom.png",
     "ensuite",  "Ensuite",      4.5),
    ("Sunlit Coral and Navy Bathroom Spa.png",
     "bathroom", "Bathroom",     5.0),
    ("Natural Light Modern Pink and Blue Kitchen.png",
     "kitchen",  "Kitchen",      5.0),
    ("Modern Navy Living Room Retreat.png",
     "living",   "Living room",  8.0),
    ("Modern Navy Patio with Garden Views.png",
     "patio",    "Veranda",     10.0),
]

STEP = 5
SPIKE = 15         # columns either side that a column is judged against
SLO = 0.40         # of the floor's own saturation, at least. See blue_test.

# The lens. This is the tangent of half the field of view across the frame,
# and everything in the room is scaled by it: it fixes the horizon, the
# horizon fixes how many pixels a metre is worth, and that fixes how big a
# tile is drawn, on the floor and on the walls alike.
#
# It was 0.49495, a 53 degree lens, and it was an assumption rather than a
# measurement. These rooms are rendered far wider than that, and the error
# showed up as tiles about 1.7 times too large: the kitchen's back wall came
# out 2.31 metres wide against the 4 it was asked for, its ceiling 1.61
# metres above the floor, and the joints fell below a pixel so a tiled wall
# read as one stretched slab.
#
# 0.778 is a 76 degree lens, and it comes from two measurements that agree.
# The feet of the left and right walls are parallel in the room, so in the
# picture they meet on the horizon; fitting them to the upper edge of the
# floor outline, and ignoring whatever stands in front of them, puts the
# kitchen's lens at 927, the veranda's at 873 and the bathroom's at 845.
# And at 930 the three indoor rooms come out with ceilings of 2.75 to 2.85
# metres above the floor, where 1462 had them at 1.75 and anything below
# 870 puts them past three.
HALF_FOV = 0.778
GRACE = 10         # pixels of not-blue the walk may cross before giving up.
                   # It has to cross something: a glossy floor reflects the
                   # pink vanity above it and that reflection is genuinely
                   # not blue. Swept against every room, 10 moves no floor
                   # top by more than 6px, and 20 takes the bathroom from
                   # 535 to 386 by stepping over a skirting board.


def hsv(r, g, b):
    """Hue in degrees, saturation and value, all from 0."""
    mx, mn = max(r, g, b), min(r, g, b)
    v = mx / 255.0
    d = mx - mn
    if mx == 0 or d == 0:
        return 0.0, 0.0, v
    s = d / float(mx)
    if mx == r:
        h = 60.0 * (((g - b) / float(d)) % 6)
    elif mx == g:
        h = 60.0 * (((b - r) / float(d)) + 2)
    else:
        h = 60.0 * (((r - g) / float(d)) + 4)
    return h, s, v


def blue_test(ref_hue, ref_sat=None):
    """Is this the painted floor, in sun, in shade, or under a lamp.

    Hue, not colour. The veranda is the case that forces it: the near half is
    in the shade of its own roof and the far half is in full sun, and as
    colours those two are far enough apart that a test anchored on one throws
    the other away, which left the back half of the floor untiled. Their hue
    is the same to within a couple of degrees, because sunlight changes how
    bright and how strong a blue is and not which blue it is.

    A saturation floor keeps the white walls out, since white has no hue to
    compare, and a value floor keeps the noise in the black of a window out.

    That saturation floor has to be relative to the floor's own blue. Fixed
    at 0.12 it let the veranda climb its own doors: the floor is painted at
    saturation 0.70, the glass returns a washed-out version of it, and the
    near-neutral darks in the door frames measure 0.14 to 0.23, which clears
    a fixed 0.12 easily. The walk went up through the threshold, found blue
    all the way, and the tiling climbed the glass with it.

    Against each room's own floor there is room between the two. Honest
    floor never falls below 0.53 of its reference in any of these rooms, and
    0.38 on the veranda where half of it is in the shade of its own roof;
    the reflections sit at 0.20 to 0.33. SLO is set at 0.40.
    """
    weak = 0.12 if ref_sat is None else ref_sat * SLO

    def test(r, g, b):
        h, s, v = hsv(r, g, b)
        if s < weak or v < 0.05:
            return False
        d = abs(h - ref_hue)
        if d > 180:
            d = 360 - d
        return d < 28
    return test


def trace(path):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    w, h = im.size
    px = im.filter(ImageFilter.GaussianBlur(0.6)).load()

    # The floor's own colour, from the bottom middle where it is all there is.
    rs = gs = bs = 0
    n = 0
    for y in range(int(h * 0.92), h, 2):
        for x in range(int(w * 0.35), int(w * 0.65), 4):
            r, g, b = px[x, y]
            rs += r; gs += g; bs += b; n += 1
    fh, fs, fv = hsv(rs / n, gs / n, bs / n)
    is_blue = blue_test(fh, fs)

    tops = []
    for x in range(0, w, STEP):
        xs = min(x, w - 1)
        # find the floor at the bottom of this column, if it is there at all
        start = None
        for y in range(h - 1, int(h * 0.45), -1):
            if is_blue(*px[xs, y]):
                start = y
                break
        if start is None:
            tops.append((xs, h - 1))
            continue
        miss = 0
        top = start
        for y in range(start, 0, -1):
            if is_blue(*px[xs, y]):
                top = y
                miss = 0
            else:
                miss += 1
                if miss > GRACE:
                    break
        tops.append((xs, top))
    return tops, (w, h)


def despike(tops):
    """Pull back a column that has climbed far above its neighbours.

    A glossy floor reflects, and a reflection of a blue floor is as blue as
    the floor. Where the veranda meets its sliding doors the walk up each
    column finds blue in the glass and keeps going, so the outline throws
    spikes a hundred and fifty pixels up into the doors, one to three
    columns wide, and the tiling climbs the glass with it.

    The error only ever goes one way. A column can be wrong by reaching too
    far back, never by stopping too early, because stopping early is what
    an object standing on the floor genuinely looks like. So this only ever
    pulls a column back towards its neighbours and never pushes one out:
    a spike is flattened, a sofa still occludes what it occludes, and a
    real step like the base of a column, which is sustained across many
    columns rather than one, carries the median with it and survives.
    """
    ys = [y for _, y in tops]
    n = len(ys)
    half = SPIKE // 2
    out = []
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        mid = sorted(ys[a:b])[(b - a) // 2]
        out.append((tops[i][0], max(ys[i], mid)))
    return out


def thin(points, tol=1.6):
    if len(points) < 3:
        return points
    keep = [points[0]]
    for i in range(1, len(points) - 1):
        ax, ay = keep[-1]
        bx, by = points[i]
        cx, cy = points[i + 1]
        dx, dy = cx - ax, cy - ay
        n = (dx * dx + dy * dy) ** 0.5
        d = abs(dy * bx - dx * by + cx * ay - cy * ax) / n if n else 0
        if d > tol:
            keep.append(points[i])
    keep.append(points[-1])
    return keep


def overlay(path, tops, size, dst, label):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    w, h = size
    poly = [(0, h - 1)] + [(x, y) for x, y in tops] + [(w - 1, h - 1)]
    d.polygon(poly, fill=(255, 140, 0, 90))
    d.line([(x, y) for x, y in tops], fill=(255, 255, 0, 255), width=2)
    d.text((16, 16), label, fill=(255, 255, 0, 255))
    im.save(dst, "JPEG", quality=86)


def main():
    for p in (OUT,):
        if not os.path.isdir(p):
            os.makedirs(p)

    scenes = []
    for name, slug, label, depth in ROOMS:
        src = os.path.join(SRC, name)
        tops, (w, h) = trace(src)
        raw = tops
        tops = despike(tops)
        moved = sum(1 for a, b in zip(raw, tops) if a[1] != b[1])
        worst = max([b[1] - a[1] for a, b in zip(raw, tops)] or [0])
        tops = thin(tops)

        dst = os.path.join(APPIMG, "scene-%s.jpg" % slug)
        with Image.open(src) as raw:
            raw.convert("RGB").save(dst, "JPEG", quality=88, optimize=True,
                                    progressive=True)

        focal = int(round(w / (2 * HALF_FOV)))
        height = 1.45
        top = min(y for _, y in tops if y < h - 1)
        horizon = int(round(top - focal * height / depth))

        pts = [[0, h - 1], [w - 1, h - 1]]
        for x, y in reversed(tops):
            pts.append([int(x), int(y)])

        scenes.append({
            "id": slug, "label": label,
            "image": "/assets/aabrick_webstore/images/scene-%s.jpg" % slug,
            "horizon": horizon, "cx": w // 2, "focal": focal,
            "height": height, "floor": pts,
        })
        overlay(src, tops, (w, h), os.path.join(OUT, "%s.jpg" % slug),
                "%s  %d points  floor top %d  horizon %d"
                % (label, len(pts), top, horizon))
        empty = sum(1 for _, y in tops if y >= h - 1)
        print("  %-16s %dx%d  %3d points  top %4d  horizon %4d  %d empty"
              "   %d columns pulled back, worst %d px"
              % (slug, w, h, len(pts), top, horizon, empty,
                 moved, worst))

    with io.open(os.path.join(OUT, "scenes.json"), "w", encoding="utf-8") as f:
        json.dump(scenes, f)
    print("traced off the blue")
    # This has just written every scene image out again from its original
    # photograph, which throws away whatever unpaint.py did to them. That is
    # fine when the three run in order and a trap when they do not: run
    # bluetrace alone to re-do a floor and the rooms quietly go back to
    # wearing their tracing paint, with coral ceilings and coral basins, and
    # nothing anywhere says so.
    print("")
    print("  the scenes are back to their original paint. Run walltrace.py")
    print("  and then unpaint.py, or the rooms ship with it still on them.")


main()
