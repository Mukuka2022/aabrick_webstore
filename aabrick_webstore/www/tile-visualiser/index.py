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
         "horizon": 253, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [-2, 1087], [1449, 1087], [1449, 1053], [1446, 1053],
            [1434, 1042], [1370, 987], [1284, 914], [1134, 788],
            [1028, 700], [986, 666], [942, 632], [934, 628],
            [922, 625], [918, 621], [916, 609], [910, 607],
            [848, 607], [820, 599], [814, 594], [794, 562],
            [792, 561], [780, 561], [778, 553], [776, 551],
            [712, 500], [708, 498], [694, 498], [404, 502],
            [402, 504], [390, 524], [388, 525], [386, 566],
            [382, 566], [380, 546], [376, 546], [374, 547],
            [372, 550], [366, 550], [364, 552], [310, 632],
            [172, 839], [146, 879], [144, 1085], [0, 1085],
            [-2, 1085],
        ]},
        {"id": "bathroom", "label": "Bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom.jpg",
         "horizon": 247, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [-2, 1088], [1448, 1088], [1448, 832], [1446, 832],
            [1434, 827], [1420, 814], [1412, 800], [1410, 794],
            [1408, 779], [1406, 778], [1378, 778], [1284, 781],
            [1282, 780], [1252, 774], [1230, 762], [1224, 754],
            [1218, 736], [1204, 696], [1202, 691], [1200, 684],
            [1188, 648], [1182, 627], [1180, 621], [1178, 610],
            [1176, 557], [1098, 517], [972, 517], [970, 539],
            [968, 615], [966, 553], [964, 517], [894, 517],
            [892, 533], [890, 517], [820, 517], [800, 539],
            [790, 546], [784, 552], [742, 555], [740, 556],
            [680, 556], [678, 557], [676, 556], [576, 556],
            [574, 555], [534, 553], [518, 545], [500, 528],
            [492, 518], [490, 517], [454, 517], [440, 518],
            [434, 532], [428, 542], [412, 546], [394, 546],
            [390, 548], [280, 620], [64, 765], [52, 774],
            [38, 774], [36, 776], [34, 774], [12, 787],
            [0, 795], [-2, 795],
        ]},
        {"id": "bathroom-family", "label": "Family bathroom",
         "image": "/assets/aabrick_webstore/images/scene-bathroom-family.jpg",
         "horizon": 347, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [-2, 1088], [1448, 1088], [1448, 901], [1446, 901],
            [1440, 902], [1438, 900], [1414, 894], [1402, 888],
            [1390, 878], [1388, 877], [1378, 866], [1368, 848],
            [1364, 838], [1362, 830], [1360, 818], [1358, 788],
            [1248, 730], [1240, 730], [1234, 727], [1232, 742],
            [1230, 745], [1226, 746], [1224, 723], [1222, 723],
            [1220, 714], [1174, 690], [1102, 654], [1024, 617],
            [994, 617], [978, 618], [976, 686], [956, 686],
            [954, 619], [836, 622], [834, 640], [832, 644],
            [828, 640], [826, 646], [824, 643], [822, 623],
            [800, 623], [708, 626], [706, 644], [704, 645],
            [702, 627], [592, 630], [580, 675], [576, 679],
            [572, 680], [566, 683], [550, 685], [548, 686],
            [520, 686], [518, 685], [504, 683], [494, 678],
            [490, 672], [482, 636], [478, 634], [424, 635],
            [418, 636], [416, 650], [390, 711], [368, 764],
            [364, 774], [362, 780], [356, 792], [328, 855],
            [320, 871], [304, 905], [270, 979], [232, 982],
            [230, 983], [210, 983], [136, 987], [128, 988],
            [126, 989], [100, 989], [76, 990], [72, 992],
            [28, 1051], [8, 1079], [2, 1086], [0, 1086],
            [-2, 1086],
        ]},
        {"id": "kitchen", "label": "Kitchen",
         "image": "/assets/aabrick_webstore/images/scene-kitchen.jpg",
         "horizon": 280, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [-2, 1087], [1449, 1087], [1449, 914], [1446, 914],
            [1382, 856], [1332, 812], [1328, 810], [1314, 810],
            [1308, 807], [1306, 804], [1304, 780], [1298, 774],
            [1246, 728], [1118, 617], [1032, 545], [1030, 544],
            [1014, 543], [1002, 532], [994, 526], [874, 526],
            [870, 528], [786, 528], [784, 529], [782, 528],
            [744, 528], [742, 526], [672, 525], [410, 525],
            [390, 526], [382, 531], [312, 585], [262, 624],
            [216, 661], [210, 667], [208, 681], [206, 683],
            [192, 684], [188, 686], [168, 701], [134, 728],
            [132, 761], [124, 771], [122, 785], [118, 788],
            [116, 791], [114, 787], [110, 788], [108, 790],
            [106, 796], [104, 795], [100, 800], [98, 798],
            [92, 805], [90, 804], [88, 805], [86, 810],
            [84, 809], [80, 811], [78, 818], [76, 818],
            [72, 820], [70, 824], [62, 826], [56, 832],
            [54, 837], [50, 837], [46, 846], [44, 846],
            [42, 849], [36, 851], [28, 861], [20, 862],
            [16, 869], [12, 869], [10, 876], [8, 877],
            [6, 874], [4, 876], [2, 882], [0, 879],
            [-2, 879],
        ]},
        {"id": "hallway", "label": "Hallway",
         "image": "/assets/aabrick_webstore/images/scene-hallway.jpg",
         "horizon": 330, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
             [-2, 1087],
             [1449, 1087],
             [1449, 1037],
             [1446, 1036],
             [1390, 983],
             [1286, 887],
             [1246, 852],
             [1244, 801],
             [1192, 758],
             [1186, 753],
             [1136, 752],
             [1120, 736],
             [1084, 704],
             [1074, 695],
             [1070, 691],
             [1068, 689],
             [1062, 684],
             [1060, 682],
             [1058, 680],
             [1048, 671],
             [1028, 654],
             [1026, 652],
             [1022, 648],
             [1018, 645],
             [1016, 643],
             [1014, 640],
             [992, 621],
             [988, 617],
             [986, 615],
             [982, 612],
             [950, 583],
             [946, 581],
             [944, 560],
             [942, 558],
             [932, 551],
             [914, 551],
             [906, 545],
             [900, 539],
             [898, 538],
             [896, 536],
             [894, 534],
             [892, 532],
             [888, 529],
             [886, 527],
             [870, 512],
             [854, 500],
             [816, 499],
             [810, 506],
             [804, 506],
             [800, 507],
             [798, 506],
             [782, 505],
             [770, 499],
             [672, 498],
             [562, 490],
             [560, 502],
             [556, 502],
             [554, 499],
             [544, 516],
             [542, 518],
             [534, 525],
             [492, 564],
             [482, 573],
             [480, 576],
             [474, 580],
             [450, 581],
             [442, 588],
             [438, 591],
             [436, 611],
             [422, 620],
             [400, 636],
             [394, 642],
             [392, 713],
             [388, 715],
             [386, 655],
             [382, 651],
             [378, 654],
             [372, 659],
             [370, 660],
             [366, 663],
             [360, 668],
             [358, 671],
             [354, 674],
             [346, 680],
             [344, 682],
             [340, 684],
             [338, 687],
             [336, 688],
             [334, 689],
             [332, 714],
             [330, 714],
             [328, 694],
             [324, 697],
             [322, 699],
             [302, 713],
             [298, 716],
             [290, 722],
             [282, 729],
             [280, 731],
             [276, 734],
             [264, 744],
             [260, 748],
             [258, 868],
             [256, 871],
             [250, 872],
             [248, 761],
             [244, 763],
             [234, 772],
             [190, 809],
             [182, 818],
             [180, 819],
             [160, 836],
             [144, 850],
             [138, 856],
             [136, 872],
             [122, 872],
             [110, 872],
             [0, 970],
             [-2, 971]
         ]},
        {"id": "kitchen-dining", "label": "Kitchen and dining",
         "image": "/assets/aabrick_webstore/images/scene-kitchen-dining.jpg",
         "horizon": 279, "cx": 723, "focal": 930, "height": 1.45,
         "floor": [
            [-2, 1088], [1448, 1088], [1448, 604], [1446, 604],
            [1292, 524], [1260, 508], [1092, 508], [1086, 505],
            [1032, 505], [1030, 506], [1024, 504], [470, 504],
            [464, 507], [436, 527], [336, 600], [232, 677],
            [228, 681], [226, 693], [208, 693], [144, 739],
            [142, 755], [136, 757], [122, 767], [110, 769],
            [96, 775], [90, 779], [86, 784], [84, 784],
            [68, 795], [64, 799], [62, 802], [60, 802],
            [56, 804], [54, 808], [50, 809], [44, 812],
            [42, 814], [40, 818], [32, 821], [30, 825],
            [26, 825], [22, 828], [20, 832], [16, 833],
            [12, 836], [6, 842], [4, 841], [0, 844],
            [-2, 844],
        ]},
        {"id": "living", "label": "Living room",
         "image": "/assets/aabrick_webstore/images/scene-living.jpg",
         "horizon": 309, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [-2, 1087], [1449, 1087], [1449, 647], [1446, 647],
            [1416, 632], [1300, 577], [1182, 523], [1094, 484],
            [1076, 484], [1072, 490], [1052, 491], [1050, 490],
            [1042, 489], [1038, 484], [1036, 483], [964, 480],
            [952, 481], [950, 480], [940, 480], [938, 478],
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
            [0, 688], [-2, 688],
        ]},
        {"id": "patio", "label": "Veranda",
         "image": "/assets/aabrick_webstore/images/scene-patio.jpg",
         "horizon": 349, "cx": 724, "focal": 931, "height": 1.45,
         "floor": [
            [-2, 1087], [1449, 1087], [1449, 674], [1446, 674],
            [1362, 636], [1282, 601], [1276, 599], [1272, 598],
            [1250, 598], [1162, 599], [1120, 577], [1118, 542],
            [1024, 497], [1008, 490], [960, 490], [950, 485],
            [932, 484], [486, 484], [482, 486], [462, 500],
            [452, 500], [444, 505], [406, 530], [400, 535],
            [388, 541], [368, 555], [366, 573], [354, 580],
            [338, 591], [332, 596], [326, 599], [308, 599],
            [290, 608], [278, 616], [270, 623], [268, 623],
            [264, 625], [252, 633], [250, 636], [244, 638],
            [226, 652], [212, 659], [204, 664], [200, 668],
            [184, 676], [180, 679], [178, 682], [176, 682],
            [170, 685], [166, 690], [164, 690], [162, 693],
            [156, 695], [152, 699], [150, 699], [130, 709],
            [128, 712], [124, 713], [122, 718], [118, 721],
            [116, 720], [114, 721], [112, 724], [108, 723],
            [104, 724], [88, 734], [86, 737], [84, 737],
            [80, 739], [78, 747], [76, 743], [66, 748],
            [64, 756], [62, 754], [60, 756], [58, 760],
            [56, 758], [54, 763], [52, 759], [48, 760],
            [44, 765], [36, 767], [34, 771], [30, 771],
            [22, 775], [18, 778], [16, 787], [14, 782],
            [8, 785], [6, 788], [4, 787], [2, 788],
            [0, 791], [-2, 791],
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
        "bathroom-family",
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
