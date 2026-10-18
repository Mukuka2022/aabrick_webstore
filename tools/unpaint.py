"""Take the paint, and the light it threw, off everything not being tiled.

The wall colour was only ever a tracing key, the way the blue was on the
floors. The floor disappears under a tile and so, now, does the wall; but
the ceiling is not a wall and nobody tiles one, and a few rims come out too
narrow for the span tracer to keep. Against a tiled wall those read as a
fault rather than as a key, so whatever is left over after the mask is
repainted as the warm off-white the room was asked for in the first place.

Brightness is kept exactly as it is. Only the colour is taken out, so every
shadow and every downlight on the ceiling survives.

Run this last: it needs the wall mask to know what to leave alone. It takes
the same hint per room as walltrace.py, and must be given the same one, or
it will measure one colour and the tracer will have masked another.
"""
import io
import json
import os

from PIL import Image

import keycolour

SRC = "/mnt/c/Users/HC COMPUTER STORE/Local Sites/visualiser-rooms"
W = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls/walls.json")
B = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/blue/scenes.json")
APP = os.environ.get(
    "AAB_SCENE_OUT",
    "/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"
    "/public/images")

# Must match walltrace.py, room for room and hint for hint. The flag says
# whether to take the wall's light back off the pale things in the room as
# well as the paint itself, and it is a room's own answer rather than
# something measured, because colour cannot settle it.
#
# In these three coral rooms the paint has plainly stained the porcelain
# and the ceilings, and the greenery outside every window sits 46 degrees
# away in hue, so the rule has a clear run. A room whose view shares its
# wall's colour is the opposite case, and the green kitchen was one: the
# garden through its window was the same green as the wall, and no
# threshold tells a sunlit palm from a worktop lit green. Such a room gets
# False here, and that judgement is the whole reason this is a flag.
#
# There was a geometric guard here as well, which skipped any gap the wall
# closed over, on the grounds that what shows through a hole in a wall is
# not a surface the paint has lit. It went, because it cannot tell a mirror
# from a window. A mirror is a hole by that definition, but what it shows
# is the room, coral walls and all, and leaving it alone left a pale coral
# patch in the top corner of the bathroom with tiled wall all around it.
ROOMS = [
    ("Coral and Navy Modern Bathroom.png",      "ensuite",   10.0, True),
    ("Sunlit Coral and Navy Bathroom Spa.png",  "bathroom",  10.0, True),
    ("kitchen-tall-units.webp",                 "kitchen",    5.0, True),
    ("kitchen-and-dining.webp", "kitchen-dining", 10.0, True),
    # No painted walls, so nothing to measure and nothing to leave
    # alone; they are here for the floor pass below.
    ("Modern Navy Living Room Retreat.png",     "living",   None, False),
    ("Modern Navy Patio with Garden Views.png", "patio",    None, False),
]

# The floor is a tracing colour as much as the wall is, and until now
# nothing took it off. Wherever the tile does not reach the blue it
# stays blue: the reflection of the floor in a glass door, the shower
# tray behind its screen, a pixel of the floor's own edge above the
# outline. The tracer is right to stop at a reflection, because a
# reflection is not a floor and tiling it would run the tile up the
# door; but the blue has to go.
#
# What keeps this off the sky, which is the same colour, is distance.
# A reflection of the floor lies against the floor. Sixty pixels above
# the outline reaches the skirting, the foot of a door and the glass
# directly above the floor; the sky in these rooms is hundreds of
# pixels higher, and the one piece of glass that comes near the floor
# is the one showing the floor.
BLUE_NEAR = 60     # pixels above the floor outline this may reach
BLUE_WIN = 12.0    # degrees from the floor's own hue
BLUE_SAT = 0.40    # ...and this much colour, which the sky has not got

FADE = 0.30        # below this the colour is not the paint itself
GROW = 0           # pixels the keep-mask is widened by, see below

