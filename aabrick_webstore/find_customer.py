"""Find a real website customer to walk the portal as."""

import frappe


def run():
    print("=== website users ===")
    users = frappe.get_all(
        "User",
        filters={"user_type": "Website User", "enabled": 1},
        fields=["name", "full_name"], limit_page_length=10,
    )
    for u in users:
        print("  %-34s %s" % (u.name, u.full_name))
    print("  total:", frappe.db.count("User", {"user_type": "Website User", "enabled": 1}))

    print()
    print("=== contacts linked to customers (that is what the portal uses) ===")
    rows = frappe.db.sql(
        """
        SELECT c.user, dl.link_name AS customer
        FROM `tabContact` c
        JOIN `tabDynamic Link` dl ON dl.parent = c.name
        WHERE dl.link_doctype = 'Customer' AND IFNULL(c.user, '') <> ''
        LIMIT 10
        """,
        as_dict=True,
    )
    for r in rows:
        print("  %-34s -> %s" % (r.user, r.customer))

    print()
    print("=== sales orders from the website ===")
    so = frappe.get_all(
        "Sales Order", fields=["name", "customer", "status", "grand_total", "owner"],
        order_by="creation desc", limit_page_length=6,
    )
    for s in so:
        print("  %-20s %-24s %-12s %s  (%s)"
              % (s.name, s.customer, s.status, s.grand_total, s.owner))
    print("  total sales orders:", frappe.db.count("Sales Order"))
