"""Trace the painted walls, the same way the blue floors were traced.

A wall is given as spans rather than as an outline. A floor is one shape and
an outline describes it; a wall has a window punched through it, a mirror on
it and a shower screen across it, and an outline cannot say "not here". So
each column carries a list of top and bottom pairs, and everything between a
pair is wall.

The geometry needs nothing new. The floor outline is the wall's own skirting,
so the depth of the wall in any column is the depth of the floor directly
below it, which the floor trace already knows. Height up the wall and
distance along it follow from that, and the drawing code cannot tell the
difference between those and the two numbers it uses for a floor.

What separates paint from furniture lives in keycolour.py, including why the
hue is hinted rather than discovered.
"""

import io
import json
import os

from PIL import Image, ImageDraw, ImageFilter

import keycolour

SRC = "/mnt/c/Users/HC COMPUTER STORE/Local Sites/visualiser-rooms"
OUT = ("/mnt/c/Users/HCCOMP~1/AppData/Local/Temp/claude/"
       "C--Users-HC-COMPUTER-STORE-Local-Sites/"
       "6b0e1eff-4cf1-4667-ac17-775c86b627df/scratchpad/walls")

# file, id, roughly what colour the walls were painted, in degrees of hue.
# Pink is about 10 and green about 85; the exact figure is measured, this
# only says which colour in the room is the paint.
ROOMS = [
    # file, id, roughly what colour the walls were painted, in degrees of
    # hue. The bathrooms and the dining room are coral, about 10; the
    # kitchen is a deep red, about 5. The living room and the veranda are
    # not here: their walls were never painted, so there is nothing to
    # trace and they are floor only.
    ("ensuite-long.webp",                       "ensuite",        10.0),
    ("Sunlit Coral and Navy Bathroom Spa.png",  "bathroom",       10.0),
    ("bathroom-family.webp",            "bathroom-family",        10.0),
    ("kitchen-galley.webp",                     "kitchen",        10.0),
    ("kitchen-and-dining.webp",                 "kitchen-dining", 10.0),
]

STEP = 1           # columns. One, not three: the mask is built in blocks
#                    this wide, so anything bigger quantises every boundary
#                    and the top of a tiled wall comes out as a staircase
#                    with steps that size. Three was visible.
MIN_RUN = 14       # a span shorter than this is a reflection, not a wall
CLOSE = 8          # a break this short is a speck, not a hole in the wall
EDGE = 2           # pixels of blend taken at each end of a span

# The growth is for the blend, and a blend lies between the wall and the
# thing beside it. Where the thing beside it is much brighter than the
# paint there is no blend worth taking: the rim of the ensuite's toilet
# reads 0.85 to 0.93 against paint at 0.63, and the two pixels taken there
# are tile drawn on the toilet, which under a dark tile is a smudge along
# its edge. Measured the other way, the blend against a cabinet is 0.65 to
# 0.75, below the bar, and is still taken.
GLARE = 1.25       # times the paint's own brightness

# What the paint lights is not the paint. The shadowed end of a kitchen
# cabinet reads 0.33 to 0.35 of the paint's own saturation and the folds
# of a towel 0.31 to 0.39, both inside a test that asks for 0.31, and the
# mask grew tongues onto both. The trouble is that wall washed out by the
# sun lands in the same band: beside the bathroom's window it reads 0.31
# to 0.34, and a plain saturation floor that excludes the cabinet takes
# forty pixels of that wall with it.
#
# What separates them is the light. The washed-out wall is bright, 0.78 to
# 0.82; the cabinet's end and the towel's folds are 0.33 to 0.65, lit by
# the wall rather than by the window. So a pixel that is not bright has to
# carry more of the paint's colour to count as the paint.
FIRM = 0.72        # of the paint's saturation, for a pixel that is not
#                    lit. Eight tenths was tried first and took a patch
#                    of the bathroom's own wall with it, sixteen by
#                    forty-nine pixels at 0.45 against a floor of 0.46.
# What counts as lit, as a multiple of the paint's own brightness rather
# than as a number of its own. The first try was absolute, 0.78, and it
# cut a cloud-shaped patch out of the bathroom's wall beside the window:
# saturation 0.39 against a firm floor of 0.41 and brightness 0.76 against
# a bar of 0.78, a hair under both. Measured against the paint instead,
# that patch is a quarter brighter than the wall it belongs to, while the
# cabinet's end is fifteen per cent darker and the towel's folds a third
# darker. The light is what tells them apart, and the paint is what the
# light should be measured against.
LIT = 1.10         # times the paint's own brightness
ISLAND = 400       # a patch of mask smaller than this is not a wall
PINHOLE = 12       # a hole no wider and no taller than this is not a window
SMOOTH = 9         # columns averaged when straightening the wall's own edges
WANDER = 10        # ...and the most a column may be moved while doing it
UPRIGHT = 7        # rows of mask a column is judged over, sideways
FLAT = 11          # ...and columns it is judged over, up and down. Seven
#                    straightened the short wobbles in the line under a
#                    cabinet and left the long ones, which are the ones
#                    the eye follows.

