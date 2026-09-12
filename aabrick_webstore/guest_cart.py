"""What a cart held on the customer's phone needs from the server.

A webshop cart is a Quotation attached to a Customer, built from the signed
in user, which is why adding to it used to demand a login. Until somebody
commits to an order there is no reason to know who they are, so a guest
cart lives in their browser and only this is asked of the server: what are
these items called, what do they cost, and what do they look like.

Prices are never taken from the browser. The basket is a list of item codes
and quantities; every figure on the page is worked out here.
"""

import json

import frappe
from frappe.utils import cint, flt

from aabrick_webstore.cart_pricing import _price
from aabrick_webstore.overrides.website_item import describe_group

MAX_LINES = 40


def _price_list():
    return frappe.db.get_single_value("Webshop Settings", "price_list") \
        or "Standard Selling"


@frappe.whitelist(allow_guest=True)
def summary(items=None):
    """Describe a basket of item codes and quantities.

    items: JSON, {"86000": 2, "96201": 1}
    """
    try:
        basket = json.loads(items or "{}")
    except ValueError:
        frappe.throw("That basket could not be read.")
    if not isinstance(basket, dict):
        frappe.throw("That basket could not be read.")

    codes = [str(c) for c in list(basket.keys())[:MAX_LINES]]
    if not codes:
        return {"items": [], "total": 0, "total_display": "", "count": 0}

    rows = frappe.get_all(
        "Website Item",
        filters={"item_code": ["in", codes], "published": 1},
        fields=["item_code", "item_group", "route",
                "website_image", "stock_uom"],
    )
    found = {r.item_code: r for r in rows}

    price_list = _price_list()
    today = frappe.utils.nowdate()

    out, total = [], 0.0
    for code in codes:
        r = found.get(code)
        if not r:
            # Unpublished since it went in the basket. Dropped rather than
            # shown, so nobody can order something that is no longer sold.
            continue
        qty = cint(basket.get(code)) or 0
        if qty < 1:
            continue
        qty = min(qty, 999)

        label, _size, _finish, grade = describe_group(r.item_group)
        name = ("%s %s" % (code, label)).strip()
        if grade:
            name = "%s (%s grade)" % (name, grade)

        rate = _price(price_list, code, r.stock_uom, today)
        amount = flt(rate) * qty
        total += amount

        out.append({
            "item_code": code,
            "name": name,
            "route": "/" + (r.route or ""),
            "image": r.website_image or "",
            "uom": (r.stock_uom or "").lower(),
            "qty": qty,
            "rate": flt(rate),
            "rate_display": frappe.utils.fmt_money(rate, currency="ZMW") if rate else "",
            "amount": amount,
            "amount_display": frappe.utils.fmt_money(amount, currency="ZMW") if rate else "",
        })

    return {
        "items": out,
        "count": sum(i["qty"] for i in out),
        "total": total,
        "total_display": frappe.utils.fmt_money(total, currency="ZMW"),
        "priced": all(i["rate"] for i in out),
    }


def quiet_guest_cart(context):
    """update_website_context hook: swallow the permission complaint that
    webshop's cart page raises for a visitor who has not signed in."""
    if frappe.session.user != "Guest":
        return context

    request = getattr(frappe.local, "request", None)
    path = (getattr(request, "path", "") or "").strip("/")
    if path != "cart":
        return context

    # The basket on this page is the browser's, so there is nothing here the
    # visitor was denied and nothing to tell them about.
    frappe.local.message_log = []
    if hasattr(frappe, "clear_last_message"):
        frappe.clear_last_message()
    return context
