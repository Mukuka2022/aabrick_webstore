"""Extend the chart of accounts for a 46-branch building-materials retailer.

Builds on the existing Standard-with-Numbers chart rather than replacing it.

    bench --site www.aabrick.com execute aabrick_webstore.coa_build.preview
    bench --site www.aabrick.com execute aabrick_webstore.coa_build.apply_all
"""

import frappe

COMPANY = "AABrick Zambia Limited"
ABBR = "AZL"

DIRECT_INCOME = "4100 - Direct Income - AZL"
INDIRECT_EXP = "5200 - Indirect Expenses - AZL"
EXPENSES = "5000 - Expenses - AZL"
CURRENT_ASSETS = "1100-1600 - Current Assets - AZL"
CASH_IN_HAND = "1100 - Cash In Hand - AZL"
DUTIES = "2300 - Duties and Taxes - AZL"
PAYABLES = "2100 - Accounts Payable - AZL"

# (number, name, parent, is_group, root_type, account_type)
NEW_GROUPS = [
    ("5300", "Branch Operating Expenses", EXPENSES, 1, "Expense", ""),
    ("5400", "Distribution Expenses", EXPENSES, 1, "Expense", ""),
    ("5500", "Central Overheads", EXPENSES, 1, "Expense", ""),
]

BRANCH_EXPENSES = [
    ("5301", "Shop Rent"),
    ("5302", "Branch Wages and Salaries"),
    ("5303", "Casual Labour"),
    ("5304", "Electricity"),
    ("5305", "Water"),
    ("5306", "Security Services"),
    ("5307", "Cleaning and Sanitation"),
    ("5308", "Repairs and Maintenance - Shop"),
    ("5309", "Shop Consumables and Packaging"),
    ("5310", "Bank and Mobile Money Charges"),
    ("5311", "Breakages and Shrinkage"),
]

DISTRIBUTION_EXPENSES = [
    ("5401", "Fuel and Lubricants"),
    ("5402", "Vehicle Repairs and Maintenance"),
    ("5403", "Drivers Wages"),
    ("5404", "Third Party Haulage"),
    ("5405", "Vehicle Insurance and Licensing"),
]

CENTRAL_EXPENSES = [
    ("5501", "Directors Remuneration"),
    ("5502", "Audit and Accountancy Fees"),
    ("5503", "Group Marketing and Advertising"),
    ("5504", "IT Software and Subscriptions"),
    ("5505", "Insurance"),
    ("5506", "Licences and Permits"),
    ("5507", "Staff Training and Welfare"),
]

NEW_INCOME = [
    ("4131", "Sales - Sanitary Ware"),
    ("4132", "Sales - PVC and Ceiling"),
    ("4133", "Sales - Lighting and Electrical"),
    ("4134", "Sales - Doors and Hardware"),
    ("4135", "Delivery and Transport Income"),
]

NEW_ASSETS = [
    ("1120", "Cash In Transit", CASH_IN_HAND, "Asset", "Cash"),
    ("1130", "Till Floats", CASH_IN_HAND, "Asset", "Cash"),
]

NEW_LIABILITIES = [
    ("2320", "Output VAT", DUTIES, "Liability", "Tax"),
    ("2330", "Input VAT", DUTIES, "Liability", "Tax"),
    ("2340", "Withholding Tax Payable", DUTIES, "Liability", "Tax"),
    ("2130", "Customer Deposits and Advances", PAYABLES, "Liability", ""),
]

def _blank_type_income():
    """Leaf income accounts with no account_type set.

    Found dynamically because some existing names use an en-dash, which makes
    hardcoding the name fragile.
    """
    return frappe.get_all(
        "Account",
        filters={"company": COMPANY, "root_type": "Income", "is_group": 0,
                 "account_type": ["in", ["", None]]},
        pluck="name",
    )


def _full(number, name):
    return "%s - %s - %s" % (number, name, ABBR)


