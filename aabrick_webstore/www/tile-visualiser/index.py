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
         "horizon": 289, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 1085], [1425, 1085],
            [1420, 882], [1410, 859], [1405, 856], [1215, 855],
            [1175, 830], [1120, 662], [995, 589], [905, 589],
            [900, 649], [885, 649], [880, 590], [780, 590],
            [775, 696], [770, 687], [765, 591], [725, 591],
            [720, 596], [715, 591], [485, 592], [465, 627],
            [430, 632], [175, 904], [115, 909], [110, 907],
            [70, 912], [0, 974],
        ]},
        {"id": "bathroom", "label": "Bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
         "horizon": 247, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 832], [1420, 814],
            [1405, 779], [1255, 775], [1225, 756], [1180, 621],
            [1175, 557], [1095, 517], [975, 517], [970, 539],
            [965, 522], [960, 517], [820, 517], [780, 553],
            [525, 549], [490, 517], [440, 518], [435, 530],
            [425, 543], [395, 546], [55, 772], [30, 777],
            [0, 795],
        ]},
        {"id": "kitchen", "label": "Kitchen",
         "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
         "horizon": 242, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 763], [1410, 737],
            [1395, 736], [1390, 726], [1380, 726], [1375, 706],
            [1215, 590], [1205, 589], [1200, 578], [1105, 512],
            [435, 513], [235, 672], [35, 833], [30, 854],
            [25, 859], [0, 861],
        ]},
        {"id": "living", "label": "Living room",
         "image": "/assets/aabrick_webstore/images/scene-living.jpg",
         "horizon": 309, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 647], [1105, 490],
            [1045, 490], [1035, 483], [945, 480], [940, 524],
            [935, 478], [830, 478], [825, 509], [815, 522],
            [800, 523], [795, 514], [695, 525], [690, 576],
            [670, 584], [545, 578], [540, 527], [465, 525],
            [375, 569], [310, 609], [300, 612], [295, 618],
            [290, 619], [285, 633], [270, 643], [65, 645],
            [40, 675], [0, 688],
        ]},
        {"id": "patio", "label": "Veranda",
         "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
         "horizon": 349, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 674], [1275, 599],
            [1165, 599], [1120, 577], [1115, 541], [1015, 493],
            [950, 485], [490, 484], [455, 500], [370, 554],
            [365, 573], [330, 597], [310, 599], [160, 694],
            [130, 709], [120, 719], [105, 723], [95, 735],
            [90, 735], [60, 752], [55, 762], [45, 762],
            [40, 767], [35, 767], [0, 791],
        ]},
        {"id": "kitchen-tall", "label": "Kitchen, tall units",
         "image": "/assets/aabrick_webstore/images/scene-kitchen-tall.jpg",
         "horizon": 352, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 862], [1440, 850],
            [1430, 843], [1425, 847], [1385, 818], [1370, 817],
            [1355, 806], [1350, 788], [1200, 679], [1190, 678],
            [1185, 665], [1090, 597], [400, 597], [215, 749],
            [135, 816], [125, 817], [35, 888], [30, 907],
            [25, 909], [0, 909],
        ]},
        {"id": "kitchen-dining", "label": "Kitchen and dining",
         "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
         "horizon": 279, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 594], [1440, 601],
            [1360, 557], [1350, 555], [1345, 547], [1340, 550],
            [1335, 547], [1330, 539], [1325, 542], [1260, 508],
            [1085, 505], [470, 504], [230, 679], [225, 693],
            [210, 693], [145, 738], [140, 756], [125, 766],
            [100, 773], [40, 818], [35, 819], [30, 825],
            [25, 826], [20, 832], [15, 833], [10, 839],
            [0, 844],
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
        "kitchen",
        "kitchen-dining",
        "kitchen-tall")
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
