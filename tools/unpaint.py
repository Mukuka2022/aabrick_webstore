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

SRC = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/images")
W = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
     "C--Users-HC-COMPUTER-STORE-Local-Sites/"
     "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls/walls.json")
APP = "/home/frappe/frappe-bench/apps/aabrick_webstore/aabrick_webstore"

# Must match walltrace.py, room for room and hint for hint. The flag says
# whether to take the wall's light back off the pale things in the room as
# well as the paint itself, and it is a room's own answer rather than
# something measured, because colour cannot settle it.
#
# In the two pink rooms the paint has plainly stained the porcelain and
# nothing outside the windows is pink, so the rule has a clear run. The
# green kitchen is the opposite: the garden through its window is the same
# green as the wall, and no threshold tells a sunlit palm from a worktop
# lit green, so the rule would strip the colour out of the garden. It also
# has nothing to gain, its fixtures being beige and its ceiling white.
ROOMS = [
    (19, "ensuite",  10.0, True),
    (23, "kitchen",  85.0, False),
    (18, "bathroom", 10.0, True),
]

FADE = 0.30        # below this the colour is not the paint itself
GROW = 2           # pixels the keep-mask is widened by

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

for n, slug, hint, lit in ROOMS:
    im = Image.open("%s/%d.webp" % (SRC, n)).convert("RGB")
    w, h = im.size
    px = im.load()

    found = keycolour.paint(px, w, h, hint)
    if found is None:
        print("  %-10s no paint near %.0f degrees, left alone" % (slug, hint))
        continue
    ref, ref_sat, win = found

    d = walls[slug]
    step = d["step"]
    keep = bytearray(w * h)          # 1 where a tile will go anyway
    seen = bytearray(w * h)          # 1 where you are seeing past the wall
    for col in d["cols"]:
        x0 = col[0]
        for i in range(1, len(col), 2):
            for y in range(col[i], min(col[i + 1] + 1, h)):
                row = y * w
                for x in range(x0, min(x0 + step, w)):
                    keep[row + x] = 1
        # A gap with wall above it and wall below it is a hole in the wall:
        # a window, a mirror, a niche. What shows there is not a surface the
        # paint has lit, it is whatever is on the far side, and a garden has
        # pale sunlit leaves in it like anything else. Colour will not
        # settle that, so the geometry does.
        #
        # This only covers a hole the wall closes over, which is every
        # window in the two rooms the rule runs in. A window that runs down
        # to a worktop has no wall beneath it and is not caught; the kitchen
        # has one, which is part of why the rule is off there.
        for i in range(2, len(col) - 2, 2):
            for y in range(col[i] + 1, min(col[i + 1], h)):
                row = y * w
                for x in range(x0, min(x0 + step, w)):
                    seen[row + x] = 1

    # the walls were sampled with a slight blur, so the mask stops a pixel
    # or two short of the true edge; grow it so a repaint cannot eat into
    # what the tile is about to cover
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

    full = ref_sat * keycolour.LO    # by here it is paint, not bounced light
    ceiling = ref_sat * keycolour.HI  # past here it is something else entirely

    fixed = 0
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
            if (lit and not seen[row + x] and off < LIT_WIN
                    and ss < LIT_CAP and vv > LIT_VAL):
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

    dst = os.path.join(APP, "public/images/scene-%s.jpg" % slug)
    im.save(dst, "JPEG", quality=88, optimize=True, progressive=True)
    print("  %-10s hue %3.0f  sat %.2f  window %2.0f   %6d pixels repainted"
          "  (%.1f%% of the room)"
          % (slug, ref, ref_sat, win, fixed, 100.0 * fixed / (w * h)))

print("leftover paint repainted")
