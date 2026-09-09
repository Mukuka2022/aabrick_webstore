"""Load tile buying/selling prices from the AABrick price-band sheet.

Run:
    bench --site www.aabrick.com execute aabrick_webstore.price_loader.run
    bench --site www.aabrick.com execute aabrick_webstore.price_loader.run --kwargs "{'apply': True}"
"""

import frappe

SELLING = "Standard Selling"
BUYING = "Standard Buying"

# item_group -> (shop_selling_price, order_price_from_factory)
GROUP_PRICES = {
    # ---- A Grade (AAA) ----
    "Wall Tiles(250X400) - 254XX":                    (285.0, 232.05),
    "Wall Tiles (300X600) - 36XXX":                   (313.0, 257.53),
    "Wall Tiles (300X300) - 33XXX":                   (285.0, 232.05),
    "Matte Porcelain Tiles (600x600) - 56/96XXX":     (313.0, 257.53),
    "Matte Textured Tiles (600X600) - 962XX/96118":   (318.0, 262.08),
    "Glazed Porcelain Tiles (600X600) - 86XXX":       (318.0, 262.08),
    "Polished Porcelain Tiles (600X600) - 6/7XXX":    (338.0, 280.28),
    "Matt Porcelain Tiles (800X800) - 89XXX":         (485.0, 414.05),
    "Glazed Porcelain Tiles (800X800) - 88XXX":       (485.0, 414.05),
    "Matt Porcelain Tiles (600X1200) - 1268/9XX":     (356.0, 296.66),
    "Glazed Porcelain Tiles (600X1200) - 1268/9XX":   (356.0, 296.66),
    # ---- B Grade (AA&A, D) ----
    "Wall Tiles D (250X400) - 254XX":                 (270.0, 208.80),
    "Wall Tiles D (300X600) - 36XXX":                 (298.0, 233.16),
    "Wall Tiles D (300X300) - 33XXX":                 (270.0, 208.80),
    "Matte Porcelain Tiles D (600x600) - 56/96XXX":   (298.0, 233.16),
    "Matte Textured Tiles D (600X600) - 962XX/96118": (303.0, 237.51),
    "Glazed Porcelain Tiles D (600X600) - 86XXX":     (303.0, 237.51),
    "Polished Porcelain Tiles D (600X600) - 6/7XXX":  (323.0, 243.19),
    "Matt Porcelain Tiles D (800X800) - 89XXX":       (470.0, 382.80),
    "Glazed Porcelain Tiles D (800X800) - 88XXX":     (470.0, 382.80),
    "Matt Porcelain Tiles D (600X1200) - 1268/9XX":   (341.0, 283.62),
    "Glazed Porcelain Tiles D (600X1200) - 1268/9XX": (341.0, 283.62),
}

# specific item_code -> (selling, buying); applied AFTER the group rules
CODE_OVERRIDES = {
    "254331": (420.0, 353.99),
    "86000": (366.0, 305.76), "86001": (366.0, 305.76),
    "86002": (366.0, 305.76), "86003": (366.0, 305.76),
    "86032": (366.0, 305.76), "56111": (366.0, 305.76),
    "126801": (385.0, 323.05),
    "254331D": (404.0, 321.03),
    "86000D": (351.0, 279.27), "86001D": (351.0, 279.27),
    "86002D": (351.0, 279.27), "86003D": (351.0, 279.27),
    "86032D": (351.0, 279.27), "56111D": (351.0, 279.27),
    "126801D": (370.0, 308.85),
}


