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
        "horizon": 168,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 577], [1385, 561],
            [1335, 563], [1305, 560], [1195, 516], [1080, 466],
            [1075, 469], [1070, 480], [1060, 480], [1055, 473],
            [1050, 443], [1040, 439], [920, 434], [915, 444],
            [880, 442], [870, 433], [865, 462], [860, 469],
            [795, 472], [790, 518], [785, 521], [725, 526],
            [715, 524], [710, 526], [650, 520], [645, 472],
            [505, 475], [495, 476], [415, 538], [225, 542],
            [110, 538], [90, 547], [65, 548], [20, 566],
            [15, 576], [0, 581],
        ],
    },
    {
        "id": "ensuite",
        "label": "Ensuite",
        "image": "/assets/aabrick_webstore/images/scene-ensuite.jpg",
        "horizon": 92,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 1085], [1375, 1085],
            [1365, 1077], [1360, 1065], [1355, 1080], [1345, 1081],
            [1340, 1076], [1335, 1047], [1330, 1046], [1325, 1034],
            [1300, 1009], [1295, 1007], [1290, 996], [1285, 992],
            [1280, 992], [1270, 973], [1265, 977], [1250, 952],
            [1245, 953], [1230, 941], [1225, 929], [1220, 930],
            [1215, 925], [1210, 925], [1205, 916], [1200, 916],
            [1195, 882], [1185, 884], [1180, 880], [1175, 884],
            [1170, 883], [1165, 869], [1160, 864], [1155, 849],
            [1150, 849], [1145, 841], [1135, 836], [1130, 824],
            [1120, 814], [1115, 801], [1110, 800], [1105, 793],
            [970, 674], [965, 662], [935, 639], [870, 640],
            [840, 628], [835, 604], [815, 594], [795, 563],
            [370, 570], [365, 575], [150, 940], [145, 1085],
            [0, 1085],
        ],
    },
    {
        "id": "kitchen",
        "label": "Kitchen",
        "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
        "horizon": 91,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 782], [1390, 738],
            [1385, 727], [1380, 727], [1375, 710], [1360, 696],
            [1215, 591], [1205, 591], [1200, 579], [1110, 518],
            [1105, 525], [1100, 526], [1095, 522], [1055, 515],
            [605, 518], [595, 515], [590, 518], [575, 519],
            [570, 522], [525, 531], [515, 530], [495, 536],
            [480, 536], [475, 540], [470, 537], [460, 544],
            [455, 540], [445, 552], [440, 552], [435, 547],
            [410, 552], [405, 560], [370, 578], [365, 588],
            [355, 591], [345, 606], [340, 605], [325, 614],
            [320, 624], [315, 628], [310, 624], [300, 632],
            [290, 648], [285, 644], [265, 656], [260, 661],
            [250, 665], [235, 696], [230, 696], [220, 708],
            [215, 709], [210, 716], [190, 728], [180, 742],
            [170, 744], [165, 750], [160, 749], [150, 758],
            [145, 771], [140, 766], [85, 816], [80, 816],
            [70, 832], [65, 833], [60, 844], [25, 860],
            [0, 860],
        ],
    },
    {
        "id": "bathroom",
        "label": "Bathroom",
        "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
        "horizon": 181,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 761], [1420, 760],
            [1415, 750], [1410, 751], [1390, 740], [1385, 718],
            [1375, 713], [1370, 704], [1365, 704], [1310, 680],
            [1290, 647], [1280, 617], [1270, 614], [1265, 647],
            [1260, 609], [1255, 647], [1250, 647], [1245, 600],
            [1200, 576], [1195, 567], [1175, 567], [1170, 647],
            [1165, 567], [1120, 567], [1115, 647], [1110, 566],
            [1005, 567], [980, 549], [975, 550], [970, 539],
            [965, 548], [960, 546], [930, 546], [915, 553],
            [910, 561], [905, 563], [895, 558], [885, 557],
            [625, 559], [595, 536], [590, 540], [580, 542],
            [570, 534], [555, 536], [550, 544], [535, 544],
            [530, 536], [520, 535], [515, 545], [475, 546],
            [470, 536], [440, 535], [410, 550], [405, 593],
            [400, 601], [395, 602], [385, 648], [375, 672],
            [370, 675], [365, 684], [355, 690], [350, 703],
            [345, 704], [340, 714], [335, 716], [325, 728],
            [320, 718], [315, 744], [305, 756], [300, 776],
            [295, 780], [290, 780], [285, 784], [280, 796],
            [260, 800], [240, 816], [235, 816], [230, 824],
            [225, 824], [215, 840], [210, 840], [205, 849],
            [200, 848], [175, 872], [170, 872], [165, 876],
            [155, 876], [150, 884], [145, 880], [140, 880],
            [135, 896], [125, 896], [120, 903], [115, 904],
            [105, 920], [100, 920], [85, 933], [80, 929],
            [70, 928], [65, 939], [60, 940], [50, 954],
            [40, 956], [35, 964], [25, 966], [20, 975],
            [15, 1033], [0, 1046],
        ],
    },
    {
        "id": "patio",
        "label": "Patio",
        "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
        "horizon": 137,
        "cx": 723,
        "focal": 1462,
        "height": 1.45,
        "floor": [
            [0, 1086], [1446, 1086], [1445, 586], [1240, 471],
            [1215, 466], [1210, 455], [1205, 454], [1200, 468],
            [1140, 464], [1130, 451], [1115, 411], [1035, 368],
            [1025, 370], [1015, 366], [1010, 356], [990, 349],
            [975, 349], [965, 368], [955, 367], [950, 360],
            [940, 362], [930, 350], [820, 349], [815, 355],
            [810, 385], [805, 359], [795, 365], [790, 385],
            [785, 365], [750, 363], [745, 369], [740, 420],
            [735, 422], [630, 421], [625, 409], [620, 351],
            [615, 388], [605, 374], [590, 382], [585, 419],
            [570, 427], [565, 437], [560, 437], [530, 451],
            [520, 460], [510, 464], [505, 469], [460, 473],
            [455, 454], [445, 454], [435, 474], [400, 478],
            [390, 478], [385, 500], [365, 501], [360, 427],
            [350, 432], [340, 497], [310, 501], [290, 507],
            [270, 513], [235, 517], [230, 544], [175, 574],
            [125, 576], [120, 589], [100, 623], [95, 644],
            [90, 648], [75, 650], [70, 855], [55, 869],
            [50, 870], [15, 904], [0, 914],
        ],
    },
    {
        "id": "kitchen-dining",
        "label": "Kitchen and dining",
        "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
        "horizon": 146,
        "cx": 724,
        "focal": 1463,
        "height": 1.45,
        "floor": [
            [0, 1085], [1447, 1085], [1445, 692], [1440, 689],
            [1435, 575], [1410, 564], [1405, 625], [1400, 619],
            [1390, 564], [1385, 561], [1380, 616], [1360, 553],
            [1350, 649], [1345, 669], [1340, 592], [1330, 545],
            [1290, 529], [1270, 626], [1265, 568], [1260, 672],
            [1250, 689], [1240, 692], [1225, 688], [1220, 550],
            [1215, 550], [1210, 624], [1205, 662], [1195, 664],
            [1190, 550], [1170, 551], [1165, 592], [1160, 552],
            [1150, 554], [1145, 569], [1125, 668], [1120, 548],
            [1095, 636], [1090, 622], [1085, 622], [1080, 581],
            [1075, 578], [1070, 593], [1065, 502], [1030, 500],
            [945, 501], [940, 504], [930, 502], [925, 504],
            [920, 502], [750, 500], [685, 502], [560, 504],
            [550, 511], [545, 505], [470, 518], [460, 520],
            [455, 524], [425, 534], [340, 598], [235, 673],
            [230, 689], [200, 698], [150, 735], [145, 753],
            [60, 810], [40, 824], [20, 842], [0, 851],
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
