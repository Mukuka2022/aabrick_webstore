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
        "height": 1.15,
        # Traced off the photograph, on the second and looser reading.
        #
        # The first scan wanted floor to be pale and grey, which the lit toe
        # kicks are not: they throw warm light down, and the boundary
        # stopped underneath them, leaving a line of old floor along the
        # bottom of every cabinet. Allowing warm light in also found what
        # the strict reading had hidden, that the floor runs back into both
        # corners to about y 600 rather than stopping at the island.
        #
        # Three columns are still wrong and are interpolated across: x 416
        # and x 1024, where the island top and the marble wall are the same
        # colour as the floor and the scan climbs them, and x 64, where it
        # climbs the front of the fridge.
        "floor": [
            [0, 1024], [1536, 1024],
            [1536, 773], [1504, 779], [1472, 779], [1440, 771],
            [1408, 752], [1376, 733], [1344, 715], [1312, 698],
            [1280, 680], [1248, 662], [1216, 645], [1184, 627],
            [1152, 611], [1120, 615], [1088, 597], [1056, 596],
            [1024, 652], [992, 708], [960, 704], [928, 701],
            [896, 693], [864, 712], [832, 698], [800, 694],
            [768, 701], [736, 699], [704, 693], [672, 693],
            [640, 704], [608, 693], [576, 696], [544, 704],
            [512, 704], [480, 693], [448, 696], [416, 646],
            [384, 596], [352, 596], [320, 596], [288, 611],
            [256, 609], [224, 625], [192, 642], [160, 659],
            [128, 679], [96, 682], [64, 700], [32, 726],
            [0, 743],
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
