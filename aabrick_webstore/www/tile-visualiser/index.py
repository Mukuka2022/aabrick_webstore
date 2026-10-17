"""The tile visualiser.

A room is a photograph plus four numbers and an outline, and that is the
whole of a scene. The four numbers are a camera: where the horizon sits in
the picture, where the lens centre is, the focal length in pixels, and how
high the camera was off the floor. From those the browser works out, for
every floor pixel, how many metres across and into the room it is, and
lays the tile on that. A 600mm tile then covers 600mm of floor wherever it
lands, and gets smaller towards the back by itself.

The outline is the floor, traced once. It has to stop where the furniture
starts, because anything inside it gets tiled.

The six rooms here were made for this, with the floor deliberately left
clear so the outline can follow the skirting rather than a sofa. They are
still not AABrick branches; swapping a real one in is this dictionary and
nothing else, plus a trace.
"""

import frappe

from aabrick_webstore import visualiser

no_cache = 1
sitemap = 1

SCENES = [
    # Empty, waiting on new photographs. What a room needs, and why, is
    # below; tools/README.md is how to turn a photograph into an entry here.
    #
    # A room is photographed twice: once as it is, and once with the floor
    # painted a flat blue and the walls a flat strong colour. The painted
    # one is what ships, because its floor is both the outline and the
    # lighting, and its walls are what the wall tracer reads.
    #
    # The outline is a measurement rather than a judgement. A pixel is floor
    # if it is that blue, and the edge is where the blue stops, so the line
    # follows a kickboard exactly and goes round a chair leg without being
    # told that a chair leg is there.
    #
    # The blue is also what makes a laid tile sit in the room. The engine
    # shades every tile by the floor's own brightness against its average, so
    # a floor that is one flat colour leaves pure light behind: the shadow
    # under a sofa, the pool of sun from a window, and none of the old
    # floor's own pattern mixed into it.
    #
    # The horizon is derived, not guessed: the gap between it and the
    # furthest floor in the picture is focal * height / depth, so writing
    # down how far back the room goes fixes it. The focal length is a 53
    # degree field of view across the frame.
]


def get_context(context):
    context.title = "Tile Visualiser | AABrick Zambia"
    context.aab_description = (
        "See an AABrick tile on a real floor before you buy it. Pick a room, "
        "pick a tile, and it is laid at its true size with the light of the "
        "room on it."
    )
    context.aab_canonical = frappe.utils.get_url("/tile-visualiser")

    tiles = visualiser.tiles()
    context.aab_tiles = tiles
    context.aab_tiles_json = frappe.as_json(tiles)
    # The same tiles, in the headed sets the picker lists them under. Sent
    # alongside the flat list rather than instead of it: the drawing code
    # wants one tile at a time and has no interest in the headings.
    context.aab_groups_json = frappe.as_json(visualiser.groups())
    # The photographs are replaced in place when a room is reshot, and a
    # browser holding the old one would show the old room under a new
    # outline. The version stamp the stylesheet uses rides along with them.
    from aabrick_webstore import hooks
    # Three of the rooms were photographed with their walls painted as well
    # as their floors, so those can be tiled too. The spans are far bulkier
    # than a floor outline, so they are fetched as a file rather than
    # written into every page.
    walled = ("ensuite", "kitchen", "bathroom")
    stamped = []
    for s in SCENES:
        s = dict(s)
        s["image"] = "%s?v=%s" % (s["image"], hooks.ASSET_VERSION)
        if s["id"] in walled:
            s["wallsUrl"] = (
                "/assets/aabrick_webstore/images/walls-%s.json?v=%s"
                % (s["id"], hooks.ASSET_VERSION))
        stamped.append(s)
    context.aab_scenes_json = frappe.as_json(stamped)
    context.aab_tile_count = len(tiles)

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
