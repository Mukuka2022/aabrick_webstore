"""Write down an ERPNext bench's trading structure, and what has been posted
against every part of it.

Read only. It opens nothing it does not read, writes nothing to the database,
and the one file it creates is a report. Safe to run on a live server.

    bench --site SITE execute aabrick_webstore.erp_audit.export

It prints where it wrote the file. Send that file back.

The counts are the point. A warehouse with no stock ledger entries can be
renamed or retired freely; one with eleven thousand cannot, and no plan that
pretends otherwise is worth reading.
"""

import io
import json
import os

import frappe

# doctype -> (parent field, the table that records use of it, its column)
SHAPES = {
    "Account": ("parent_account", "GL Entry", "account"),
    "Cost Center": ("parent_cost_center", "GL Entry", "cost_center"),
    "Warehouse": ("parent_warehouse", "Stock Ledger Entry", "warehouse"),
    "Mode of Payment": (None, None, None),
    "Item Group": ("parent_item_group", None, None),
}

# fields worth carrying, taken only when the doctype actually has them
WANTED = [
    "name", "company", "is_group", "disabled", "root_type", "report_type",
    "account_type", "account_number", "account_currency", "account_name",
    "warehouse_name", "cost_center_name", "item_group_name", "enabled",
    "type", "is_default", "parent_item_group", "lft", "rgt",
]


def _fields_for(dt):
    meta = frappe.get_meta(dt)
    have = {df.fieldname for df in meta.fields}
    have.add("name")
    return [f for f in WANTED if f in have]


def _usage(table, column):
    """How many live rows point at each value, cancelled ones excluded."""
    if not table or not frappe.db.table_exists(table):
        return {}
    cancelled = ""
    if "is_cancelled" in {df.fieldname for df in frappe.get_meta(table).fields}:
        cancelled = "where is_cancelled = 0"
    rows = frappe.db.sql(
        "select `%s` as k, count(*) as n from `tab%s` %s group by `%s`"
        % (column, table, cancelled, column), as_dict=True)
    return {r["k"]: r["n"] for r in rows if r["k"]}


def export():
    out = {
        "site": frappe.local.site,
        "taken": frappe.utils.now(),
        "versions": {},
        "companies": [],
        "doctypes": {},
    }

    for app in ("frappe", "erpnext"):
        try:
            out["versions"][app] = __import__(app).__version__
        except Exception:
            out["versions"][app] = "unknown"

    for c in frappe.get_all("Company", fields=["name", "abbr",
                                               "default_currency"]):
        out["companies"].append(dict(c))

    for dt, (parent_field, table, column) in SHAPES.items():
        if not frappe.db.exists("DocType", dt):
            out["doctypes"][dt] = {"missing": True}
            continue
        fields = _fields_for(dt)
        if parent_field:
            fields = fields + [parent_field]
        rows = frappe.get_all(dt, fields=fields, limit_page_length=0,
                              order_by="name")
        used = _usage(table, column)
        for r in rows:
            r["_parent"] = r.get(parent_field) if parent_field else None
            r["_used"] = used.get(r["name"], 0)
        out["doctypes"][dt] = {
            "parent_field": parent_field,
            "usage_from": "%s.%s" % (table, column) if table else None,
            "count": len(rows),
            "rows": [dict(r) for r in rows],
        }
        total = sum(r["_used"] for r in rows)
        carrying = sum(1 for r in rows if r["_used"])
        print("  %-16s %4d records, %4d carry history, %d rows in all"
              % (dt, len(rows), carrying, total))

    folder = frappe.get_site_path("private", "files")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    path = os.path.join(folder, "erp-audit-%s.json"
                        % frappe.local.site.replace(".", "-"))
    with io.open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=1, default=str))

    print("\n  written to %s" % path)
    print("  %.0f kB -- send this file back" % (os.path.getsize(path) / 1024.0))
    return path
