"""AABrick's sitemap.

Frappe's own sitemap only lists a doctype when its DocType record has
allow_guest_to_view set. Website Item does not, and neither does Branch
Location, so 436 published products and every branch page were absent while
the categories, which do have it, were listed. Flipping that flag would work
but it is a schema property stored in the database, which does not travel with
a deploy and would have to be set again on every site.

Listing the routes here instead keeps the fix in code, and makes the contents
deliberate: the shop, the ranges, the products, the branches and the pages
worth indexing, and none of the cart, account or checkout routes that Frappe
would otherwise offer a crawler.
"""

from urllib.parse import quote

import frappe
from frappe.utils import get_url, nowdate
from frappe.website.router import get_pages

no_cache = 1
base_template_path = "www/sitemap.xml"

# Routes a crawler has no business indexing, even though they render.
EXCLUDE_EXACT = {
    "cart", "checkout", "login", "signup", "wishlist", "orders", "addresses",
    "me", "update-password", "third-party-apps", "book-appointment", "search",
    "product_search", "shop-by-category", "customer-care/new", "rfq",
}
EXCLUDE_PREFIX = ("me/", "orders/", "invoices/", "quotations/", "shipments/",
                  "book-appointment/", "customer-care/")


def _keep(route):
    route = (route or "").strip("/")
    if not route:
        return False
    if route in EXCLUDE_EXACT:
        return False
    return not route.startswith(EXCLUDE_PREFIX)


def _add(links, seen, route, modified=None):
    route = (route or "").strip("/")
    if not _keep(route) or route in seen:
        return
    seen.add(route)
    links.append({
        "loc": get_url(quote(route.encode("utf-8"))),
        "lastmod": modified.strftime("%Y-%m-%d") if modified else nowdate(),
    })


def get_context(context):
    links = []
    seen = set()

    # The homepage first: it is the only route that is not a path.
    links.append({"loc": get_url("/"), "lastmod": nowdate()})

    # Static pages that opted in, the same set Frappe would list.
    for route, page in get_pages().items():
        if getattr(page, "sitemap", None):
            _add(links, seen, route)

    for doctype, condition in (
        ("Website Item", {"published": 1}),
        ("Item Group", {"show_in_website": 1, "is_group": 0}),
        ("Branch Location", {"published": 1}),
        ("Web Page", {"published": 1}),
        ("Job Opening", {"publish": 1}),
    ):
        if not frappe.db.exists("DocType", doctype):
            continue
        try:
            rows = frappe.get_all(
                doctype, filters=condition, fields=["route", "modified"],
                limit_page_length=0,
            )
        except Exception:
            continue
        for row in rows:
            _add(links, seen, row.route, row.modified)

    return {"links": links}
