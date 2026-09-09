"""Build the Web Price List as Standard Selling + a flat markup.

Website prices = POS/counter price + WEB_MARKUP (ZMW).

    bench --site www.aabrick.com execute aabrick_webstore.web_prices.preview
    bench --site www.aabrick.com execute aabrick_webstore.web_prices.apply_prices
    bench --site www.aabrick.com execute aabrick_webstore.web_prices.point_webshop_at_web_list
"""

import frappe

SOURCE_LIST = "Standard Selling"
WEB_LIST = "Web Price List"
WEB_MARKUP = 10.0
LOW_VALUE_THRESHOLD = 50.0


def _build(apply=False):
    source = frappe.get_all(
        "Item Price",
        filters={"price_list": SOURCE_LIST},
        fields=["item_code", "price_list_rate"],
    )
    existing = {
        r["item_code"]: r
        for r in frappe.get_all(
            "Item Price",
            filters={"price_list": WEB_LIST},
            fields=["name", "item_code", "price_list_rate"],
        )
    }

    created = updated = unchanged = skipped = failed = 0
    low_value = []
    failures = []

    for row in source:
        code = row["item_code"]
        base = float(row["price_list_rate"] or 0)
        if base <= 0:
            skipped += 1
            continue

        web_rate = base + WEB_MARKUP
        if base < LOW_VALUE_THRESHOLD:
            low_value.append((code, base, web_rate, WEB_MARKUP / base * 100))

        prior = existing.get(code)
        if prior:
            if abs(float(prior["price_list_rate"] or 0) - web_rate) < 0.005:
                unchanged += 1
                continue
            updated += 1
            if apply:
                frappe.db.set_value("Item Price", prior["name"],
                                    "price_list_rate", web_rate,
                                    update_modified=True)
        else:
            created += 1
            if apply:
                try:
                    frappe.get_doc({
                        "doctype": "Item Price",
                        "item_code": code,
                        "price_list": WEB_LIST,
                        "price_list_rate": web_rate,
                        "currency": "ZMW",
                    }).insert(ignore_permissions=True)
                except Exception as e:
                    failed += 1
                    created -= 1
                    failures.append((code, str(e)[:80]))

    print("=" * 62)
    print("MODE: %s   markup = +%.2f ZMW" % ("APPLIED" if apply else "PREVIEW", WEB_MARKUP))
    print("=" * 62)
    print("source prices (%s) : %d" % (SOURCE_LIST, len(source)))
    print("web prices created           : %d" % created)
    print("web prices updated           : %d" % updated)
    print("already correct              : %d" % unchanged)
    print("skipped (zero/no price)      : %d" % skipped)
    print("failed                       : %d" % failed)
    print()
    print("--- items under %.0f ZMW where +%.0f is a large %% ---"
          % (LOW_VALUE_THRESHOLD, WEB_MARKUP))
    for code, base, web, pct in sorted(low_value, key=lambda x: -x[3])[:12]:
        print("  %-14s %7.2f -> %7.2f   (+%.0f%%)" % (code, base, web, pct))
    print("  (%d items under %.0f ZMW in total)" % (len(low_value), LOW_VALUE_THRESHOLD))
    for code, err in failures[:8]:
        print("  FAIL %-14s %s" % (code, err))

    if apply:
        frappe.db.commit()
        print("\nCOMMITTED")
    return {"created": created, "updated": updated, "unchanged": unchanged,
            "skipped": skipped, "failed": failed, "low_value": len(low_value)}


def preview():
    return _build(apply=False)


def apply_prices():
    return _build(apply=True)


def point_webshop_at_web_list():
    """Switch the storefront from Standard Selling to the Web Price List."""
    before = frappe.db.get_single_value("Webshop Settings", "price_list")
    frappe.db.set_single_value("Webshop Settings", "price_list", WEB_LIST)
    frappe.db.commit()
    frappe.clear_cache()
    after = frappe.db.get_single_value("Webshop Settings", "price_list")
    print("Webshop Settings.price_list: %s -> %s" % (before, after))
    return after
