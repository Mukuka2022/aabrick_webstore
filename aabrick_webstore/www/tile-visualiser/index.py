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

Rooms here are the three already published on the site. They are stand-ins.
The photographs that belong here are AABrick branch showrooms, which are
the only rooms that are both AABrick property and full of AABrick tiles.
Swapping one in is this dictionary and nothing else.
"""

import frappe

from aabrick_webstore import visualiser

no_cache = 1
sitemap = 1

SCENES = [
    {
        "id": "kitchen",
        "label": "Kitchen",
        "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
        # 1536x1024. The floor it replaces already has grout lines in it,
        # which is the easiest calibration there is: the numbers below were
        # moved until the new joints ran along the old ones.
        "horizon": 460,
        "cx": 768,
        "focal": 1536,
        "height": 2.0,
        "floor": [
            [0, 1024], [1536, 1024], [1536, 780], [1450, 755],
            [1200, 715], [1035, 700], [400, 700], [330, 650],
            [150, 625], [0, 615],
        ],
    },
    {
        "id": "living",
        "label": "Living room",
        "image": "/assets/aabrick_webstore/images/showcase-3.jpg",
        # Measured against the 900x979 original.
        "horizon": 330,
        "cx": 450,
        "focal": 900,
        "height": 2.4,
        "floor": [
            [0, 979], [900, 979], [900, 530], [760, 495],
            [430, 455], [200, 420], [0, 450],
        ],
    },
    {
        "id": "lounge",
        "label": "Lounge, wide",
        "image": "/assets/aabrick_webstore/images/hero.jpg",
        # 960x432.
        "horizon": 110,
        "cx": 480,
        "focal": 960,
        "height": 2.2,
        "floor": [
            [0, 432], [960, 432], [960, 255], [700, 240],
            [430, 205], [240, 185], [0, 175],
        ],
    },
    {
        "id": "living2",
        "label": "Living room, tall",
        "image": "/assets/aabrick_webstore/images/showcase-1.jpg",
        # 900x979.
        "horizon": 280,
        "cx": 450,
        "focal": 900,
        "height": 2.4,
        "floor": [
            [0, 979], [900, 979], [900, 500], [620, 455],
            [330, 400], [120, 370], [0, 390],
        ],
    },
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
    context.aab_scenes_json = frappe.as_json(SCENES)
    context.aab_tile_count = len(tiles)

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
