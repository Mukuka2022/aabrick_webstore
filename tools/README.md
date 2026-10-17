# Building a visualiser room

Three scripts, run in this order, turn a generated room into a room the
visualiser can tile. They all read the original generated images and write
into `aabrick_webstore/public/images/`, so any of them can be re-run without
first undoing the last run.

| | what it does |
|---|---|
| `bluetrace.py` | Finds the floor, where the floor was painted flat blue, and writes the outline and the camera into the page. |
| `walltrace.py` | Finds the walls, where the walls were painted flat pink, and writes them as spans beside the room photograph. |
| `depink.py` | Repaints whatever pink is left over, which is the ceiling and a few rims, as off-white. Run it last: it needs the wall mask to know what to leave alone. |

They all want `SRC` pointed at wherever the generated images are, and
`ROOMS` listing the ones to do.

## Why a key colour at all

A painted floor turns tracing from a judgement into a measurement. A pixel
is floor if it is that blue, so the outline follows a kickboard exactly and
goes round a chair leg without anyone having to say a chair is there. The
same colour then carries the light: the engine shades each tile by the
surface's own brightness against its average, and a surface that is one flat
colour everywhere leaves pure lighting behind, with none of the old floor's
pattern mixed in. That is the difference between a tile sitting in the room
and sitting on top of it.

`visualiser-room-brief.md`, kept with Mukuka's files rather than here, is
what to ask an image generator for. The one thing it does not yet say is
that the walls want painting too, a flat saturated pink, the same way the
floor wants painting blue.

## What separates paint from furniture

Not the same test twice. For the floor it is **hue**: the veranda has half
its floor in the shade of its own roof and half in full sun, and as colours
those are far enough apart that a test anchored on one throws the other
away. Their hue is the same to within a couple of degrees, because sunlight
changes how bright and how strong a blue is and not which blue it is.

For the walls hue is not enough on its own, because the pink paint throws
pink light over the whole room: in the ensuite the wall measures 9 degrees
and the toilet measures 12. What the paint has and the porcelain has not is
**strength of colour**, around 0.6 against 0.25. And the one strongly
coloured thing that is not wall, the oak vanity, sits 17 degrees away in
hue. Neither test holds alone; together they are clean.

## Checking the result

Both tracers write an overlay per room next to their output, the floor in
orange and the walls in green. Look at them. Four generations of floor
tracer were thrown away because they looked plausible in code and wrong in
the picture.

The page itself will show you too: `/tile-visualiser?mask=1` paints the
floor red and the walls blue instead of tiling them.
