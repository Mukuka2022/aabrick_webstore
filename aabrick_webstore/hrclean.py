"""Delete HRMS Branch records that do not match an active branch warehouse.

Employee.branch is cleared first, so the delete does not fail on links. The
mapping is dumped to /tmp/employee_branch_backup.csv before anything is removed.

    bench --site www.aabrick.com execute aabrick_webstore.hrclean.preview
    bench --site www.aabrick.com execute aabrick_webstore.hrclean.apply_all
"""

import csv
import frappe

ABBR = "AZL"
SKIP_PARENTS = ("All Warehouses - AZL", "Website Warehouses - AZL")
BACKUP = "/tmp/employee_branch_backup.csv"

# lowercase strays that block the correctly-cased records
RECASE = {"livingstone": "Livingstone", "Sos": "SOS"}


def _active_branches():
    names = set()
    for r in frappe.get_all("Warehouse",
                            filters={"is_group": 0, "disabled": 0},
                            fields=["name", "parent_warehouse"]):
        if not r.parent_warehouse or r.parent_warehouse in SKIP_PARENTS:
            continue
        clean = r.name
        for suffix in (" - %s" % ABBR, " - ALZ"):
            while clean.endswith(suffix):
                clean = clean[: -len(suffix)]
        names.add(clean)
    return names


def _stale():
    active = _active_branches()
    existing = set(frappe.get_all("Branch", pluck="name"))
    # a lowercase stray is stale even though its proper-cased twin is active
    stale = {b for b in existing if b not in active}
    stale |= {b for b in existing if b in RECASE}
    return sorted(stale), active


def preview():
    stale, active = _stale()
    print("active branch warehouses : %d" % len(active))
    print("HR Branch records         : %d" % frappe.db.count("Branch"))
    print("\nTO DELETE (%d):" % len(stale))
    total_emp = 0
    for b in stale:
        n = frappe.db.count("Employee", {"branch": b})
        total_emp += n
        flag = "  <-- %d employees will lose their branch" % n if n else ""
        print("   - %-20s%s" % (b, flag))
    print("\nemployees affected: %d" % total_emp)
    print("recase after delete: %s" % ", ".join("%s -> %s" % (k, v)
                                                for k, v in RECASE.items()))
    return {"delete": len(stale), "employees": total_emp}


def apply_all():
    stale, active = _stale()

    # 1. back up the mapping before touching anything
    rows = frappe.get_all("Employee",
                          filters={"branch": ["in", stale]},
                          fields=["name", "employee_name", "branch",
                                  "designation", "status"])
    with open(BACKUP, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["employee", "employee_name", "branch", "designation", "status"])
        for r in rows:
            w.writerow([r.name, r.employee_name, r.branch, r.designation, r.status])
    print("backed up %d employee-branch rows to %s" % (len(rows), BACKUP))

    # 2. clear the link so deletes do not fail
    cleared = 0
    for r in rows:
        frappe.db.set_value("Employee", r.name, "branch", None)
        cleared += 1
    frappe.db.commit()

    # 3. delete the stale branch records
    deleted, errors = 0, []
    for b in stale:
        try:
            frappe.delete_doc("Branch", b, force=1, ignore_permissions=True)
            deleted += 1
        except Exception as e:
            errors.append((b, str(e)[:100]))
    frappe.db.commit()

    # 4. recreate the two that were blocked by lowercase strays
    recreated = []
    for proper in RECASE.values():
        if proper in active and not frappe.db.exists("Branch", proper):
            try:
                frappe.get_doc({"doctype": "Branch",
                                "branch": proper}).insert(ignore_permissions=True)
                recreated.append(proper)
            except Exception as e:
                errors.append((proper, str(e)[:100]))
    frappe.db.commit()

    remaining = set(frappe.get_all("Branch", pluck="name"))
    print("\nemployee links cleared : %d" % cleared)
    print("branch records deleted : %d" % deleted)
    print("recreated properly     : %s" % (", ".join(recreated) or "none"))
    print("errors                 : %d" % len(errors))
    for b, err in errors[:10]:
        print("   FAIL %-20s %s" % (b, err))

    print("\nHR Branch records now  : %d" % len(remaining))
    print("active warehouses      : %d" % len(active))
    missing = sorted(active - remaining)
    extra = sorted(remaining - active)
    print("missing from HR list   : %s" % (", ".join(missing) or "none"))
    print("extra in HR list       : %s" % (", ".join(extra) or "none"))
    return {"deleted": deleted, "cleared": cleared, "errors": len(errors)}