def run(apply=False):
    stats = {"created": 0, "updated": 0, "unchanged": 0, "dupes": 0, "failed": 0}
    failures = []
    changes = []

    def upsert(item_code, price_list, rate):
        existing = frappe.get_all(
            "Item Price",
            filters={"item_code": item_code, "price_list": price_list},
            fields=["name", "price_list_rate"],
            order_by="creation asc",
        )
        if len(existing) > 1:
            stats["dupes"] += len(existing) - 1
            if apply:
                for extra in existing[1:]:
                    frappe.delete_doc("Item Price", extra["name"],
                                      force=1, ignore_permissions=True)
        if existing:
            cur = float(existing[0]["price_list_rate"] or 0)
            if abs(cur - rate) < 0.005:
                stats["unchanged"] += 1
                return
            stats["updated"] += 1
            changes.append((item_code, price_list, cur, rate))
            if apply:
                frappe.db.set_value("Item Price", existing[0]["name"],
                                    "price_list_rate", rate, update_modified=True)
        else:
            stats["created"] += 1
            changes.append((item_code, price_list, None, rate))
            if apply:
                try:
                    frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": item_code,
                        "price_list": price_list,
                        "price_list_rate": rate,
                        "currency": "ZMW",
                    }).insert(ignore_permissions=True)
                except Exception as e:
                    stats["failed"] += 1
                    failures.append((item_code, price_list, str(e)[:90]))

    targets = {}
    for group, (sell, buy) in GROUP_PRICES.items():
        for code in frappe.get_all("Item", filters={"item_group": group}, pluck="name"):
            targets[code] = (sell, buy)

    missing = []
    for code, prices in CODE_OVERRIDES.items():
        if frappe.db.exists("Item", code):
            targets[code] = prices
        else:
            missing.append(code)

    for code, (sell, buy) in sorted(targets.items()):
        upsert(code, SELLING, sell)
        upsert(code, BUYING, buy)

    print("=" * 60)
    print("MODE: %s" % ("APPLIED" if apply else "DRY RUN (nothing written)"))
    print("=" * 60)
    print("items matched                 : %d" % len(targets))
    print("price records created         : %d" % stats["created"])
    print("price records updated         : %d" % stats["updated"])
    print("already correct (skipped)     : %d" % stats["unchanged"])
    print("duplicate price rows          : %d" % stats["dupes"])
    print("insert failures               : %d" % stats["failed"])
    print("override codes not in system  : %s" % (", ".join(missing) or "none"))
    print()
    print("--- first 12 changes ---")
    for code, pl, old, new in changes[:12]:
        print("  %-10s %-17s %9s -> %8.2f"
              % (code, pl, "(new)" if old is None else "%.2f" % old, new))
    print("  ... %d more" % max(0, len(changes) - 12))

    if failures:
        print()
        print("--- insert failures (first 10) ---")
        for code, pl, err in failures[:10]:
            print("  %-10s %-17s %s" % (code, pl, err))

    if apply:
        frappe.db.commit()
        print("\nCOMMITTED")
    return stats


def run_apply():
    """Entry point that writes. Kept separate so `bench execute` needs no --kwargs."""
    return run(apply=True)


def check_uoms():
    """Report Item Price rows whose UOM is not valid for their item.

    These block a normal doc.save() on the price row, which is why the loader
    writes rates directly instead.
    """
    bad = frappe.db.sql("""
        SELECT ip.name, ip.item_code, ip.price_list, ip.uom, i.stock_uom
        FROM `tabItem Price` ip
        JOIN `tabItem` i ON i.name = ip.item_code
        WHERE IFNULL(ip.uom, '') <> ''
          AND ip.uom <> i.stock_uom
          AND NOT EXISTS (
              SELECT 1 FROM `tabUOM Conversion Detail` ucd
              WHERE ucd.parent = i.name AND ucd.uom = ip.uom
          )
    """, as_dict=True)
    print("Item Price rows with an invalid UOM: %d" % len(bad))
    for r in bad[:20]:
        print("  %-10s  price_list=%-17s  uom=%-8s  stock_uom=%s"
              % (r.item_code, r.price_list, r.uom, r.stock_uom))
    if len(bad) > 20:
        print("  ... %d more" % (len(bad) - 20))
    return len(bad)
