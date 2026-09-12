import re

import frappe
import frappe.website.serve

USER = "mainzaadam@gmail.com"


def _render(route):
    frappe.local._aab_nav = None
    frappe.local._aab_text = None
    frappe.local._aab_images = None
    return frappe.website.serve.get_response_content(route)


def _text(html, limit=700):
    t = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:limit]


def run():
    frappe.set_user(USER)

    print("=== /me, the account page ===")
    html = _render("me")
    print("  ", _text(html, 600))
    print()
    print("  links offered:")
    for href, label in re.findall(r'href="(/[^"]*)"[^>]*>\s*([^<]{2,40})', html):
        if href.startswith(("/app", "/assets")):
            continue
        print("     %-26s %s" % (href, label.strip()))

    print()
    print("=== /addresses, why is our theme missing ===")
    html = _render("addresses")
    print("  first 300 chars:", html[:300].replace("\n", " "))
    print("  length:", len(html))

    print()
    print("=== /orders, is the list drawn by javascript ===")
    html = _render("orders")
    print("  mentions list.js  :", "list.js" in html)
    print("  has a container   :", "web-list-container" in html or "result" in html)
    print("  text:", _text(html, 300))

    frappe.set_user("Guest")