# What the paint threw over the rest of the room. A wall painted strongly
# enough to trace lights everything near it: in the ensuite the wall reads
# saturation 0.65 and the basin 0.17, the vanity top 0.15, the ceiling 0.19.
# None of that is paint, so the pass above leaves it, and against a white
# tiled wall every one of them reads pink.
#
# Saturation is what separates it, not hue. The vanity top sits at 22
# degrees and the oak front it stands on at 24, so no hue window can tell
# those two apart; their saturations are 0.15 and 0.73. So the rule is pale
# and bright: a surface that is barely coloured and catching the light is
# porcelain or paintwork wearing the wall's colour, and a surface that is
# strongly coloured is itself. Plants at 0.91 and oak at 0.73 are excluded
# by the same number that includes the basin.
LIT_CAP = 0.35     # more strongly coloured than this and it is its own colour
LIT_SOFT = 0.26    # ...below this the tint comes out whole, and eases between
LIT_VAL = 0.55     # bounced light shows on pale bright surfaces, not in shade
LIT_WIN = 22.0     # degrees; wider than the paint's own, the tint drifts
#                    more, but measured: every surface this is meant to
#                    reach lies within 17 degrees of the paint, and the
#                    greenery outside the windows sits at 48
# the warm off-white the rooms were asked for, as a tint
TINT = (1.000, 0.976, 0.953)

walls = json.load(io.open(W, encoding="utf-8"))
floors = {s["id"]: s for s in json.load(io.open(B, encoding="utf-8"))}


