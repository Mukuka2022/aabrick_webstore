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
    # Six rooms, each photographed twice: once as it is, and once with the
    # floor painted a flat blue. The blue one is what ships, because its
    # floor is both the outline and the lighting.
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
    {
        "id": "living",
        "label": "Living room",
        "image": "/assets/aabrick_webstore/images/scene-living.jpg",
        "horizon": 212,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 646], [1080, 483],
            [1070, 490], [1050, 490], [1035, 482], [995, 480],
            [970, 481], [945, 478], [830, 477], [825, 504],
            [815, 521], [800, 523], [795, 513], [695, 525],
            [690, 576], [660, 586], [545, 578], [540, 527],
            [480, 524], [475, 513], [470, 514], [460, 528],
            [330, 598], [325, 598], [295, 619], [290, 619],
            [275, 629], [270, 642], [65, 645], [45, 672],
            [0, 688],
        ],
    },
    {
        "id": "ensuite",
        "label": "Ensuite",
        "image": "/assets/aabrick_webstore/images/scene-ensuite.jpg",
        "horizon": 118,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 1085], [1425, 1085],
            [1420, 882], [1405, 854], [1255, 861], [1190, 844],
            [1175, 828], [1120, 662], [995, 589], [910, 590],
            [905, 649], [885, 650], [880, 590], [775, 591],
            [770, 616], [765, 591], [720, 594], [715, 591],
            [485, 593], [465, 627], [430, 632], [175, 905],
            [105, 909], [90, 916], [85, 912], [80, 916],
            [75, 912], [70, 913], [20, 958], [0, 974],
        ],
    },
    {
        "id": "kitchen",
        "label": "Kitchen",
        "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
        "horizon": 90,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1087], [1444, 1087], [1440, 760], [1410, 737],
            [1395, 736], [1390, 722], [1380, 725], [1375, 707],
            [1220, 595], [1200, 589], [1195, 576], [1105, 513],
            [435, 513], [245, 663], [225, 689], [195, 713],
            [190, 714], [185, 721], [180, 723], [175, 730],
            [160, 742], [155, 743], [150, 748], [135, 753],
            [35, 834], [30, 856], [20, 862], [0, 861],
        ],
    },
    {
        "id": "bathroom",
        "label": "Bathroom",
        "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
        "horizon": 92,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 832], [1420, 813],
            [1405, 777], [1255, 774], [1225, 754], [1180, 620],
            [1175, 557], [1095, 517], [820, 516], [815, 523],
            [780, 551], [525, 548], [490, 517], [440, 519],
            [425, 543], [395, 546], [55, 772], [40, 775],
            [0, 796],
        ],
    },
    {
        "id": "patio",
        "label": "Veranda",
        "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
        "horizon": 272,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 673], [1270, 596],
            [1160, 598], [1120, 576], [1115, 540], [1015, 492],
            [950, 485], [485, 484], [465, 498], [450, 501],
            [370, 553], [365, 572], [325, 598], [300, 598],
            [295, 605], [290, 598], [285, 596], [270, 605],
            [240, 624], [235, 643], [230, 647], [225, 645],
            [215, 657], [200, 664], [195, 638], [190, 644],
            [185, 642], [180, 676], [175, 648], [160, 656],
            [155, 692], [145, 700], [130, 707], [125, 677],
            [120, 714], [115, 716], [110, 685], [105, 723],
            [95, 726], [85, 679], [80, 739], [70, 740],
            [65, 711], [60, 709], [55, 755], [50, 718],
            [45, 723], [40, 724], [10, 744], [5, 788],
            [0, 789],
        ],
    },
    {
        "id": "kitchen-dining",
        "label": "Kitchen and dining",
        "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
        "horizon": 143,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 691], [1440, 688],
            [1435, 649], [1430, 551], [1420, 553], [1410, 552],
            [1405, 623], [1390, 561], [1375, 555], [1370, 580],
            [1365, 556], [1360, 552], [1355, 579], [1350, 643],
            [1345, 664], [1340, 584], [1330, 543], [1290, 526],
            [1285, 539], [1270, 623], [1265, 567], [1260, 662],
            [1255, 634], [1250, 680], [1245, 690], [1225, 687],
            [1220, 549], [1210, 549], [1205, 598], [1200, 611],
            [1190, 549], [1170, 550], [1165, 590], [1160, 552],
            [1150, 552], [1145, 565], [1125, 663], [1120, 543],
            [1095, 628], [1085, 580], [1080, 580], [1075, 573],
            [1070, 502], [1065, 500], [915, 497], [475, 497],
            [245, 666], [235, 671], [230, 688], [210, 690],
            [150, 733], [145, 752], [140, 752], [135, 757],
            [115, 767], [110, 756], [100, 775], [95, 774],
            [90, 781], [80, 785], [65, 798], [60, 799],
            [55, 807], [50, 806], [45, 812], [40, 810],
            [30, 824], [25, 824], [20, 831], [15, 831],
            [10, 838], [0, 841],
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
