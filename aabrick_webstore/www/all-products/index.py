"""The shop listing.

Replaces webshop's page, which ships an empty container and fills it from
JavaScript, so the source a crawler reads holds no products. This renders the
grid on the server, and its filters are ordinary links with query parameters
rather than script, so the page works with JavaScript off and every filtered
view has a URL that can be shared, bookmarked and indexed.

The facets are derived from the item groups, the same parse the product and
category pages use, so size, type and grade come from the catalogue rather than
from a list kept by hand.
"""

import frappe

from aabrick_webstore.overrides.item_group import _plural
from aabrick_webstore.overrides.website_item import (
    describe_group,
    image_shape,
    unit_label,
)

sitemap = 1
no_cache = 1

PER_PAGE = 48   # whole rows of four
LEAD_TIME_DAYS = 7


def get_context(context):
    groups = _groups()

    selected = frappe._dict({
        "size": (frappe.form_dict.get("size") or "").strip(),
        "type": (frappe.form_dict.get("type") or "").strip(),
        "grade": (frappe.form_dict.get("grade") or "").strip().upper(),
    })

    matching = [g for g in groups if _matches(g, selected)]
    names = [g.name for g in matching] or ["\0none"]

    page = max(frappe.utils.cint(frappe.form_dict.get("page")) or 1, 1)
    total = frappe.db.sql(
        """SELECT COUNT(*) FROM `tabWebsite Item`
           WHERE published = 1 AND item_group IN %s""",
        (names,),
    )[0][0]

    pages = max(-(-total // PER_PAGE), 1)
    page = min(page, pages)

    context.aab_products = _products(names, page)
    context.aab_total = total
    context.aab_page = page
    context.aab_pages = pages
    context.aab_selected = selected
    context.aab_facets = _facets(groups, selected)
    context.aab_active = any(selected.values())
    context.aab_lead_time = LEAD_TIME_DAYS
    context.aab_branch_count = frappe.db.count("Branch Location") or 46

    context.aab_heading = _heading(selected)
    context.title = "%s | AABrick Zambia" % context.aab_heading
    context.aab_canonical = frappe.utils.get_url("/all-products")
    context.aab_description = (
        "%s from AABrick Zambia. %d products, available at %s branches nationwide "
        "or delivered within %s days on anything not in stock."
        % (context.aab_heading, total, context.aab_branch_count, LEAD_TIME_DAYS)
    )
    context.aab_query = _query
    return context


# ----------------------------------------------------------------------
def _groups():
    rows = frappe.db.sql(
        """
        SELECT g.name, g.route
        FROM `tabItem Group` g
        WHERE g.is_group = 0 AND EXISTS (
            SELECT 1 FROM `tabWebsite Item` w
            WHERE w.item_group = g.name AND w.published = 1
        )
        """,
        as_dict=True,
    )
    for r in rows:
        label, size, finish, grade = describe_group(r.name)
        r["label"] = _plural(label)
        r["size"] = (size or "").replace(" x ", "x").replace(" mm", "")
        r["finish"] = finish
        r["grade"] = grade or "A"
    return rows


def _matches(group, selected):
    if selected.size and group.size != selected.size:
        return False
    if selected.type and (group.finish or "") != selected.type:
        return False
    if selected.grade and group.grade != selected.grade:
        return False
    return True


def _facets(groups, selected):
    """Every value that exists, with how many products sit behind it once the
    other filters are applied. A count of nothing is not offered."""
    def count_for(key, value):
        trial = frappe._dict(selected)
        trial[key] = value
        names = [g.name for g in groups if _matches(g, trial)]
        if not names:
            return 0
        return frappe.db.sql(
            """SELECT COUNT(*) FROM `tabWebsite Item`
               WHERE published = 1 AND item_group IN %s""",
            (names,),
        )[0][0]

    sizes = sorted({g.size for g in groups if g.size},
                   key=lambda s: [int(x) for x in s.split("x")])
    types = sorted({g.finish for g in groups if g.finish})

    return frappe._dict({
        "size": [frappe._dict(value=s, label=s.replace("x", " x ") + " mm",
                              count=count_for("size", s)) for s in sizes],
        "type": [frappe._dict(value=t, label=t, count=count_for("type", t))
                 for t in types],
        "grade": [frappe._dict(value=g, label="%s Grade" % g, count=count_for("grade", g))
                  for g in ("A", "B")],
    })


def _products(names, page):
    rows = frappe.db.sql(
        """
        SELECT wi.item_code, wi.route, wi.website_image, wi.item_group,
               ip.price_list_rate
        FROM `tabWebsite Item` wi
        LEFT JOIN `tabItem Price` ip
          ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
        WHERE wi.published = 1 AND wi.item_group IN %s
        ORDER BY wi.item_code
        LIMIT %s OFFSET %s
        """,
        (names, PER_PAGE, (page - 1) * PER_PAGE),
        as_dict=True,
    )
    for r in rows:
        label, _size, _finish, grade = describe_group(r.item_group)
        r["label"] = label
        r["grade"] = grade
        r["shape"] = image_shape(r.website_image)
        r["price"] = (
            frappe.utils.fmt_money(r.price_list_rate, currency="ZMW")
            if r.price_list_rate else None
        )
        r["uom"] = unit_label(r.item_code)
    return rows


def _heading(selected):
    if not any(selected.values()):
        return "All Products"
    bits = []
    if selected.type:
        bits.append(selected.type)
    bits.append("Tiles" if (selected.size or selected.type) else "Products")
    if selected.size:
        bits.append(selected.size)
    if selected.grade == "B":
        bits.append("(B Grade)")
    return " ".join(bits)


def _query(selected, key=None, value=None, page=None):
    """Build a filter URL, dropping anything empty so the plain listing stays
    at /all-products with no query string at all."""
    parts = dict(size=selected.size, type=selected.type, grade=selected.grade)
    if key is not None:
        parts[key] = "" if parts.get(key) == value else value
    if page and page > 1:
        parts["page"] = page
    query = "&".join(
        "%s=%s" % (k, frappe.utils.quoted(v)) for k, v in parts.items() if v
    )
    return "/all-products?%s" % query if query else "/all-products"
