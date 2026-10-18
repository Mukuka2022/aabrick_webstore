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
            [1420, 882], [1410, 859], [1405, 856], [1360, 856],
            [1265, 861], [1240, 860], [1215, 855], [1185, 841],
            [1175, 830], [1140, 729], [1120, 662], [995, 589],
            [905, 589], [900, 649], [885, 649], [880, 590],
            [780, 590], [775, 696], [770, 687], [765, 591],
            [725, 591], [720, 596], [715, 591], [485, 592],
            [465, 627], [450, 631], [430, 632], [410, 650],
            [175, 904], [120, 907], [115, 909], [110, 907],
            [95, 911], [70, 912], [0, 974],
        ]},
        {"id": "bathroom", "label": "Bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
         "horizon": 247, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 832], [1435, 828],
            [1420, 814], [1405, 779], [1285, 781], [1255, 775],
            [1230, 762], [1225, 756], [1210, 714], [1180, 621],
            [1175, 557], [1095, 517], [975, 517], [970, 539],
            [965, 522], [960, 517], [820, 517], [800, 539],
            [780, 553], [675, 557], [540, 554], [520, 546],
            [490, 517], [440, 518], [430, 539], [425, 543],
            [390, 548], [55, 772], [30, 777], [0, 795],
        ]},
        {"id": "kitchen", "label": "Kitchen",
         "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
         "horizon": 352, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 862], [1440, 850],
            [1430, 843], [1425, 847], [1385, 818], [1370, 817],
            [1355, 806], [1350, 788], [1345, 784], [1200, 679],
            [1190, 678], [1185, 665], [1090, 597], [400, 597],
            [225, 736], [200, 764], [135, 816], [120, 819],
            [40, 883], [35, 888], [30, 907], [25, 909],
            [0, 909],
        ]},
        {"id": "kitchen-dining", "label": "Kitchen and dining",
         "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
         "horizon": 279, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1445, 594], [1440, 601],
            [1365, 563], [1360, 557], [1350, 555], [1345, 547],
            [1340, 550], [1335, 547], [1330, 539], [1325, 542],
            [1260, 508], [1095, 508], [1085, 505], [1030, 506],
            [1020, 504], [470, 504], [245, 667], [230, 679],
            [225, 693], [205, 695], [145, 738], [140, 756],
            [125, 766], [110, 769], [90, 779], [45, 811],
            [40, 818], [35, 819], [30, 825], [25, 826],
            [20, 832], [15, 833], [10, 839], [0, 844],
        ]},
        {"id": "living", "label": "Living room",
         "image": "/assets/aabrick_webstore/images/scene-living.jpg",
         "horizon": 309, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 647], [1300, 577],
            [1105, 490], [1075, 489], [1055, 491], [1045, 490],
            [1035, 483], [945, 480], [940, 524], [935, 478],
            [830, 478], [825, 509], [815, 522], [800, 523],
            [795, 514], [750, 514], [715, 523], [695, 525],
            [690, 576], [670, 584], [625, 589], [595, 589],
            [555, 583], [545, 578], [540, 527], [465, 525],
            [455, 531], [440, 535], [430, 542], [410, 549],
            [315, 604], [310, 609], [300, 612], [295, 618],
            [290, 619], [285, 633], [270, 643], [140, 641],
            [70, 644], [65, 645], [60, 650], [50, 665],
            [40, 675], [25, 682], [0, 688],
        ]},
        {"id": "patio", "label": "Veranda",
         "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
         "horizon": 349, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1445, 674], [1275, 599],
            [1165, 599], [1155, 596], [1120, 577], [1115, 541],
            [1005, 490], [960, 490], [950, 485], [930, 484],
            [490, 484], [485, 485], [465, 498], [450, 502],
            [385, 543], [370, 554], [365, 573], [330, 597],
            [310, 599], [290, 608], [230, 649], [170, 685],
            [160, 694], [130, 709], [120, 719], [105, 723],
            [95, 735], [85, 736], [65, 748], [60, 752],
            [55, 762], [45, 762], [40, 767], [35, 767],
            [0, 791],
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
        "kitchen-dining")
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
