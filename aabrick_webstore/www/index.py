"""Homepage context.

Built as a file rather than a Web Page record so it is versioned and deploys
with the app. Products are pulled live, so the page never shows a price that
disagrees with the shop.
"""

import frappe

no_cache = 1

COMPANY_PHONE = "+260 960 787 777"

# The four lines being sold online for now. The rest of the catalogue stays in
# ERPNext for branch trading until we are ready to sell it online.
CATEGORIES = [
    {
        "title": "Tiles",
        "blurb": "Wall, floor, porcelain and polished",
        "match": "Tiles",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Tiles%22%5D%7D",
    },
    {
        "title": "Tile Fix",
        "blurb": "Adhesive and grout",
        "match": "Tile Fix",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Tile%20Fix%22%5D%7D",
    },
    {
        "title": "PVC Ceiling Boards",
        "blurb": "Boards, skirting and accessories",
        "match": "PVC",
        "route": "/all-products",
    },
    {
        "title": "Fertilizer",
        "blurb": "For farm and garden",
        "match": "Fertilizer",
        "route": "/all-products?field_filters=%7B%22custom_category%22%3A%5B%22Fertilizer%22%5D%7D",
    },
]


def get_context(context):
    context.title = "AABrick Zambia"
    context.company_phone = COMPANY_PHONE
    context.whatsapp_number = ""  # set once the WhatsApp line is confirmed

    context.branch_count = frappe.db.count("Branch Location") or 46
    context.published_branches = frappe.db.count("Branch Location", {"published": 1})

    context.categories = _categories()
    context.featured = _featured()
    context.description = (
        "Tiles, tile fix, PVC ceiling boards and fertilizer from AABrick Zambia. "
        "%s branches nationwide, delivery within 7 days on anything not in stock."
        % context.branch_count
    )
    return context


def _categories():
    out = []
    for c in CATEGORIES:
        image = frappe.db.get_value(
            "Website Item",
            {"published": 1, "item_group": ["like", "%%%s%%" % c["match"]],
             "website_image": ["not in", ["", None]]},
            "website_image",
        )
        count = frappe.db.count(
            "Website Item",
            {"published": 1, "item_group": ["like", "%%%s%%" % c["match"]]},
        )
        out.append(dict(c, image=image, count=count))
    return out


def _featured():
    """Published items with an image and a price, one per item group so the row
    shows range rather than six near-identical tiles."""
    rows = frappe.db.sql(
        """
        SELECT wi.item_code, wi.web_item_name, wi.website_image, wi.route,
               wi.item_group, ip.price_list_rate
        FROM `tabWebsite Item` wi
        JOIN `tabItem Price` ip
          ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
        WHERE wi.published = 1
          AND IFNULL(wi.website_image, '') <> ''
        GROUP BY wi.item_group
        ORDER BY ip.price_list_rate DESC
        LIMIT 6
        """,
        as_dict=True,
    )
    for r in rows:
        r["price"] = frappe.utils.fmt_money(r.price_list_rate, currency="ZMW")
        r["group_label"] = (r.item_group or "").split(" - ")[0]
    return rows
