"""The enquiry page.

Replaces Frappe's default /contact, which carried no form at all while every
"ask about this tile", "send an enquiry" and "ask for a quotation" button on
the site pointed at it.

The page takes context from the query string, so an enquiry that starts on a
product page or in the calculator arrives with the tile and the quantity
already attached rather than as "I need tiles".
"""

import frappe

no_cache = 1
sitemap = 1

COMPANY_PHONE = "+260 960 787 777"


def get_context(context):
    context.title = "Contact AABrick Zambia"
    context.aab_description = (
        "Ask AABrick Zambia about tiles, tile fix, PVC ceiling boards and "
        "fertilizer. Send an enquiry, call the sales line, or find your nearest "
        "branch."
    )
    context.aab_canonical = frappe.utils.get_url("/contact")
    context.aab_phone = COMPANY_PHONE
    context.aab_phone_link = COMPANY_PHONE.replace(" ", "")
    context.aab_branch_count = frappe.db.count("Branch Location") or 46

    context.aab_branches = frappe.get_all(
        "Branch Location",
        fields=["branch_name", "province"],
        order_by="province asc, branch_name asc",
        limit_page_length=0,
    )

    # Whatever the customer was looking at when they clicked.
    item = (frappe.form_dict.get("item") or "").strip()[:60]
    context.aab_item = None
    if item:
        row = frappe.db.get_value(
            "Website Item", {"item_code": item, "published": 1},
            ["item_code", "route", "item_group"], as_dict=True,
        )
        if row:
            from aabrick_webstore.overrides.website_item import describe_group
            label, _size, _finish, grade = describe_group(row.item_group)
            context.aab_item = frappe._dict({
                "code": row.item_code,
                "route": "/" + (row.route or ""),
                "label": label + (" (B Grade)" if grade else ""),
            })

    context.aab_qty = (frappe.form_dict.get("qty") or "").strip()[:40]
    context.aab_area = (frappe.form_dict.get("area") or "").strip()[:40]

    from aabrick_webstore import hooks
    context.aab_version = hooks.ASSET_VERSION
    return context
