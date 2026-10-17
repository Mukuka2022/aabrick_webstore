"""The painted key, and what tells it apart from the room around it.

A room is generated with its floor painted one flat colour and its walls
another, so that tracing is a measurement rather than a judgement. This is
the shared part: given roughly what colour a surface was painted, measure
what it actually came out as, and hand back a test for it.

Two colours have been used so far and they failed in opposite directions,
which is why the test ended up shaped the way it is.

The pink walls were *more* strongly coloured than anything else in the room
but barely different in hue, because the paint threw pink light over
everything: in the ensuite the wall reads 9 degrees and the toilet reads 12.
There, saturation did the separating.

The green wall is the other way round. It is far from anything else in hue
but *less* strongly coloured than the oak tall unit beside it, 0.41 against
0.59. Anything looking for the most strongly coloured thing, or simply for
the biggest coloured area, found the woodwork instead.

So three things are measured rather than assumed.

**The hue is hinted, then measured.** Whoever generated the room knows what
colour they painted the wall, and one number from them removes the whole
class of failure where the tool confidently measures the wrong object. The
hint is only a family; the exact hue is still found inside it, and both pink
rooms land where they always did.

**Saturation is bounded on both sides.** The lower bound keeps out what is
merely lit by the paint; the upper bound keeps out things that happen to
share the hue but are far more vivid, which is how the houseplants stay out
of the green kitchen's wall.

**The hue window is measured too.** This is what the green needed. A flat
wall does not photograph as one hue: the pinks hold to within two degrees,
but the green drifts from 78 at the top of the wall to 94 down on the
splashback, because a dark low-chroma colour carries its hue much more
loosely than a pale vivid one. A window wide enough for the green would have
been slack on the pink, and the one that fitted the pink cut the green wall
into patches. So the window comes from the spread of the paint itself.
"""

from collections import Counter

FAMILY = 25.0    # degrees around the hint that count as the hinted colour
SEED = 10.0      # degrees used to get a first fix before the spread is known
LO = 0.62        # of the paint's own saturation, at least
HI = 1.55        # ...and at most
SPREAD = 2.5     # how many interquartile ranges of hue count as the paint
MIN_WIN = 10.0   # never narrower than this
MAX_WIN = 20.0   # never wider, or the room starts getting in


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


def apart(a, b):
    """How far apart two hues are, the short way round the circle."""
    d = abs(a - b)
    return 360 - d if d > 180 else d


def paint(px, w, h, hint):
    """Measure the paint, given roughly what colour it is.

    Sampled from a band across the upper part of the picture, which is wall
    in every room built so far. Returns the hue it came out as, how strongly
    coloured it is, and how far either side of that hue to still call it the
    paint. None if the hinted colour is not in the room at all.
    """
    top, bottom = int(h * 0.06), int(h * 0.40)

    def sample():
        for y in range(top, bottom, 2):
            for x in range(0, w, 2):
                yield hsv(*px[x, y])

    votes = Counter()
    for hh, s, v in sample():
        if s > 0.20 and v > 0.08 and apart(hh, hint) < FAMILY:
            votes[round(hh)] += 1
    if sum(votes.values()) < 500:
        return None
    # the mode, averaged over its neighbours so a single degree cannot win
    ref = float(max(votes, key=lambda k: sum(votes.get(k + d, 0)
                                             for d in range(-4, 5))))

    # how strongly coloured, from a narrow window where it is certainly paint
    sats = sorted(s for hh, s, v in sample()
                  if s > 0.20 and v > 0.08 and apart(hh, ref) < SEED)
    ref_sat = sats[len(sats) // 2]
    lo, hi = ref_sat * LO, ref_sat * HI

    # and how far it drifts, now that the vivid and the dull are both out
    hues = sorted(hh for hh, s, v in sample()
                  if lo <= s <= hi and v > 0.08 and apart(hh, ref) < FAMILY)
    iqr = hues[int(len(hues) * .75)] - hues[int(len(hues) * .25)]
    win = min(MAX_WIN, max(MIN_WIN, SPREAD * iqr))
    return ref, ref_sat, win


def tester(ref, ref_sat, win):
    """Is this pixel the paint itself."""
    lo, hi = ref_sat * LO, ref_sat * HI

    def test(r, g, b):
        hh, s, v = hsv(r, g, b)
        if s < lo or s > hi or v < 0.08:
            return False
        return apart(hh, ref) < win

    return test
