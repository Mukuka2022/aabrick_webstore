"""Remove the November 2025 test stock and stop the storefront advertising
stock status, so every item reads as orderable on a 7-day lead time.

    bench --site www.aabrick.com execute aabrick_webstore.clearstock.preview
    bench --site www.aabrick.com execute aabrick_webstore.clearstock.apply_all
"""

import frappe

# cancel in this order so dependent documents go first
ORDER = ["Stock Reconciliation", "Purchase Receipt", "Stock Entry",
         "Delivery Note", "Sales Invoice", "POS Invoice"]


def _vouchers():
    rows = frappe.db.sql("""
        SELECT voucher_type, voucher_no,
               COUNT(*) AS line_count,
               MIN(DATE(posting_date)) AS dt,
               ROUND(SUM(stock_value_difference), 2) AS value
        FROM `tabStock Ledger Entry`
        WHERE is_cancelled = 0
        GROUP BY voucher_type, voucher_no
        ORDER BY voucher_type, voucher_no
    """, as_dict=True)
    rank = {t: i for i, t in enumerate(ORDER)}
    rows.sort(key=lambda r: rank.get(r.voucher_type, 99))
    return rows


def preview():
    rows = _vouchers()
    print("=" * 70)
    print("STOCK CLEARANCE - PREVIEW")
    print("=" * 70)
    total = 0.0
    for r in rows:
        total += float(r.value or 0)
        print("   %-22s %-22s %s  lines=%-4d value=%.2f"
              % (r.voucher_type, r.voucher_no, r.dt, r.line_count, r.value or 0))
    print("\ndocuments to cancel and delete : %d" % len(rows))
    print("stock value to be removed      : ZMW %.2f" % total)

    bins = frappe.db.sql("""SELECT COUNT(*), IFNULL(SUM(actual_qty),0),
                                   IFNULL(SUM(stock_value),0)
                            FROM `tabBin` WHERE actual_qty <> 0""")[0]
    print("bins with quantity now         : %d  qty=%s  value=%.2f"
          % (bins[0], bins[1], bins[2]))

    print("\nSETTINGS TO CHANGE")
    for f in ("show_stock_availability", "show_quantity_in_website",
              "allow_items_not_in_stock"):
        print("   %-28s currently %s"
              % (f, frappe.db.get_single_value("Webshop Settings", f)))
    return len(rows)


def apply_all():
    cancelled = deleted = 0
    errors = []

    for r in _vouchers():
        try:
            doc = frappe.get_doc(r.voucher_type, r.voucher_no)
            if doc.docstatus == 1:
                doc.cancel()
                cancelled += 1
            frappe.delete_doc(r.voucher_type, r.voucher_no,
                              force=1, ignore_permissions=True)
            deleted += 1
        except Exception as e:
            errors.append((r.voucher_type, r.voucher_no, str(e)[:110]))
    frappe.db.commit()

    # clear any Bin rows the cancellations left behind
    stale = frappe.db.sql("""SELECT name FROM `tabBin` WHERE actual_qty <> 0""",
                          as_dict=True)
    for b in stale:
        try:
            frappe.db.set_value("Bin", b.name, {
                "actual_qty": 0, "stock_value": 0,
                "projected_qty": 0, "valuation_rate": 0,
            })
        except Exception as e:
            errors.append(("Bin", b.name, str(e)[:110]))
    frappe.db.commit()

    # the storefront should never announce stock status
    frappe.db.set_single_value("Webshop Settings", "show_stock_availability", 0)
    frappe.db.set_single_value("Webshop Settings", "show_quantity_in_website", 0)
    # items must stay listed and orderable regardless of stock
    frappe.db.set_single_value("Webshop Settings", "allow_items_not_in_stock", 1)
    frappe.db.commit()
    frappe.clear_cache()

    print("documents cancelled : %d" % cancelled)
    print("documents deleted   : %d" % deleted)
    print("bins zeroed         : %d" % len(stale))
    print("errors              : %d" % len(errors))
    for dt, name, err in errors[:12]:
        print("   FAIL %-20s %-20s %s" % (dt, name, err))

    left = frappe.db.sql("""SELECT COUNT(*), IFNULL(SUM(actual_qty),0),
                                   IFNULL(SUM(stock_value),0)
                            FROM `tabBin` WHERE actual_qty <> 0""")[0]
    sle = frappe.db.count("Stock Ledger Entry", {"is_cancelled": 0})
    print("\nbins with quantity  : %d  qty=%s  value=%.2f" % (left[0], left[1], left[2]))
    print("live ledger entries : %d" % sle)
    for f in ("show_stock_availability", "show_quantity_in_website",
              "allow_items_not_in_stock"):
        print("%-28s = %s" % (f, frappe.db.get_single_value("Webshop Settings", f)))
    return {"deleted": deleted, "errors": len(errors)}


def tidy_remnants():
    """Delete documents that cancelled but would not delete, and report any
    submitted stock document still standing."""
    deleted, errors = 0, []

    for dt in ("Stock Reconciliation", "Purchase Receipt", "Stock Entry",
               "Delivery Note"):
        for name in frappe.get_all(dt, filters={"docstatus": 2}, pluck="name"):
            try:
                frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
                deleted += 1
            except Exception as e:
                errors.append((dt, name, str(e)[:100]))
    frappe.db.commit()

    print("cancelled documents deleted : %d" % deleted)
    print("errors                      : %d" % len(errors))
    for dt, name, err in errors[:10]:
        print("   FAIL %-22s %-22s %s" % (dt, name, err))

    print("\n--- anything still submitted ---")
    for dt in ("Stock Reconciliation", "Purchase Receipt", "Stock Entry",
               "Delivery Note", "Sales Invoice", "POS Invoice"):
        rows = frappe.get_all(dt, filters={"docstatus": 1},
                              fields=["name"], limit=10)
        if rows:
            sle = frappe.db.count("Stock Ledger Entry",
                                  {"voucher_type": dt, "is_cancelled": 0})
            print("   %-22s submitted=%-3d live ledger rows=%d"
                  % (dt, len(rows), sle))
            for r in rows[:5]:
                print("        %s" % r.name)

    bins = frappe.db.sql("""SELECT COUNT(*), IFNULL(SUM(actual_qty),0),
                                   IFNULL(SUM(stock_value),0) FROM `tabBin`""")[0]
    live = frappe.db.sql("""SELECT COUNT(*) FROM `tabStock Ledger Entry`
                            WHERE IFNULL(is_cancelled,0)=0""")[0][0]
    print("\nbins: %d   total qty: %s   total value: %.2f" % (bins[0], bins[1], bins[2]))
    print("live (uncancelled) stock ledger entries: %d" % live)
    return deleted