# A nub is a bump on the outline rather than a piece of surface: mask
# whose neighbourhood is mostly not mask. It cannot be swept as an island
# because it is attached to the wall, and it is too small for any of the
# medians to reach. There are eighty one such pixels in the kitchen, in
# clumps of three to ten, and one of them sits on the corner of a cabinet
# where it shows.
NUB = 6            # the neighbourhood, either side
NUBBY = 0.34       # mask within it, below which a pixel is a bump
# A wall seen as a band narrower than this cannot show a tile; it shows a
# line. Three was enough to drop a strip two pixels wide in the kitchen's
# corner, and it leaves the fingers the mask grows into the folds of the
# ensuite's towel, where the shadow takes enough of the wall's colour to
# pass the test: five to nine pixels across, against the seventeen of the
# genuine wall beside them.
#
# A saturation floor was tried first and is the wrong instrument. The
# fingers read 0.31 to 0.39 of the paint's own saturation and the wall
# beside them 0.51, so a floor at 0.40 separates them here, and in the
# bathroom it takes out forty pixels of sunlit wall along the side of the
# window, which is the same brightness washing out the same colour.
THIN = 10          # a row of mask narrower than this is not a wall

# A hole in the wall that is the paint with the light taken out of it: the
# reveal, the return of the wall into a window, which faces the sun and
# washes out past what the colour test will accept. Measured on the three
# rooms that have one, they read 3.5, 5.8 and 9.3 degrees from the paint's
# own hue, saturation 0.22 to 0.30 against a test wanting 0.33 or more, and
# brightness 0.87 to 0.93. Everything else enclosed by wall in these rooms
# is a long way from one of those: the windows themselves sit 59 to 80
# degrees away in hue, being greenery; the black frames and the shadow
# behind a screen are at brightness 0.05 to 0.33; the toilet roll is at
# saturation 0.08. The cream towel, which caught every earlier attempt at
# this, fails twice over: it hangs against a door, so it is not enclosed by
# wall at all, and it sits 25 degrees away in hue.
REVEAL_WIN = 10.0  # degrees from the paint's own hue
REVEAL_SAT = 0.15  # at least this much colour, or it is porcelain
REVEAL_VAL = 0.78  # and this bright, or it is a shadow
REVEAL_WIDE = 60   # a reveal is a return of the wall, so it is narrow
REVEAL_MOST = 0.6  # ...and most of it has to read that way, not its average

# The island sweep in tidy() runs before the sides are straightened and
# grown, and those passes make pieces of their own: a sliver of the
# ensuite's towel, 13 by 81, and specks five and seven pixels across in the
# bathroom. The gap in the measurements is wide. Every piece that is wall
# in these rooms is 3,647 cells or more; every piece that is not is 701 or
# fewer.
SPECK = 1500       # a piece of mask smaller than this is not a wall