def skirting(pts, w, h):
    """The floor outline as one y per column, as the engine fills it."""
    top = [-1] * w
    for i in range(2, len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        x0, x1 = min(a[0], b[0]), max(a[0], b[0])
        for x in range(x0, min(x1 + 1, w)):
            k = 0.0 if x1 == x0 else (x - x0) / float(x1 - x0)
            y = (a[1] + (b[1] - a[1]) * k if a[0] <= b[0]
                 else b[1] + (a[1] - b[1]) * k)
            y = int(round(y))
            if top[x] < 0 or y < top[x]:
                top[x] = y
    return top


def floor_hue(px, w, h):
    """The floor's own colour, measured where it is all there is."""
    rs = gs = bs = n = 0
    for y in range(int(h * 0.92), h, 2):
        for x in range(int(w * 0.35), int(w * 0.65), 4):
            r, g, b = px[x, y]
            rs += r
            gs += g
            bs += b
            n += 1
    return keycolour.hsv(rs / n, gs / n, bs / n)[0]

for name, slug, hint, lit in ROOMS:
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    w, h = im.size
    px = im.load()

    found = keycolour.paint(px, w, h, hint) if hint is not None else None
    if hint is not None and found is None:
        print("  %-10s no paint near %.0f degrees, left alone" % (slug, hint))
        continue

    keep = bytearray(w * h)          # 1 where a tile will go anyway
    d = walls.get(slug)
    if d:
        step = d["step"]
        for col in d["cols"]:
            x0 = col[0]
            for i in range(1, len(col), 2):
                for y in range(col[i], min(col[i + 1] + 1, h)):
                    row = y * w
                    for x in range(x0, min(x0 + step, w)):
                        keep[row + x] = 1

    # This used to widen the mask by a couple of pixels, from when the spans
    # stopped short of the true edge and a repaint could eat into what the
    # tile was about to cover. walltrace grows its own spans now, so widening
    # again protected a ring that the tile does not reach: not tiled, and not
    # repainted either, so the old paint showed through as a coral line along
    # the top of every wall and down the side of every window.
    #
    # Nothing is lost by not widening. Repainting a pixel the tile covers
    # costs nothing, because the tile is drawn over it.
    grown = bytearray(keep)
    span = range(-GROW, GROW + 1)
    for y in range(h):
        row = y * w
        for x in range(w):
            if not keep[row + x]:
                continue
            for dy in span:
                yy = y + dy
                if yy < 0 or yy >= h:
                    continue
                r2 = yy * w
                for dx in span:
                    xx = x + dx
                    if 0 <= xx < w:
                        grown[r2 + xx] = 1

    fixed = 0
    if found:
      ref, ref_sat, win, ref_val = found
      full = ref_sat * keycolour.LO   # by here it is paint, not light
      ceiling = ref_sat * keycolour.HI  # past here it is something else
      for y in range(h):
        row = y * w
        for x in range(w):
            if grown[row + x]:
                continue
            r, g, b = px[x, y]
            hh, ss, vv = keycolour.hsv(r, g, b)
            if vv < 0.10:
                continue
            off = keycolour.apart(hh, ref)

            # the paint itself, wherever the mask did not reach it. A ramp
            # rather than a cut, so there is no seam where a ceiling meets a
            # wall and the ramp runs out.
            k = 0.0
            if off < win and FADE <= ss <= ceiling:
                k = (ss - FADE) / (full - FADE) if full > FADE else 1.0
                if k > 1.0:
                    k = 1.0

            # and the light it threw on everything pale near it
            if lit and off < LIT_WIN and ss < LIT_CAP and vv > LIT_VAL:
                glow = (1.0 if ss <= LIT_SOFT
                        else (LIT_CAP - ss) / (LIT_CAP - LIT_SOFT))
                if glow > k:
                    k = glow

            if k <= 0.0:
                continue
            L = 0.299 * r + 0.587 * g + 0.114 * b
            px[x, y] = (
                min(255, int(r + (L * TINT[0] - r) * k)),
                min(255, int(g + (L * TINT[1] - g) * k)),
                min(255, int(b + (L * TINT[2] - b) * k)))
            fixed += 1

    # and the floor's own blue, close above the line where the tile
    # stops
    blued = 0
    s = floors.get(slug)
    if s:
        top = skirting(s["floor"], w, h)
        fh = floor_hue(px, w, h)
        for x in range(w):
            t2 = top[x]
            if t2 < 0:
                continue
            # From two pixels below the outline, not from one above it.
            # The topmost row of the polygon is on the boundary, which the
            # engine's inside test does not always take, so a blue pixel
            # sitting exactly on the line was covered by neither the tile
            # nor the repaint. Repainting a pixel the tile does cover is
            # free, because the tile is drawn over it.
            for up in range(-2, BLUE_NEAR + 1):
                y = t2 - up
                if y >= h:
                    continue
                if y < 0:
                    break
                r, g, b = px[x, y]
                hh, ss, vv = keycolour.hsv(r, g, b)
                if (vv < 0.10 or ss < BLUE_SAT
                        or keycolour.apart(hh, fh) >= BLUE_WIN):
                    continue
                L = 0.299 * r + 0.587 * g + 0.114 * b
                px[x, y] = (
                    min(255, int(L * TINT[0])),
                    min(255, int(L * TINT[1])),
                    min(255, int(L * TINT[2])))
                blued += 1

    dst = os.path.join(APP, "scene-%s.jpg" % slug)
    # Colour at full resolution, not half. Every pixel under the mask
    # keeps its paint, because a tile is drawn over it, and a JPEG stores
    # colour in blocks of four: a pale pixel just outside the mask is
    # handed the strongly coloured one inside. Measured on the four rooms,
    # a third to three fifths of the pale pixels touching the mask came
    # back out of the file more coloured than they went in, which is the
    # coral line down the side of the cistern. Subsampling off costs about
    # a fifth of the file and ends it.
    im.save(dst, "JPEG", quality=88, subsampling=0, optimize=True,
            progressive=True)
    if found:
        print("  %-10s hue %3.0f  sat %.2f  window %2.0f   %6d wall"
              " pixels repainted (%.1f%%), %4d of the floor's blue"
              % (slug, ref, ref_sat, win, fixed,
                 100.0 * fixed / (w * h), blued))
    else:
        print("  %-10s no painted walls, %4d of the floor's blue"
              " repainted" % (slug, blued))

print("leftover paint repainted")
