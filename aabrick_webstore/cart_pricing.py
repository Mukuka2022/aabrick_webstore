"""Stop an old cart from pricing itself at nothing.

A webshop cart is a draft Quotation, and it keeps the date it was started
on. ERPNext will not read an Item Price whose valid_from is later than the
date on the document, so a cart started before the web prices were loaded
finds no price at all and every line sits at zero.

That is not only untidy. Checkout is enabled, so a customer who left a cart
in June and comes back can put a Sales Order through at zero.

So a cart that is still open brings its date forward to today before it is
validated, and any line that has no price gets one. before_validate rather
than validate, because ERPNext works out the amounts and the totals during
validate: set the rate first and the rest follows on its own.

Only zero lines are touched. A rate somebody has deliberately changed is
left exactly as it is; a rate of zero in a shop never is.
"""

import frappe
from frappe.utils import flt, nowdate

CART = "Shopping Cart"


def _price(price_list, item_code, uom, on_date):
    """The rate for one line, read the way ERPNext reads it."""
    rows = frappe.db.sql(
        """
        SELECT price_list_rate
        FROM `tabItem Price`
        WHERE price_list = %(price_list)s
          AND item_code = %(item_code)s
          AND IFNULL(selling, 0) = 1
          AND IFNULL(uom, '') IN ('', %(uom)s)
          AND IFNULL(valid_from, '2000-01-01') <= %(on_date)s
          AND IFNULL(valid_upto, '2500-12-31') >= %(on_date)s
        ORDER BY IFNULL(uom, '') DESC, valid_from DESC
        LIMIT 1
        """,
        {
            "price_list": price_list,
            "item_code": item_code,
            "uom": uom or "",
            "on_date": on_date,
        },
    )
    return flt(rows[0][0]) if rows else 0.0


def before_validate(doc, method=None):
    """doc_events hook on Quotation."""
    if doc.docstatus != 0 or (doc.order_type or "") != CART:
        return

    today = nowdate()
    if str(doc.transaction_date or "") < today:
        doc.transaction_date = today
        # A payment term due before the posting date is an error ERPNext
        # refuses to save. The dates were written against the old posting
        # date, so anything now in the past moves up with it; the amounts
        # and the terms themselves are left alone.
        for row in (doc.get("payment_schedule") or []):
            if str(row.due_date or "") < today:
                row.due_date = today

    if not doc.selling_price_list:
        return

    for item in doc.items:
        if flt(item.price_list_rate):
            continue
        rate = _price(doc.selling_price_list, item.item_code, item.uom,
                      doc.transaction_date)
        if rate:
            item.price_list_rate = rate
            item.rate = rate
            item.discount_percentage = 0
            item.discount_amount = 0


def repair():
    """Fix the carts that are already sitting at zero.

    Saving is what applies the hook above. Safe to run twice: a cart that
    already prices itself is saved unchanged.
    """
    names = frappe.db.sql_list(
        """
        SELECT DISTINCT q.name
        FROM `tabQuotation` q
        JOIN `tabQuotation Item` i ON i.parent = q.name
        WHERE q.docstatus = 0
          AND q.order_type = %s
          AND IFNULL(i.rate, 0) = 0
        """,
        CART,
    )
    if not names:
        print("  no cart is sitting at zero")
        return

    fixed = stuck = 0
    for name in names:
        doc = frappe.get_doc("Quotation", name)
        before = flt(doc.net_total)
        try:
            doc.save(ignore_permissions=True)
        except Exception as e:
            print("  %s could not be saved: %s" % (name, e))
            stuck += 1
            continue
        doc.reload()
        if flt(doc.net_total) > before:
            print("  %-20s %s -> %s" % (name, before, doc.net_total))
            fixed += 1
        else:
            # Nothing to price it with: the item has no rate on that list.
            missing = [i.item_code for i in doc.items if not flt(i.rate)]
            print("  %-20s still zero, no price for %s" % (name, missing))
            stuck += 1

    frappe.db.commit()
    print()
    print("  repriced : %d" % fixed)
    print("  left     : %d" % stuck)