def spans(path, hint):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    w, h = im.size
    px = im.filter(ImageFilter.GaussianBlur(0.6)).load()
    found = keycolour.paint(px, w, h, hint)
    if found is None:
        return None, (w, h), None
    ref, ref_sat, win, ref_val = found
    is_wall = keycolour.tester(ref, ref_sat, win, ref_val, FIRM, LIT)

    order = []
    raw = {}
    for x in range(0, w, STEP):
        xs = min(x, w - 1)
        order.append(xs)
        runs = []
        y0 = None
        for y in range(0, h):
            if is_wall(*px[xs, y]):
                if y0 is None:
                    y0 = y
            else:
                if y0 is not None:
                    runs.append([y0, y - 1])
                y0 = None
        if y0 is not None:
            runs.append([y0, h - 1])
        raw[xs] = merge(runs, CLOSE)

    cols = []
    for i, xs in enumerate(order):
        left = raw[order[i - 1]] if i > 0 else None
        right = raw[order[i + 1]] if i + 1 < len(order) else None
        runs = [r for r in raw[xs]
                if r[1] - r[0] + 1 >= MIN_RUN or joined(r, left, right)]
        runs = merge(grow(runs, h, px, xs, ref_val * keycolour.VLO,
                          ref_val * GLARE), 0)
        if runs:
            cols.append([xs] + [c for r in runs for c in r])
    cols = tidy(cols, w, h, px, ref, ref_sat * keycolour.LO)
    cols = straighten(cols, h)
    # Straighten, grow, straighten. Growing a ragged side leaves it ragged
    # and two pixels further out, and growth stops at a different pixel in
    # each row, so it ravels a straight side again by a pixel. Doing it on
    # both sides of the growth keeps the mask within two or three pixels of
    # the paint and still leaves a line the eye can follow.
    cols = upright(cols, w, h)
    cols = sliver(cols, w, h)
    cols = widen(cols, w, h, px, ref_val * keycolour.VLO,
                 ref_val * GLARE)
    cols = upright(cols, w, h)
    cols = flatten(cols, w, h)
    # Twice: taking a bump off exposes the one behind it, and a third
    # pass found nothing left to take in any of these rooms.
    cols = shave(cols, w, h)
    cols = shave(cols, w, h)
    cols = despeck(cols, w, h)
    return cols, (w, h), (ref, ref_sat, win)


def asgrid(cols, w, h):
    """The mask as one cell per pixel of the picture.

    Every column of the picture, not only the ones that carry a span. A
    column with no wall in it is a gap, and anything working sideways has
    to see it as one. Indexing by the columns that happen to have spans
    puts two pieces of wall side by side that have a window between them,
    which is how a strip two pixels wide survived a pass meant to drop it.
    """
    grid = bytearray(w * h)
    for col in cols:
        i = col[0]
        for k in range(1, len(col), 2):
            for y in range(max(col[k], 0), min(col[k + 1] + 1, h)):
                grid[y * w + i] = 1
    return grid


def ascols(grid, w, h):
    out = []
    for x in range(w):
        runs = []
        y0 = None
        for y in range(h):
            if grid[y * w + x]:
                if y0 is None:
                    y0 = y
            elif y0 is not None:
                runs.append([y0, y - 1])
                y0 = None
        if y0 is not None:
            runs.append([y0, h - 1])
        if runs:
            out.append([x] + [v for r in runs for v in r])
    return out


def sliver(cols, w, h):
    """Drop the rows of mask that are only a pixel or two across.

    MIN_RUN throws away a run too short to be a wall, measured down the
    column, and there was never anything measuring it across. The kitchen
    kept a strip two pixels wide and forty rows tall between the window
    frame and the edge of the picture: a real enough piece of wall, and
    tiled it reads as a bright line drawn down the corner, because two
    pixels of tile cannot show that they are a wall.

    This runs before the sides are grown, so a strip that survives is one
    the photograph really does show three pixels of.
    """
    grid = asgrid(cols, w, h)
    out = bytearray(grid)
    for y in range(h):
        row = y * w
        run = 0
        for i in range(w + 1):
            if i < w and grid[row + i]:
                run += 1
                continue
            if 0 < run < THIN:
                for j in range(i - run, i):
                    out[row + j] = 0
            run = 0
    return ascols(out, w, h)


def upright(cols, w, h):
    """Take the wiggle out of the edges that run up the picture.

    straighten() works on the top and the bottom of the wall, which is
    where the gradients are, and nothing has ever touched the sides. Where
    a wall ends against the side of a cabinet or a cistern the boundary is
    wherever the colour test happened to flip in each row, and measured on
    these rooms it moves a pixel or two from its neighbours in one row in
    eight, and three or more in one in thirty. Seen as a line rather than
    as pixels, that is a ragged edge down every upright junction.

    A median down the column fixes it and costs nothing else: a median
    leaves a straight edge and a sloping one exactly where they are, and
    only moves a boundary that disagrees with the rows around it. Seven
    rows is the window, so a jog has to last four rows to survive, and a
    strip of wall three rows tall is not worth tiling anyway.
    """
    grid = asgrid(cols, w, h)
    half = UPRIGHT // 2
    out = bytearray(grid)
    for i in range(w):
        for y in range(h):
            a = max(0, y - half)
            b = min(h, y + half + 1)
            n = 0
            for yy in range(a, b):
                n += grid[yy * w + i]
            out[y * w + i] = 1 if n * 2 > (b - a) else 0
    return ascols(out, w, h)


