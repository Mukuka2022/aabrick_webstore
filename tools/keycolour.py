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

So four things are measured rather than assumed.

**The hue is hinted, then measured.** Whoever generated the room knows what
colour they painted the wall, and one number from them removes the whole
class of failure where the tool confidently measures the wrong object. The
hint is only a family; the exact hue is still found inside it, and both pink
rooms land where they always did.

The hint needs a short leash. A warm room puts its woodwork and its
cabinetry close enough to a pink wall to be in the same wide family: the
kitchen has its wall at 7 degrees, its oak at 25 and its cabinet doors at
29, and the doors cover so much of the picture that at twenty-five degrees
they simply outvoted the wall. So the paint is looked for within NEAR of
the hint, which the paint itself has never needed more than a few degrees
of.

The same leash has to hold when the drift is measured, or the measurement
eats itself: let the oak into the sample and the spread it adds widens the
window until the window admits the oak. That is exactly what happened here
before the leash was shortened, and the kitchen tiled its tall unit.

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

NEAR = 12.0      # degrees from the hint the paint may be found at
SEED = 10.0      # degrees used to get a first fix before the spread is known
LO = 0.62        # of the paint's own saturation, at least
HI = 1.55        # ...and at most
SPREAD = 2.5     # how many interquartile ranges of hue count as the paint
MIN_WIN = 10.0   # never narrower than this
MAX_WIN = 14.0   # never wider, or the room starts getting in

# That ceiling was 20, set for a green kitchen that is no longer in the
# set. The deep red kitchen is what brought it down. Red drifts, so its
# window opened to the ceiling, and its oak column stands 21 degrees away
# from it: near enough that the grain's own variation reached across and
# the trace tiled part of the woodwork. Swept against a patch that is
# certainly wall and a patch that is certainly oak, the window keeps the
# same 68 per cent of the wall anywhere between 10 and 20 degrees, while
# the oak it takes falls from 5.7 per cent at 20 to 0.3 at 14. The width
# was buying nothing and costing the oak.
VLO = 0.35       # of the paint's own brightness, at least

# That last one is what keeps the fittings out. A matte black tap in a room
# painted strongly enough to trace does not read black, it reads dark
# paint: the ensuite's tap measures hue 22 at saturation 0.76, which is the
# wall's own colour, and the only thing separating them is that the tap is
# at brightness 0.10 and the wall is at 0.75. Hue and saturation both stop
# meaning much once a pixel is nearly black, so neither can be asked.
#
# The floor has to be relative, because a flat dark green wall lives at
# 0.22 and would fail any fixed figure that excluded a tap. Against each
# room's own paint, 0.35 clears the taps and keeps the darkest wall yet
# traced: the coral rooms cut at 0.21 to 0.26 against walls whose lowest
# honest twentieth sits at 0.31, and the green kitchen cuts at 0.08 against
# 0.12.


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

    Sampled from a band across the upper part of the picture, which is
    wall in every room built so far. Returns the hue it came out as, how
    strongly coloured it is, how far either side of that hue to still call
    it the paint, and how bright it is. None if the hinted colour is not in
    the room at all.
    """
    top, bottom = int(h * 0.06), int(h * 0.40)

    def sample():
        for y in range(top, bottom, 2):
            for x in range(0, w, 2):
                yield hsv(*px[x, y])

    votes = Counter()
    for hh, s, v in sample():
        if s > 0.20 and v > 0.08 and apart(hh, hint) < NEAR:
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
    vals = sorted(v for hh, s, v in sample()
                  if s > 0.20 and v > 0.08 and apart(hh, ref) < SEED)
    ref_val = vals[len(vals) // 2]
    lo, hi = ref_sat * LO, ref_sat * HI

    # and how far it drifts, now that the vivid and the dull are both out
    hues = sorted(hh for hh, s, v in sample()
                  if lo <= s <= hi and v > 0.08 and apart(hh, ref) < NEAR)
    iqr = hues[int(len(hues) * .75)] - hues[int(len(hues) * .25)]
    win = min(MAX_WIN, max(MIN_WIN, SPREAD * iqr))
    return ref, ref_sat, win, ref_val


def tester(ref, ref_sat, win, ref_val, firm=None, lit=None):
    """Is this pixel the paint itself.

    firm and lit, when given, add a second floor for the pixels that are
    not catching the light. See FIRM in walltrace.py: a surface the paint
    has merely lit, a cabinet's shadowed end or the fold of a towel, lands
    in the same saturation band as wall that the sun has washed out, and
    only its brightness tells them apart.
    """
    lo, hi = ref_sat * LO, ref_sat * HI
    dark = ref_val * VLO
    strict = None if firm is None else ref_sat * firm

    def test(r, g, b):
        hh, s, v = hsv(r, g, b)
        if s < lo or s > hi or v < dark:
            return False
        if strict is not None and v < lit and s < strict:
            return False
        return apart(hh, ref) < win

    return test
