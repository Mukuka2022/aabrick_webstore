"""Homepage context.

Built as a file rather than a Web Page record so it is versioned and deploys
with the app. Products are pulled live, so the page never shows a price that
disagrees with the shop.
"""

import os

import frappe

from aabrick_webstore import showcase

no_cache = 1
sitemap = 1

COMPANY_PHONE = "+260 960 787 777"

IMG = "/assets/aabrick_webstore/images/"

# The hero photograph is optional. Without it the hero keeps its charcoal
# gradient, which is a deliberate look rather than a hole in the page.
HERO_FILE = os.path.join(
    os.path.dirname(__file__), "..", "public", "images", "hero.jpg"
)

# The four lines being sold online for now. The rest of the catalogue stays in
# ERPNext for branch trading until we are ready to sell it online.
#
# "fit" says how the card should treat the image. Photographs fill the card;
# cut-out pack shots are letterboxed so nothing is sliced off their edges.
CATEGORIES = [
    {
        "key": "tiles",
        "title": "Tiles",
        "blurb": "Wall, floor, porcelain and polished",
        "match": "Tiles",
        "image": IMG + "cat-tiles.jpg",
        "fit": "cover",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Tiles%22%5D%7D",
    },
    {
        "key": "tile_fix",
        "title": "Tile Fix",
        "blurb": "Adhesive and grout",
        "match": "Tile Fix",
        "image": IMG + "cat-tile-fix.png",
        "fit": "contain",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Tile%20Fix%22%5D%7D",
    },
    {
        "key": "pvc",
        "title": "PVC Ceiling Boards",
        "blurb": "Boards, skirting and accessories",
        "match": "PVC",
        "image": IMG + "cat-pvc.png",
        "fit": "contain",
        "route": "/all-products",
    },
    {
        "key": "fertilizer",
        "title": "Fertilizer",
        "blurb": "For farm and garden",
        "match": "Fertilizer",
        "image": IMG + "cat-fertilizer.jpg",
        "fit": "cover",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Fertilizer%22%5D%7D",
    },
]


def get_context(context):
    context.title = "AABrick Zambia"
    context.company_phone = COMPANY_PHONE
    context.whatsapp_number = ""  # set once the WhatsApp line is confirmed

    context.branch_count = frappe.db.count("Branch Location") or 46
    context.published_branches = frappe.db.count("Branch Location", {"published": 1})

    context.has_hero = os.path.exists(HERO_FILE)
    context.showcase = showcase.context()
    context.categories = _categories()
    context.featured = _featured()
    context.description = (
        "Tiles, tile fix, PVC ceiling boards and fertilizer from AABrick Zambia. "
        "%s branches nationwide, delivery within 7 days on anything not in stock."
        % context.branch_count
    )
    return context


def _categories():
    """A card shows whatever was last uploaded for it in Website Images, so
    the four cards can be changed on the live server without a deploy.

    Failing that it shows the artwork in the app, which is why that artwork
    is still here: a fresh install looks like this one before anybody has
    uploaded anything. A product photograph from the group is the last
    resort, for a category with no artwork at all.
    """
    from aabrick_webstore.jinja_helpers import site_images

    uploaded = site_images().cats
    out = []
    for c in CATEGORIES:
        card = uploaded.get(c["key"]) or {}
        image, fit = card.get("src"), card.get("fit")
        if not image:
            image = c.get("image") or frappe.db.get_value(
                "Website Item",
                {"published": 1, "item_group": ["like", "%%%s%%" % c["match"]],
                 "website_image": ["not in", ["", None]]},
                "website_image",
            )
            fit = c["fit"]
        count = frappe.db.count(
            "Website Item",
            {"published": 1, "item_group": ["like", "%%%s%%" % c["match"]]},
        )
        out.append(dict(c, image=image, fit=fit, count=count))
    return out


def _image_path(url):
    """A website image URL as a path on disk, or None."""
    rel = (url or "").lstrip("/")
    if not rel:
        return None
    if rel.startswith("files/"):
        return frappe.get_site_path("public", rel)
    if rel.startswith("private/files/"):
        return frappe.get_site_path(rel)
    return None