def widen(cols, w, h, px, dark, glare):
    """Stretch each row over the blend at its sides, as grow() does its ends.

    The reasoning is grow()'s exactly, turned ninety degrees. A wall does
    not stop at a line where it passes behind a cistern or a cabinet side;
    there are two or three pixels that are part wall and part object, they
    are not the paint so the test refuses them, and they show as a coral
    line down the junction. Nothing covered them until now, because growth
    only ever ran up and down a column.
    """
    grid = asgrid(cols, w, h)
    out = bytearray(grid)
    for y in range(h):
        row = y * w
        for i in range(w):
            if not grid[row + i]:
                continue
            if i and grid[row + i - 1] and i + 1 < w and grid[row + i + 1]:
                continue
            for side in (-1, 1):
                for k in range(1, EDGE + 1):
                    j = i + side * k
                    if j < 0 or j >= w or grid[row + j]:
                        break
                    v = max(px[j, y]) / 255.0
                    if v < dark or v > glare:
                        break
                    out[row + j] = 1
    return ascols(out, w, h)


def blobs(grid, nc, h, want):
    """Every 4-connected patch of `want`, as (cells, width, height, edge)."""
    from collections import deque
    seen = bytearray(nc * h)
    out = []
    for start in range(nc * h):
        if seen[start] or grid[start] != want:
            continue
        q = deque([start])
        seen[start] = 1
        cells = [start]
        x0 = x1 = start % nc
        y0 = y1 = start // nc
        edge = False
        while q:
            p = q.popleft()
            cx, cy = p % nc, p // nc
            if cx == 0 or cx == nc - 1 or cy == 0 or cy == h - 1:
                edge = True
            if cx < x0:
                x0 = cx
            if cx > x1:
                x1 = cx
            if cy < y0:
                y0 = cy
            if cy > y1:
                y1 = cy
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ax, ay = cx + dx, cy + dy
                if 0 <= ax < nc and 0 <= ay < h:
                    a = ay * nc + ax
                    if not seen[a] and grid[a] == want:
                        seen[a] = 1
                        q.append(a)
                        cells.append(a)
        out.append((cells, x1 - x0 + 1, y1 - y0 + 1, edge))
    return out


def flatten(cols, w, h):
    """Take the wobble out of the edges that run across the picture.

    straighten() smooths the top of the first span and the bottom of the
    last, which are the wall's own outer edges, and nothing has ever
    touched the ones in between. In a kitchen the wall shows above the
    cabinets and again below them, so every column has two spans and the
    long boundary along the underside of a cabinet is an inside end: the
    shadow there takes just enough of the wall's colour to pass the test
    in some columns and not in others, and the line comes out chewed.
    Measured on the kitchen, that boundary disagrees with its neighbours
    by three pixels or more four times as often as the outer edge that is
    straightened.

    A median across the row does for a flat edge what upright() does for
    an upright one, and for the same reason: a median leaves a straight
    edge and a sloping one where they are, and only moves a column that
    disagrees with the columns beside it.
    """
    grid = asgrid(cols, w, h)
    half = FLAT // 2
    out = bytearray(grid)
    for y in range(h):
        row = y * w
        for x in range(w):
            a, b = max(0, x - half), min(w, x + half + 1)
            n = 0
            for xx in range(a, b):
                n += grid[row + xx]
            out[row + x] = 1 if n * 2 > (b - a) else 0
    return ascols(out, w, h)


def shave(cols, w, h):
    """Take off the pixels that stick out of the outline.

    Counted over a square either side, with a summed area table so the
    count is four lookups rather than a hundred and sixty nine. A strip of
    wall ten pixels wide, which is the narrowest that survives THIN, fills
    three quarters of that square and is left alone; a bump of three or
    four pixels fills a fifth of it and goes.
    """
    grid = asgrid(cols, w, h)
    wide = w + 1
    sat = [0] * (wide * (h + 1))
    for y in range(h):
        run = 0
        row = y * w
        here = (y + 1) * wide
        above = y * wide
        for x in range(w):
            run += grid[row + x]
            sat[here + x + 1] = sat[above + x + 1] + run

    def count(x0, y0, x1, y1):
        return (sat[(y1 + 1) * wide + x1 + 1] - sat[y0 * wide + x1 + 1]
                - sat[(y1 + 1) * wide + x0] + sat[y0 * wide + x0])

    side = (2 * NUB + 1) ** 2
    out = bytearray(grid)
    for y in range(NUB, h - NUB):
        for x in range(NUB, w - NUB):
            if not grid[y * w + x]:
                continue
            if count(x - NUB, y - NUB, x + NUB, y + NUB) < side * NUBBY:
                out[y * w + x] = 0
    return ascols(out, w, h)


