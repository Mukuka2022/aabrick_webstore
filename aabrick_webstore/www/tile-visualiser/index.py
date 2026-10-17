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
            [0, 1085], [1447, 1085], [1440, 552], [1424, 552],
            [1408, 552], [1392, 552], [1376, 552], [1360, 544],
            [1344, 544], [1328, 539], [1312, 531], [1296, 524],
            [1280, 518], [1264, 512], [1248, 504], [1232, 496],
            [1216, 490], [1200, 482], [1184, 477], [1168, 467],
            [1152, 461], [1136, 454], [1120, 447], [1104, 442],
            [1088, 439], [1072, 436], [1056, 436], [1040, 435],
            [1024, 433], [1008, 430], [992, 424], [976, 420],
            [960, 420], [944, 424], [928, 424], [912, 424],
            [896, 425], [880, 425], [864, 425], [848, 425],
            [832, 425], [816, 425], [800, 425], [784, 425],
            [768, 425], [752, 468], [736, 508], [720, 511],
            [704, 519], [688, 521], [672, 523], [656, 523],
            [640, 523], [624, 523], [608, 523], [592, 524],
            [576, 523], [560, 522], [544, 516], [528, 512],
            [512, 477], [496, 476], [480, 476], [464, 477],
            [448, 479], [432, 480], [416, 491], [400, 503],
            [384, 516], [368, 529], [352, 540], [336, 549],
            [320, 555], [304, 562], [288, 566], [272, 566],
            [256, 566], [240, 569], [224, 571], [208, 560],
            [192, 560], [176, 560], [160, 560], [144, 559],
            [128, 559], [112, 559], [96, 559], [80, 589],
            [64, 595], [48, 600], [32, 603], [16, 605],
            [0, 605],
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
            [0, 1085], [1447, 1085], [1440, 629], [1424, 1004],
            [1408, 989], [1392, 989], [1376, 989], [1360, 975],
            [1344, 961], [1328, 947], [1312, 933], [1296, 919],
            [1280, 905], [1264, 891], [1248, 879], [1232, 877],
            [1216, 864], [1200, 863], [1184, 849], [1168, 834],
            [1152, 819], [1136, 804], [1120, 789], [1104, 775],
            [1088, 759], [1072, 744], [1056, 730], [1040, 715],
            [1024, 699], [1008, 672], [992, 668], [976, 667],
            [960, 667], [944, 659], [928, 659], [912, 659],
            [896, 626], [880, 524], [864, 524], [848, 524],
            [832, 574], [816, 579], [800, 579], [784, 579],
            [768, 579], [752, 580], [736, 580], [720, 580],
            [704, 581], [688, 581], [672, 581], [656, 583],
            [640, 583], [624, 583], [608, 583], [592, 583],
            [576, 583], [560, 583], [544, 583], [528, 583],
            [512, 584], [496, 584], [480, 584], [464, 585],
            [448, 585], [432, 585], [416, 585], [400, 585],
            [384, 586], [368, 611], [352, 637], [336, 662],
            [320, 687], [304, 712], [288, 737], [272, 763],
            [256, 787], [240, 813], [224, 838], [208, 863],
            [192, 888], [176, 913], [160, 1085], [144, 1085],
            [128, 1085], [112, 1085], [96, 1085], [80, 1085],
            [64, 1085], [48, 1085], [32, 1085], [16, 1085],
            [0, 1085],
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
            [0, 1085], [1447, 1085], [1440, 779], [1424, 779],
            [1408, 766], [1392, 753], [1376, 741], [1360, 713],
            [1344, 701], [1328, 689], [1312, 677], [1296, 665],
            [1280, 653], [1264, 641], [1248, 629], [1232, 617],
            [1216, 606], [1200, 594], [1184, 588], [1168, 569],
            [1152, 558], [1136, 546], [1120, 535], [1104, 524],
            [1088, 513], [1072, 510], [1056, 510], [1040, 510],
            [1024, 510], [1008, 510], [992, 510], [976, 510],
            [960, 510], [944, 510], [928, 510], [912, 510],
            [896, 510], [880, 510], [864, 510], [848, 510],
            [832, 510], [816, 510], [800, 510], [784, 510],
            [768, 510], [752, 510], [736, 510], [720, 510],
            [704, 511], [688, 511], [672, 511], [656, 511],
            [640, 511], [624, 511], [608, 511], [592, 511],
            [576, 511], [560, 511], [544, 511], [528, 510],
            [512, 510], [496, 510], [480, 510], [464, 510],
            [448, 510], [432, 510], [416, 521], [400, 534],
            [384, 548], [368, 561], [352, 575], [336, 588],
            [320, 602], [304, 615], [288, 628], [272, 642],
            [256, 656], [240, 675], [224, 688], [208, 702],
            [192, 716], [176, 730], [160, 744], [144, 752],
            [128, 766], [112, 780], [96, 793], [80, 807],
            [64, 821], [48, 821], [32, 835], [16, 865],
            [0, 865],
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
            [0, 1085], [1447, 1085], [1440, 740], [1424, 740],
            [1408, 729], [1392, 729], [1376, 718], [1360, 707],
            [1344, 685], [1328, 685], [1312, 674], [1296, 674],
            [1280, 704], [1264, 704], [1248, 690], [1232, 690],
            [1216, 676], [1200, 636], [1184, 622], [1168, 589],
            [1152, 578], [1136, 548], [1120, 548], [1104, 545],
            [1088, 537], [1072, 537], [1056, 535], [1040, 534],
            [1024, 475], [1008, 474], [992, 470], [976, 470],
            [960, 468], [944, 468], [928, 475], [912, 475],
            [896, 475], [880, 475], [864, 476], [848, 491],
            [832, 496], [816, 498], [800, 499], [784, 499],
            [768, 500], [752, 500], [736, 499], [720, 499],
            [704, 499], [688, 498], [672, 498], [656, 497],
            [640, 496], [624, 496], [608, 496], [592, 493],
            [576, 490], [560, 480], [544, 479], [528, 479],
            [512, 480], [496, 480], [480, 492], [464, 507],
            [448, 524], [432, 540], [416, 556], [400, 571],
            [384, 572], [368, 573], [352, 573], [336, 572],
            [320, 572], [304, 572], [288, 572], [272, 572],
            [256, 572], [240, 572], [224, 575], [208, 575],
            [192, 575], [176, 572], [160, 522], [144, 522],
            [128, 522], [112, 522], [96, 639], [80, 680],
            [64, 680], [48, 680], [32, 679], [16, 679],
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
            [0, 1085], [1447, 1085], [1440, 586], [1424, 586],
            [1408, 577], [1392, 568], [1376, 558], [1360, 549],
            [1344, 540], [1328, 531], [1312, 522], [1296, 513],
            [1280, 504], [1264, 495], [1248, 486], [1232, 476],
            [1216, 467], [1200, 459], [1184, 453], [1168, 448],
            [1152, 448], [1136, 447], [1120, 446], [1104, 446],
            [1088, 443], [1072, 427], [1056, 394], [1040, 379],
            [1024, 377], [1008, 369], [992, 354], [976, 345],
            [960, 339], [944, 339], [928, 339], [912, 339],
            [896, 338], [880, 336], [864, 330], [848, 330],
            [832, 330], [816, 330], [800, 362], [784, 367],
            [768, 368], [752, 368], [736, 368], [720, 388],
            [704, 405], [688, 405], [672, 407], [656, 408],
            [640, 408], [624, 408], [608, 407], [592, 407],
            [576, 403], [560, 403], [544, 408], [528, 435],
            [512, 435], [496, 438], [480, 449], [464, 451],
            [448, 452], [432, 453], [416, 453], [400, 454],
            [384, 474], [368, 478], [352, 493], [336, 497],
            [320, 499], [304, 502], [288, 502], [272, 502],
            [256, 504], [240, 506], [224, 517], [208, 541],
            [192, 545], [176, 547], [160, 547], [144, 548],
            [128, 549], [112, 587], [96, 590], [80, 801],
            [64, 815], [48, 828], [32, 844], [16, 859],
            [0, 859],
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
            [0, 1085], [1447, 1085], [1440, 745], [1424, 745],
            [1408, 714], [1392, 625], [1376, 625], [1360, 625],
            [1344, 611], [1328, 611], [1312, 543], [1296, 543],
            [1280, 543], [1264, 588], [1248, 625], [1232, 687],
            [1216, 687], [1200, 687], [1184, 626], [1168, 586],
            [1152, 586], [1136, 586], [1120, 600], [1104, 610],
            [1088, 610], [1072, 600], [1056, 590], [1040, 509],
            [1024, 508], [1008, 508], [992, 508], [976, 497],
            [960, 508], [944, 508], [928, 497], [912, 497],
            [896, 496], [880, 496], [864, 496], [848, 496],
            [832, 496], [816, 496], [800, 496], [784, 496],
            [768, 502], [752, 517], [736, 517], [720, 518],
            [704, 518], [688, 518], [672, 518], [656, 517],
            [640, 516], [624, 495], [608, 495], [592, 495],
            [576, 495], [560, 495], [544, 495], [528, 495],
            [512, 495], [496, 495], [480, 516], [464, 521],
            [448, 521], [432, 521], [416, 472], [400, 472],
            [384, 472], [368, 479], [352, 487], [336, 579],
            [320, 590], [304, 601], [288, 623], [272, 629],
            [256, 652], [240, 664], [224, 686], [208, 696],
            [192, 707], [176, 718], [160, 730], [144, 742],
            [128, 762], [112, 772], [96, 784], [80, 797],
            [64, 808], [48, 820], [32, 832], [16, 844],
            [0, 844],
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
