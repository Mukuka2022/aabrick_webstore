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
    # Six rooms, photographed for this with the floor left clear, which is
    # most of why the outlines below are as close as they are. Every one is
    # 1448 by 1086.
    #
    # The floor outline is traced rather than drawn: each column of the
    # photograph is walked up from the bottom and stops where the colour
    # departs from the floor just below it, which finds a skirting board even
    # where a pale wall meets a pale floor. A column that never starts on
    # floor, the door in the ensuite, is left out of the outline entirely.
    #
    # The horizon and the lens centre are the point the two side walls of the
    # room converge on, found by fitting a line to each side of the traced
    # boundary and intersecting them. The focal length is a 53 degree field of
    # view across the frame. The height is the camera off the floor, and it is
    # the one number here set by eye, against something of known size in the
    # picture.
    {
        "id": "living",
        "label": "Living room",
        "image": "/assets/aabrick_webstore/images/scene-living.jpg",
        "horizon": 320,
        "cx": 905,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 554], [1434, 558],
            [1404, 550], [1398, 552], [1392, 538], [1386, 556],
            [1380, 558], [1362, 554], [1356, 548], [1242, 499],
            [1236, 499], [1200, 482], [1182, 477], [1176, 471],
            [1098, 436], [1092, 443], [1074, 436], [1002, 430],
            [996, 420], [984, 420], [978, 425], [966, 419],
            [804, 424], [798, 418], [792, 426], [768, 424],
            [762, 459], [756, 459], [744, 480], [738, 479],
            [732, 508], [726, 502], [720, 511], [714, 514],
            [708, 525], [660, 532], [654, 523], [570, 522],
            [564, 527], [552, 526], [546, 517], [528, 512],
            [516, 474], [480, 481], [474, 477], [444, 484],
            [438, 479], [414, 492], [354, 540], [348, 538],
            [342, 551], [336, 549], [330, 558], [324, 554],
            [300, 565], [156, 570], [90, 589], [0, 607],
        ],
    },
    {
        "id": "ensuite",
        "label": "Ensuite",
        "image": "/assets/aabrick_webstore/images/scene-ensuite.jpg",
        "horizon": 330,
        "cx": 700,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 631], [1440, 966],
            [1434, 961], [1428, 961], [1422, 955], [1416, 955],
            [1410, 950], [1404, 950], [1398, 945], [1392, 1004],
            [1218, 850], [1212, 875], [1020, 696], [1014, 682],
            [996, 661], [990, 668], [954, 669], [948, 658],
            [942, 659], [936, 670], [930, 659], [924, 661],
            [918, 671], [912, 660], [906, 659], [894, 650],
            [888, 650], [882, 589], [876, 583], [846, 579],
            [840, 589], [834, 579], [828, 582], [804, 579],
            [786, 579], [732, 584], [726, 580], [690, 581],
            [684, 586], [678, 581], [666, 581], [660, 586],
            [618, 582], [408, 587], [402, 562], [396, 567],
            [174, 916], [168, 1085], [0, 1085],
        ],
    },
    {
        "id": "kitchen",
        "label": "Kitchen",
        "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
        "horizon": 300,
        "cx": 735,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 797], [1362, 725],
            [1356, 710], [1194, 589], [1182, 587], [1176, 575],
            [1092, 516], [1086, 517], [1080, 510], [516, 521],
            [510, 526], [444, 544], [420, 545], [408, 556],
            [390, 566], [366, 574], [354, 588], [348, 587],
            [324, 606], [312, 609], [294, 633], [264, 650],
            [228, 690], [222, 691], [198, 716], [192, 717],
            [174, 735], [144, 754], [108, 793], [102, 790],
            [66, 826], [60, 852], [42, 862], [0, 866],
        ],
    },
    {
        "id": "bathroom",
        "label": "Bathroom",
        "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
        "horizon": 300,
        "cx": 820,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 876], [1440, 827],
            [1434, 865], [1428, 858], [1422, 818], [1416, 850],
            [1374, 813], [1368, 790], [1362, 802], [1344, 786],
            [1338, 762], [1332, 756], [1326, 756], [1320, 764],
            [1314, 762], [1134, 607], [1122, 604], [1110, 582],
            [1104, 582], [1098, 552], [1092, 572], [1086, 569],
            [1080, 540], [1038, 537], [1032, 533], [1026, 475],
            [996, 475], [990, 524], [984, 471], [978, 466],
            [948, 468], [942, 477], [936, 466], [918, 469],
            [912, 475], [876, 474], [864, 485], [840, 495],
            [744, 502], [732, 499], [582, 487], [576, 498],
            [564, 498], [558, 479], [504, 477], [486, 485],
            [396, 575], [390, 573], [366, 579], [360, 572],
            [294, 572], [288, 577], [246, 577], [234, 572],
            [216, 576], [210, 572], [198, 576], [174, 608],
            [168, 577], [144, 608], [138, 630], [132, 676],
            [0, 679],
        ],
    },
    {
        "id": "patio",
        "label": "Patio",
        "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
        "horizon": 180,
        "cx": 700,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 600], [1356, 549],
            [1350, 543], [1344, 542], [1338, 552], [1332, 553],
            [1326, 530], [1194, 459], [1182, 451], [1140, 448],
            [1086, 442], [1074, 430], [1062, 397], [1044, 381],
            [1032, 375], [1026, 377], [1020, 368], [1014, 365],
            [1008, 369], [1002, 359], [996, 361], [984, 350],
            [972, 352], [966, 344], [954, 337], [924, 338],
            [918, 342], [876, 337], [870, 330], [822, 330],
            [816, 361], [804, 361], [798, 365], [762, 366],
            [744, 369], [732, 366], [726, 400], [708, 400],
            [702, 406], [672, 409], [594, 404], [588, 409],
            [582, 402], [552, 407], [540, 433], [510, 436],
            [480, 449], [396, 454], [390, 469], [384, 474],
            [366, 478], [360, 490], [342, 499], [312, 496],
            [306, 502], [264, 506], [258, 489], [252, 491],
            [246, 509], [240, 491], [228, 517], [222, 517],
            [210, 539], [204, 543], [156, 547], [150, 550],
            [132, 547], [126, 586], [96, 593], [90, 779],
            [84, 779], [78, 802], [0, 873],
        ],
    },
    {
        "id": "kitchen-dining",
        "label": "Kitchen and dining",
        "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
        "horizon": 300,
        "cx": 640,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1446, 724], [1440, 745],
            [1434, 690], [1428, 689], [1422, 695], [1416, 753],
            [1410, 738], [1404, 752], [1398, 753], [1392, 692],
            [1374, 685], [1356, 683], [1350, 640], [1344, 705],
            [1332, 685], [1326, 700], [1320, 607], [1314, 624],
            [1308, 626], [1302, 683], [1296, 626], [1284, 626],
            [1278, 634], [1272, 656], [1254, 656], [1248, 687],
            [1200, 687], [1194, 622], [1182, 656], [1176, 622],
            [1170, 626], [1128, 621], [1122, 601], [1116, 664],
            [1104, 663], [1098, 593], [1092, 590], [1086, 626],
            [1074, 618], [1068, 621], [1062, 618], [1050, 593],
            [1038, 511], [1026, 510], [1020, 497], [1008, 497],
            [1002, 510], [990, 508], [984, 511], [978, 508],
            [954, 508], [948, 497], [942, 507], [918, 507],
            [912, 517], [888, 515], [882, 496], [876, 522],
            [870, 496], [864, 496], [858, 503], [852, 496],
            [846, 496], [840, 503], [834, 496], [828, 518],
            [822, 522], [816, 496], [804, 517], [798, 496],
            [792, 522], [786, 496], [780, 517], [762, 517],
            [756, 503], [750, 517], [654, 519], [648, 495],
            [642, 495], [636, 517], [630, 495], [618, 495],
            [612, 516], [600, 517], [594, 495], [570, 495],
            [564, 516], [558, 495], [534, 495], [528, 516],
            [510, 516], [504, 495], [498, 517], [492, 495],
            [486, 516], [474, 518], [468, 525], [462, 525],
            [456, 516], [426, 533], [420, 518], [408, 524],
            [378, 533], [372, 558], [366, 558], [342, 575],
            [336, 594], [330, 583], [306, 600], [300, 620],
            [234, 669], [228, 685], [144, 742], [138, 755],
            [90, 789], [84, 801], [78, 798], [0, 856],
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
