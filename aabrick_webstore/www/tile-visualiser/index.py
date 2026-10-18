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
            [0, 1085], [1447, 1085], [1446, 1085], [1424, 1085],
            [1422, 885], [1416, 876], [1410, 859], [1408, 855],
            [1380, 855], [1254, 861], [1252, 860], [1218, 856],
            [1188, 843], [1176, 832], [1170, 814], [1142, 734],
            [1140, 729], [1134, 710], [1132, 707], [1130, 698],
            [1120, 662], [1062, 627], [1016, 600], [996, 589],
            [902, 589], [900, 649], [884, 649], [882, 590],
            [778, 590], [776, 591], [774, 713], [772, 708],
            [770, 687], [768, 707], [766, 591], [722, 591],
            [720, 596], [718, 597], [716, 591], [532, 591],
            [482, 592], [478, 605], [466, 626], [450, 631],
            [428, 632], [408, 652], [212, 863], [188, 889],
            [174, 905], [120, 907], [118, 909], [110, 907],
            [108, 909], [96, 909], [94, 912], [90, 910],
            [88, 916], [86, 912], [84, 911], [68, 912],
            [36, 940], [0, 974],
        ]},
        {"id": "bathroom", "label": "Bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
         "horizon": 247, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1446, 832], [1434, 827],
            [1420, 814], [1412, 800], [1410, 794], [1408, 779],
            [1406, 778], [1378, 778], [1284, 781], [1282, 780],
            [1252, 774], [1230, 762], [1224, 754], [1218, 736],
            [1204, 696], [1202, 691], [1200, 684], [1188, 648],
            [1182, 627], [1180, 621], [1178, 610], [1176, 557],
            [1098, 517], [972, 517], [970, 539], [968, 615],
            [966, 553], [964, 517], [894, 517], [892, 533],
            [890, 517], [820, 517], [800, 539], [790, 546],
            [784, 552], [742, 555], [740, 556], [680, 556],
            [678, 557], [676, 556], [576, 556], [574, 555],
            [534, 553], [518, 545], [500, 528], [492, 518],
            [490, 517], [454, 517], [440, 518], [434, 532],
            [428, 542], [412, 546], [394, 546], [390, 548],
            [280, 620], [64, 765], [52, 774], [38, 774],
            [36, 776], [34, 774], [12, 787], [0, 795],
        ]},
        {"id": "kitchen", "label": "Kitchen",
         "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
         "horizon": 351, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1446, 863], [1444, 861],
            [1442, 851], [1436, 847], [1430, 847], [1428, 850],
            [1426, 847], [1418, 842], [1416, 842], [1410, 836],
            [1396, 825], [1386, 819], [1376, 817], [1370, 817],
            [1358, 807], [1356, 806], [1352, 806], [1350, 788],
            [1348, 786], [1258, 720], [1248, 713], [1244, 711],
            [1238, 705], [1202, 680], [1198, 678], [1188, 677],
            [1186, 666], [1184, 664], [1094, 599], [1088, 596],
            [448, 596], [400, 597], [392, 600], [390, 604],
            [388, 604], [384, 607], [224, 737], [220, 741],
            [218, 744], [216, 749], [212, 752], [210, 755],
            [208, 756], [160, 795], [154, 801], [150, 803],
            [138, 812], [134, 816], [122, 817], [40, 883],
            [36, 887], [34, 892], [32, 905], [30, 907],
            [26, 909], [0, 909],
        ]},
        {"id": "kitchen-dining", "label": "Kitchen and dining",
         "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
         "horizon": 279, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [0, 1086], [1446, 1086], [1446, 604], [1380, 571],
            [1378, 569], [1364, 562], [1362, 558], [1360, 556],
            [1358, 555], [1356, 558], [1354, 550], [1352, 556],
            [1350, 555], [1348, 546], [1346, 546], [1344, 552],
            [1342, 546], [1340, 550], [1338, 543], [1336, 547],
            [1332, 545], [1330, 541], [1328, 543], [1260, 508],
            [1092, 508], [1086, 505], [1032, 505], [1030, 506],
            [1024, 504], [470, 504], [464, 507], [436, 527],
            [336, 600], [232, 677], [228, 681], [226, 693],
            [208, 693], [144, 739], [142, 755], [136, 757],
            [122, 767], [110, 769], [96, 775], [90, 779],
            [86, 784], [84, 784], [68, 795], [64, 799],
            [62, 802], [60, 802], [56, 804], [54, 808],
            [50, 809], [44, 812], [42, 814], [40, 818],
            [32, 821], [30, 825], [26, 825], [22, 828],
            [20, 832], [16, 833], [12, 836], [6, 842],
            [4, 841], [0, 844],
        ]},
        {"id": "living", "label": "Living room",
         "image": "/assets/aabrick_webstore/images/scene-living.jpg",
         "horizon": 309, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1446, 647], [1416, 632],
            [1300, 577], [1182, 523], [1094, 484], [1076, 484],
            [1072, 490], [1052, 491], [1050, 490], [1042, 489],
            [1038, 484], [1036, 483], [964, 480], [944, 480],
            [942, 520], [940, 524], [938, 522], [936, 478],
            [828, 478], [826, 479], [824, 512], [820, 514],
            [818, 522], [798, 523], [796, 516], [794, 514],
            [748, 514], [730, 520], [726, 520], [694, 525],
            [692, 574], [680, 581], [654, 586], [652, 587],
            [594, 589], [592, 588], [562, 585], [548, 580],
            [544, 577], [542, 527], [512, 524], [464, 525],
            [456, 530], [454, 532], [450, 532], [440, 535],
            [422, 546], [410, 549], [406, 553], [396, 557],
            [394, 560], [384, 564], [380, 568], [374, 570],
            [346, 587], [344, 590], [342, 590], [322, 600],
            [312, 606], [310, 609], [308, 609], [300, 612],
            [290, 619], [288, 630], [272, 641], [270, 643],
            [236, 643], [234, 644], [228, 641], [196, 640],
            [110, 642], [70, 644], [64, 645], [62, 647],
            [48, 668], [42, 674], [22, 683], [2, 687],
            [0, 688],
        ]},
        {"id": "patio", "label": "Veranda",
         "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
         "horizon": 349, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [0, 1085], [1447, 1085], [1446, 674], [1362, 636],
            [1282, 601], [1276, 599], [1272, 598], [1250, 598],
            [1162, 599], [1120, 577], [1118, 542], [1024, 497],
            [1008, 490], [960, 490], [950, 485], [932, 484],
            [486, 484], [482, 486], [462, 500], [452, 500],
            [444, 505], [406, 530], [400, 535], [388, 541],
            [368, 555], [366, 573], [354, 580], [338, 591],
            [332, 596], [326, 599], [308, 599], [290, 608],
            [278, 616], [270, 623], [268, 623], [264, 625],
            [252, 633], [250, 636], [244, 638], [226, 652],
            [212, 659], [204, 664], [200, 668], [184, 676],
            [180, 679], [178, 682], [176, 682], [170, 685],
            [166, 690], [164, 690], [162, 693], [156, 695],
            [152, 699], [150, 699], [130, 709], [128, 712],
            [124, 713], [122, 718], [118, 721], [116, 720],
            [114, 721], [112, 724], [108, 723], [104, 724],
            [88, 734], [86, 737], [84, 737], [80, 739],
            [78, 747], [76, 743], [66, 748], [64, 756],
            [62, 754], [60, 756], [58, 760], [56, 758],
            [54, 763], [52, 759], [48, 760], [44, 765],
            [36, 767], [34, 771], [30, 771], [22, 775],
            [18, 778], [16, 787], [14, 782], [8, 785],
            [6, 788], [4, 787], [2, 788], [0, 791],
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
