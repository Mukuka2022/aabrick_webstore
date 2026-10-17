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
        "horizon": 162,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 577], [1330, 542],
            [1325, 546], [1320, 540], [1085, 455], [1080, 460],
            [1075, 461], [1070, 471], [1060, 474], [1050, 443],
            [1025, 433], [920, 433], [915, 441], [910, 443],
            [875, 439], [870, 427], [865, 462], [860, 466],
            [820, 466], [795, 471], [790, 514], [680, 518],
            [675, 475], [670, 473], [505, 465], [415, 536],
            [125, 532], [90, 546], [65, 547], [15, 568],
            [10, 578], [0, 581],
        ],
    },
    {
        "id": "ensuite",
        "label": "Ensuite",
        "image": "/assets/aabrick_webstore/images/scene-ensuite.jpg",
        "horizon": 28,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 1085], [1430, 1085],
            [1375, 1035], [1370, 1079], [1365, 1076], [1360, 1065],
            [1355, 1062], [1350, 1063], [1345, 1046], [1340, 1051],
            [1335, 1036], [1325, 1035], [1320, 1024], [1315, 1021],
            [1310, 975], [1305, 1012], [1300, 998], [1290, 1000],
            [1285, 981], [1280, 975], [1270, 982], [1265, 964],
            [1255, 968], [1250, 964], [1245, 953], [1240, 950],
            [1235, 942], [1230, 942], [1225, 931], [1220, 932],
            [1215, 917], [1210, 932], [1205, 881], [1195, 912],
            [1190, 892], [1185, 892], [1180, 858], [1175, 894],
            [1170, 887], [1165, 869], [1160, 872], [1150, 852],
            [1145, 855], [1140, 822], [970, 674], [965, 661],
            [905, 614], [900, 657], [885, 656], [880, 651],
            [875, 651], [870, 608], [865, 608], [860, 652],
            [855, 652], [850, 633], [845, 635], [840, 605],
            [815, 594], [795, 564], [790, 588], [775, 550],
            [710, 499], [405, 503], [390, 525], [385, 567],
            [365, 573], [150, 939], [145, 1085], [0, 1085],
        ],
    },
    {
        "id": "kitchen",
        "label": "Kitchen",
        "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
        "horizon": 88,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 782], [1395, 742],
            [1390, 720], [1385, 716], [1380, 726], [1375, 706],
            [1215, 590], [1205, 590], [1200, 577], [1105, 512],
            [435, 513], [245, 660], [220, 692], [215, 691],
            [205, 704], [155, 745], [150, 742], [145, 749],
            [140, 748], [35, 834], [30, 855], [25, 860],
            [0, 860],
        ],
    },
    {
        "id": "bathroom",
        "label": "Bathroom",
        "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
        "horizon": 182,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 735], [1415, 717],
            [1385, 717], [1360, 707], [1355, 701], [1305, 679],
            [1270, 595], [1210, 565], [1120, 566], [1115, 638],
            [1110, 565], [1005, 566], [965, 536], [920, 536],
            [915, 549], [910, 550], [905, 559], [900, 549],
            [895, 548], [890, 536], [860, 536], [850, 552],
            [840, 555], [590, 554], [570, 535], [510, 535],
            [500, 545], [475, 546], [455, 537], [435, 535],
            [410, 549], [405, 592], [390, 603], [385, 623],
            [380, 626], [360, 666], [350, 672], [345, 684],
            [340, 685], [335, 695], [320, 712], [310, 719],
            [295, 756], [290, 756], [285, 762], [270, 770],
            [265, 780], [260, 780], [255, 788], [250, 788],
            [245, 792], [240, 792], [235, 802], [220, 809],
            [215, 819], [210, 820], [195, 832], [190, 833],
            [185, 840], [170, 850], [150, 870], [145, 870],
            [135, 876], [125, 888], [120, 884], [115, 891],
            [105, 894], [100, 902], [85, 912], [75, 912],
            [65, 924], [55, 929], [40, 944], [35, 944],
            [20, 952], [15, 1032], [0, 1046],
        ],
    },
    {
        "id": "patio",
        "label": "Patio",
        "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
        "horizon": 133,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 586], [1440, 581],
            [1430, 578], [1425, 571], [1420, 571], [1330, 517],
            [1325, 517], [1315, 508], [1305, 505], [1275, 486],
            [1255, 480], [1205, 451], [1190, 466], [1155, 464],
            [1150, 458], [1145, 461], [1130, 449], [1115, 410],
            [1030, 365], [1025, 345], [1020, 360], [1000, 352],
            [970, 347], [965, 354], [955, 355], [950, 352],
            [940, 352], [935, 346], [930, 348], [820, 348],
            [810, 358], [795, 364], [750, 361], [745, 368],
            [740, 408], [725, 419], [695, 423], [655, 421],
            [625, 408], [620, 357], [615, 384], [610, 387],
            [605, 375], [545, 407], [540, 426], [530, 438],
            [525, 418], [520, 440], [515, 425], [505, 469],
            [470, 473], [465, 444], [460, 454], [440, 451],
            [435, 426], [360, 425], [350, 432], [345, 453],
            [340, 437], [325, 443], [320, 503], [295, 509],
            [235, 518], [230, 543], [170, 575], [125, 576],
            [115, 598], [90, 634], [80, 641], [75, 852],
            [0, 920],
        ],
    },
    {
        "id": "kitchen-dining",
        "label": "Kitchen and dining",
        "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
        "horizon": 142,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 690], [1440, 688],
            [1435, 573], [1430, 551], [1405, 550], [1400, 608],
            [1390, 551], [1385, 559], [1375, 555], [1370, 571],
            [1365, 553], [1360, 551], [1355, 556], [1350, 641],
            [1345, 663], [1340, 546], [1335, 547], [1330, 542],
            [1290, 526], [1285, 536], [1280, 564], [1275, 518],
            [1270, 619], [1265, 566], [1260, 662], [1255, 625],
            [1250, 608], [1245, 690], [1225, 687], [1220, 548],
            [1210, 547], [1205, 592], [1200, 549], [1195, 564],
            [1190, 549], [1180, 547], [1150, 551], [1145, 563],
            [1125, 663], [1120, 542], [1105, 589], [1100, 560],
            [1090, 608], [1085, 580], [1080, 580], [1075, 506],
            [1065, 500], [995, 497], [965, 499], [960, 496],
            [950, 499], [940, 496], [925, 498], [915, 497],
            [475, 497], [235, 670], [230, 688], [215, 688],
            [150, 733], [145, 751], [140, 738], [135, 755],
            [130, 761], [120, 765], [110, 756], [105, 760],
            [90, 764], [80, 783], [75, 782], [65, 795],
            [50, 806], [45, 804], [30, 822], [20, 827],
            [10, 819], [5, 832], [0, 827],
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
    stamped = []
    for s in SCENES:
        s = dict(s)
        s["image"] = "%s?v=%s" % (s["image"], hooks.ASSET_VERSION)
        stamped.append(s)
    context.aab_scenes_json = frappe.as_json(stamped)
    context.aab_tile_count = len(tiles)

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
