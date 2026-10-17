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
        {"id": "ensuite", "label": "Ensuite",
         "image": "/assets/aabrick_webstore/images/scene-ensuite.jpg",
         "horizon": 118, "cx": 724, "focal": 1463, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 1085], [1425, 1085],
            [1420, 882], [1410, 859], [1405, 854], [1265, 861],
            [1195, 847], [1175, 828], [1120, 662], [995, 589],
            [905, 589], [900, 649], [885, 649], [880, 590],
            [780, 590], [775, 696], [770, 663], [765, 591],
            [725, 591], [720, 596], [715, 591], [485, 592],
            [465, 627], [430, 632], [175, 904], [115, 909],
            [110, 907], [105, 909], [100, 907], [95, 911],
            [85, 912], [80, 909], [70, 911], [0, 974],
        ]},
        {"id": "bathroom", "label": "Bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
         "horizon": 93, "cx": 723, "focal": 1462, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 831], [1440, 830],
            [1415, 806], [1405, 777], [1250, 773], [1225, 755],
            [1180, 621], [1175, 557], [1100, 518], [975, 517],
            [970, 537], [965, 518], [820, 517], [780, 551],
            [530, 551], [490, 517], [440, 518], [425, 543],
            [395, 545], [55, 772], [30, 777], [0, 795],
        ]},
        {"id": "kitchen", "label": "Kitchen",
         "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
         "horizon": 88, "cx": 723, "focal": 1462, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 762], [1410, 736],
            [1395, 736], [1390, 721], [1385, 716], [1380, 726],
            [1375, 706], [1215, 590], [1205, 589], [1200, 578],
            [1105, 512], [435, 513], [235, 672], [35, 833],
            [30, 854], [25, 859], [0, 860],
        ]},
        {"id": "living", "label": "Living room",
         "image": "/assets/aabrick_webstore/images/scene-living.jpg",
         "horizon": 213, "cx": 724, "focal": 1463, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 646], [1080, 483],
            [1070, 490], [1045, 490], [1035, 483], [975, 479],
            [970, 481], [945, 478], [825, 479], [820, 512],
            [815, 522], [800, 523], [795, 513], [695, 525],
            [690, 576], [680, 581], [545, 578], [540, 527],
            [480, 525], [475, 513], [465, 518], [460, 528],
            [385, 563], [380, 568], [375, 569], [310, 609],
            [300, 612], [295, 618], [290, 618], [275, 631],
            [270, 643], [65, 645], [40, 675], [0, 688],
        ]},
        {"id": "patio", "label": "Veranda",
         "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
         "horizon": 272, "cx": 724, "focal": 1463, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 673], [1270, 596],
            [1265, 598], [1160, 598], [1120, 576], [1115, 540],
            [1010, 490], [950, 485], [485, 484], [465, 498],
            [450, 501], [405, 531], [400, 524], [395, 537],
            [370, 553], [365, 572], [330, 596], [305, 599],
            [290, 594], [230, 632], [225, 648], [200, 664],
            [195, 637], [180, 645], [175, 679], [170, 650],
            [160, 656], [155, 692], [130, 707], [125, 676],
            [120, 714], [115, 717], [110, 684], [105, 723],
            [90, 732], [85, 634], [80, 653], [75, 742],
            [65, 748], [60, 710], [55, 755], [50, 718],
            [15, 738], [10, 782], [0, 789],
        ]},
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
    walled = (
        "bathroom",
        "ensuite",
        "kitchen")
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