def despeck(cols, w, h):
    """Sweep the pieces the straightening and the growing leave behind.

    tidy() does this once, before the sides are touched, and the sides make
    new pieces: a sliver of a towel, where the shadow in its folds takes
    enough of the wall's colour to pass, and a speck of five pixels where a
    column was straightened away from its neighbours. Looked at as a mask
    rather than as columns, both are obvious.
    """
    grid = asgrid(cols, w, h)
    for cells, bw, bh, _ in blobs(grid, w, h, 1):
        if len(cells) < SPECK:
            for c in cells:
                grid[c] = 0
    return ascols(grid, w, h)


def lit(cells, w, px, ref, floor):
    """Is this hole the paint with the light taken out of it.

    Counted pixel by pixel, not averaged. Averaging was the first attempt
    and it filled the lit rim of the ensuite's toilet: the rim carries
    almost no colour, saturation 0.08 to 0.12, but the shadow line between
    it and the wall carries a great deal, and the two averaged out in the
    middle of the band a reveal sits in. A reveal is washed-out paint all
    the way along, so most of it reads that way on its own.
    """
    good = 0
    n = 0
    for c in cells[::3]:
        hh, ss, vv = keycolour.hsv(*px[c % w, c // w])
        n += 1
        if (keycolour.apart(hh, ref) < REVEAL_WIN and ss >= REVEAL_SAT
                and ss < floor and vv >= REVEAL_VAL):
            good += 1
    return bool(n) and good >= n * REVEAL_MOST


def tidy(cols, w, h, px, ref, floor):
    """Take the specks out of the mask and fill the pinholes in it.

    Everything above this point works a column at a time, which cannot see
    a speck sitting on a toilet lid or a pinhole in the middle of a wall.
    Looked at as a mask, both are obvious, and both are what shows in the
    picture as a small patch that changes colour whenever the tile changes.

    The two thresholds are not taste, they are the gap in the measurements.
    A real wall is between fifty thousand and two hundred thousand cells;
    everything else in these rooms is under four hundred, with nothing in
    between. A window, a mirror or a sunlit reveal is between forty-five and
    two hundred and thirty rows tall; the noise is twelve by twelve or less.
    A hole has to be small in both directions to be filled, which is what
    keeps the towel and the reveals as holes: they are narrow, but they are
    long.
    """
    if not cols:
        return cols
    grid = asgrid(cols, w, h)

    for cells, bw, bh, _ in blobs(grid, w, h, 1):
        if len(cells) < ISLAND:
            for c in cells:
                grid[c] = 0
    for cells, bw, bh, edge in blobs(grid, w, h, 0):
        if edge:
            continue
        if bw <= PINHOLE and bh <= PINHOLE:
            for c in cells:
                grid[c] = 1
        elif min(bw, bh) <= REVEAL_WIDE and lit(cells, w, px, ref, floor):
            for c in cells:
                grid[c] = 1

    return ascols(grid, w, h)


def joined(run, left, right):
    """Is this short run part of the wall on either side of it.

    The minimum length is there to throw away a speck: a reflection, a
    highlight, a few pixels of noise that happen to be the right colour. But
    it throws away honest wall too, wherever a run is cut short — under the
    lip of a cabinet, beside the hood — and what is left is a dash of old
    paint standing on a tiled wall. Every dash in all three rooms was
    thirteen pixels or less against a threshold of fourteen.

    So the length alone no longer decides. A short run is kept when the
    columns to either side are wall at the same height, because that is a
    continuous surface seen through a narrow gap. A speck has no such
    neighbours, which is exactly what makes it a speck.
    """
    a, b = run
    sides = [s for s in (left, right) if s is not None]
    if not sides:
        return False
    for s in sides:
        if not any(r[0] <= b and r[1] >= a for r in s):
            return False
    return True


def merge(runs, gap):
    """Join runs separated by no more than gap pixels.

    A flat wall photographs with specks in it: a pixel of sensor noise, the
    highlight on a socket, the line of a shadow. Each one cuts the column in
    two and leaves a dot of old paint showing through the tiling. Nothing
    that short is a real hole in a wall, and a window or a mirror is hundreds
    of pixels, so it survives this untouched.
    """
    out = []
    for a, b in runs:
        if out and a - out[-1][1] - 1 <= gap:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def grow(runs, h, px, x, dark, glare):
    """Stretch each run over the blend at its ends, where there is one.

    Where the wall meets a cabinet there is no edge, there is a ramp: three
    or four pixels that are part wall and part cabinet. They are not the
    paint, so the test rightly refuses them, and the tiling then stops short
    and leaves them showing as a fringe along the junction.

    Where the wall meets a black window frame there is no ramp at all. The
    wall ends at one row and the frame starts at the next, measured in all
    three rooms: zero pixels in between. Growing into that puts two pixels
    of tile along the top and bottom of every window, on a crisp black edge
    where it shows, and covers nothing that needed covering.

    So the growth stops at the first pixel that is plainly not wall, which
    is the same brightness floor the test itself uses: a frame, a tap, a
    black fitting. A blend pixel against a cabinet is dark but not that
    dark, and is still taken.

    Being mean here is cheap either way. Whatever the tile does not cover,
    the repaint pass neutralises, and a neutralised pixel is invisible.
    """
    out = []
    for a, b in runs:
        na, nb = a, b
        for i in range(1, EDGE + 1):
            y = a - i
            if y < 0:
                break
            v = max(px[x, y]) / 255.0
            if v < dark or v > glare:
                break
            na = y
        for i in range(1, EDGE + 1):
            y = b + i
            if y >= h:
                break
            v = max(px[x, y]) / 255.0
            if v < dark or v > glare:
                break
            nb = y
        out.append([na, nb])
    return out


def overlay(path, cols, dst, label):
    with Image.open(path) as raw:
        im = raw.convert("RGB")
    d = ImageDraw.Draw(im, "RGBA")
    for col in cols:
        x = col[0]
        for i in range(1, len(col), 2):
            d.rectangle([x, col[i], x + STEP - 1, col[i + 1]],
                        fill=(255, 0, 200, 110))
    d.text((16, 16), label, fill=(255, 255, 0, 255))
    im.save(dst, "JPEG", quality=86)


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    out = {}
    for name, slug, hint in ROOMS:
        p = os.path.join(SRC, name)
        cols, (w, h), found = spans(p, hint)
        if cols is None:
            print("  %-10s no paint near %.0f degrees" % (slug, hint))
            continue
        ref, ref_sat, win = found
        nums = sum(len(c) for c in cols)
        out[slug] = {"step": STEP, "size": [w, h], "cols": cols}
        overlay(p, cols, os.path.join(OUT, "%s.jpg" % slug),
                "%s  hint %.0f -> hue %.0f deg  sat %.2f  window %.0f  %d columns"
                % (slug, hint, ref, ref_sat, win, len(cols)))
        print("  %-10s hint %3.0f -> hue %3.0f deg  sat %.2f  %4d columns"
              " window %2.0f %5d numbers" % (slug, hint, ref, ref_sat, len(cols), win, nums))
    with io.open(os.path.join(OUT, "walls.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("walls traced")




def straighten(cols, h):
    """Take the wander out of the top and bottom edges of the wall.

    Where a wall meets a ceiling there is no line, there is a gradient: the
    ceiling catches the wall's colour and fades into it over several pixels.
    The test has to cross that gradient somewhere, and it crosses a pixel or
    two higher or lower in each column depending on nothing but noise. The
    mask is correct to within a pixel everywhere and still reads as a chewed
    edge, because the eye follows the edge rather than the pixels.

    Measured on these rooms, that wander is at most three pixels in
    ninety-five columns out of a hundred. A genuine step, where the wall
    meets a window or a cabinet, is twenty-five or more. There is a wide gap
    between the two, so a column is moved to the median of its neighbours
    only when that asks for less than WANDER pixels, and a real step is left
    exactly where it is.

    Only the outermost edges are straightened. The sides of a window are
    already crisp in the photograph, being a black frame against paint, and
    they are nobody's idea of a gradient.
    """
    if not cols:
        return cols
    first = [c[1] for c in cols]
    last = [c[-1] for c in cols]
    half = SMOOTH // 2
    out = []
    for i, col in enumerate(cols):
        a, b = max(0, i - half), min(len(cols), i + half + 1)
        ftop = sorted(first[a:b])[(b - a) // 2]
        flast = sorted(last[a:b])[(b - a) // 2]
        new = list(col)
        if abs(ftop - new[1]) <= WANDER:
            new[1] = max(0, min(ftop, new[2]))
        if abs(flast - new[-1]) <= WANDER:
            new[-1] = min(h - 1, max(flast, new[-2]))
        out.append(new)
    return out


main()