def _shape(url):
    """wide, tall or square.

    The card gives each shape a different amount of room, because one box
    cannot shrink the square tiles without shrinking the upright bags with
    them: both are limited by the height. Reading the header is cheap, and
    Pillow does not decode the pixels to answer this.
    """
    path = _image_path(url)
    if not path or not os.path.exists(path):
        return "square"
    try:
        from PIL import Image

        with Image.open(path) as im:
            ratio = im.width / float(im.height or 1)
    except Exception:
        return "square"
    if ratio >= 1.4:
        return "wide"
    if ratio <= 0.8:
        return "tall"
    return "square"


# How many products the home page row holds. The column count is in the
# stylesheet, under .aab-home .aab-tiles, and the two have to agree or the row
# comes up a card short. Four, matching the four category cards above it.
FEATURED_COUNT = 4

# Set by featured.run. Read through a column check rather than assumed, so a
# site that has pulled the code but not yet run the script falls back to
# choosing for itself instead of erroring on a column that is not there.
ON_HOME = "custom_on_home"


def _picked():
    """The products somebody at AABrick ticked, in the order they should show.

    Ordered by Ranking so the choice can be arranged, then by price. Grouped by
    item code because a product can carry more than one Item Price on the same
    price list, and without it one product would take two places in the row.

    A left join on the price: a ticked product with no web price still belongs
    on the page, and the card already knows how to say Price on request. The
    photograph is required though — a card with an empty grey square in it
    reads as a fault, not as a choice.
    """
    if not frappe.db.has_column("Website Item", ON_HOME):
        return []
    return frappe.db.sql(
        """
        SELECT wi.item_code, wi.web_item_name, wi.website_image, wi.route,
               wi.item_group, wi.ranking, MIN(ip.price_list_rate) AS price_list_rate
        FROM `tabWebsite Item` wi
        LEFT JOIN `tabItem Price` ip
          ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
        WHERE wi.published = 1
          AND wi.`{on_home}` = 1
          AND IFNULL(wi.website_image, '') <> ''
        GROUP BY wi.item_code
        ORDER BY wi.ranking DESC, price_list_rate DESC
        LIMIT {count}
        """.format(on_home=ON_HOME, count=FEATURED_COUNT),
        as_dict=True,
    )


def _auto():
    """What the row shows when nobody has chosen: published items with an image
    and a price, one per item group, so it reads as the spread of the catalogue
    rather than four near-identical tiles."""
    return frappe.db.sql(
        """
        SELECT wi.item_code, wi.web_item_name, wi.website_image, wi.route,
               wi.item_group, ip.price_list_rate
        FROM `tabWebsite Item` wi
        JOIN `tabItem Price` ip
          ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
        WHERE wi.published = 1
          AND IFNULL(wi.website_image, '') <> ''
          AND wi.item_group NOT LIKE '%% D (%%'
        GROUP BY wi.item_group
        ORDER BY ip.price_list_rate DESC
        LIMIT %s
        """,
        FEATURED_COUNT,
        as_dict=True,
    )


def _featured():
    """The products on the home page: whatever was ticked, or failing that
    whatever the catalogue suggests."""
    rows = _picked() or _auto()

    from aabrick_webstore.overrides.website_item import describe_group, unit_label

    for r in rows:
        # A ticked product may have no web price, where the automatic pick
        # could not: fmt_money would print ZK 0.00 and the card would offer to
        # sell it for nothing.
        r["price"] = (frappe.utils.fmt_money(r.price_list_rate, currency="ZMW")
                      if r.price_list_rate else "")
        r["group_label"] = (r.item_group or "").split(" - ")[0]
        r["shape"] = _shape(r.website_image)
        # The homepage shows the same card as the shop, so it needs the same
        # fields: what to call it, which grade it is, and what the price buys.
        label, _size, _finish, grade = describe_group(r.item_group)
        r["label"] = label
        r["grade"] = grade
        r["uom"] = unit_label(r.item_code)
    return rows