def _all_planned():
    rows = []
    for num, name, parent, is_group, root, atype in NEW_GROUPS:
        rows.append((num, name, parent, is_group, root, atype))
    for num, name in BRANCH_EXPENSES:
        rows.append((num, name, _full("5300", "Branch Operating Expenses"), 0,
                     "Expense", "Expense Account"))
    for num, name in DISTRIBUTION_EXPENSES:
        rows.append((num, name, _full("5400", "Distribution Expenses"), 0,
                     "Expense", "Expense Account"))
    for num, name in CENTRAL_EXPENSES:
        rows.append((num, name, _full("5500", "Central Overheads"), 0,
                     "Expense", "Expense Account"))
    for num, name in NEW_INCOME:
        rows.append((num, name, DIRECT_INCOME, 0, "Income", "Income Account"))
    for num, name, parent, root, atype in NEW_ASSETS:
        rows.append((num, name, parent, 0, root, atype))
    for num, name, parent, root, atype in NEW_LIABILITIES:
        rows.append((num, name, parent, 0, root, atype))
    return rows


def preview():
    rows = _all_planned()
    print("=" * 74)
    print("CHART OF ACCOUNTS EXTENSION - PREVIEW (%d accounts)" % len(rows))
    print("=" * 74)
    new = exists = 0
    last_parent = None
    for num, name, parent, is_group, root, atype in rows:
        if parent != last_parent:
            print("\n  under %s" % parent)
            last_parent = parent
        full = _full(num, name)
        if frappe.db.exists("Account", full):
            exists += 1
            print("     = %-46s (exists)" % full)
        else:
            new += 1
            kind = "GROUP" if is_group else atype or root
            print("     + %-46s %s" % (full, kind))
    print("\n  FIXES")
    for acct in _blank_type_income():
        print("     ~ %-46s blank -> Income Account" % acct)
    print("\nto create: %d   already present: %d" % (new, exists))
    return {"new": new, "exists": exists}


def apply_all():
    created = skipped = fixed = 0
    errors = []
    for num, name, parent, is_group, root, atype in _all_planned():
        full = _full(num, name)
        if frappe.db.exists("Account", full):
            skipped += 1
            continue
        try:
            doc = frappe.get_doc({
                "doctype": "Account",
                "account_name": name,
                "account_number": num,
                "parent_account": parent,
                "is_group": is_group,
                "root_type": root,
                "company": COMPANY,
            })
            if atype:
                doc.account_type = atype
            doc.insert(ignore_permissions=True)
            created += 1
        except Exception as e:
            errors.append((full, str(e)[:100]))

    for acct in _blank_type_income():
        try:
            frappe.db.set_value("Account", acct, "account_type", "Income Account")
            fixed += 1
        except Exception as e:
            errors.append((acct, str(e)[:100]))

    frappe.db.commit()
    print("accounts created : %d" % created)
    print("already present  : %d" % skipped)
    print("fixed            : %d" % fixed)
    print("errors           : %d" % len(errors))
    for full, err in errors[:15]:
        print("  FAIL %-48s %s" % (full, err))
    print("\ntotal accounts now: %d" % frappe.db.count("Account", {"company": COMPANY}))
    return {"created": created, "errors": len(errors)}


OUTPUT_VAT = "2320 - Output VAT - AZL"
INPUT_VAT = "2330 - Input VAT - AZL"


def split_vat():
    """Point sales tax rows at Output VAT and purchase tax rows at Input VAT.

    They currently both post to a single 'VAT - AZL' account, which nets the
    two together and makes the VAT return hard to prepare and audit.
    """
    moved = []
    for dt, target in (("Sales Taxes and Charges", OUTPUT_VAT),
                       ("Purchase Taxes and Charges", INPUT_VAT)):
        rows = frappe.get_all(dt, fields=["name", "parent", "account_head", "rate"])
        for r in rows:
            if r.account_head == target:
                continue
            frappe.db.set_value(dt, r.name, "account_head", target)
            moved.append((dt, r.parent, r.account_head, target, r.rate))
    frappe.db.commit()
    print("VAT ROUTING")
    for dt, parent, old, new, rate in moved:
        print("  %-28s %-18s %s -> %s  @%.0f%%"
              % (dt, parent, old, new, rate or 0))
    if not moved:
        print("  (already routed correctly)")
    print("\n%d tax rows repointed" % len(moved))
    return len(moved)
