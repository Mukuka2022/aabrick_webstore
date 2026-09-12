"""Walk the signed-in part of the site as a real customer.

A browser cannot be signed in from here, so each page is rendered as the
customer server side. What that shows is the markup: the route answers, it
carries our header and footer, and the customer's own things are on it.
"""

import frappe
import frappe.website.serve

USER = "mainzaadam@gmail.com"


def _render(route):
    frappe.local._aab_nav = None
    frappe.local._aab_text = None
    frappe.local._aab_images = None
    try:
        return frappe.website.serve.get_response_content(route)
    except Exception as e:
        return "!!ERROR!! %s: %s" % (type(e).__name__, e)


def run():
    print("=== what the portal menu offers a customer ===")
    items = frappe.get_hooks("standard_portal_menu_items") or []
    for it in items:
        print("  %-22s %-26s role=%s"
              % (it.get("title"), it.get("route"), it.get("role") or "-"))

    print()
    print("=== the customer ===")
    so = frappe.get_all("Sales Order", filters={"owner": USER},
                        fields=["name", "status", "grand_total"])
    print("  orders:", [(s.name, s.status) for s in so])

    frappe.set_user(USER)
    print("  signed in as a %s"
          % frappe.db.get_value("User", USER, "user_type"))

    routes = [
        ("me", "Account"),
        ("orders", "Orders"),
        ("order/" + so[0].name, "One order") if so else None,
        ("quotations", "Quotations"),
        ("invoices", "Invoices"),
        ("addresses", "Addresses"),
        ("cart", "Cart"),
        ("shipments", "Shipments"),
        ("", "Home"),
        ("all-products", "Shop"),
    ]
    routes = [r for r in routes if r]

    print()
    print("=== every page a signed-in customer can reach ===")
    print("  %-16s %-8s %-6s %-6s %-6s %s"
          % ("route", "renders", "nav", "foot", "css", "note"))
    for route, label in routes:
        html = _render(route or "index")
        if html.startswith("!!ERROR!!"):
            print("  %-16s %s" % ("/" + route, html[:90]))
            continue
        print("  %-16s %-8s %-6s %-6s %-6s %s"
              % ("/" + route,
                 "yes",
                 "y" if "aab-nav-main" in html else "NO",
                 "y" if "aab-foot-main" in html else "NO",
                 "y" if "webstore.css" in html else "NO",
                 ""))

    print()
    print("=== does the orders page actually list their orders ===")
    html = _render("orders")
    for s in so:
        print("  %-22s on the page: %s" % (s.name, s.name in html))

    print()
    print("=== does one order show what they bought ===")
    if so:
        html = _render("order/" + so[0].name)
        print("  order number      :", so[0].name in html)
        print("  a money figure    :", "7,590" in html or "43,884" in html
              or str(int(so[0].grand_total)) in html)
        print("  an item code      :", any(
            c in html for c in frappe.get_all(
                "Sales Order Item", filters={"parent": so[0].name},
                pluck="item_code")))

    frappe.set_user("Guest")
