"""Branch Location: a public page per branch.

AABrick is not one local business, it is one brand plus 46 local locations.
Customers search "tiles Kitwe", not "AABrick". Without a page per branch there
is nothing for those searches to land on, and nothing for a Google Business
Profile to link to.

Each record becomes a page at /branches/<route> automatically, because the
doctype is a website generator.

    bench --site www.aabrick.com execute aabrick_webstore.branches.install
    bench --site www.aabrick.com execute aabrick_webstore.branches.seed
    bench --site www.aabrick.com execute aabrick_webstore.branches.status
"""

import re
import frappe

DOCTYPE = "Branch Location"
MODULE = "Aabrick Webstore"
COMPANY_PHONE = "+260 960 787 777"
SKIP_PARENTS = ("All Warehouses - AZL", "Website Warehouses - AZL")
ABBR = "AZL"


def slug(text):
    s = (text or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


# --------------------------------------------------------------- setup
def install():
    if frappe.db.exists("DocType", DOCTYPE):
        print("%s already exists" % DOCTYPE)
        return

    frappe.get_doc({
        "doctype": "DocType",
        "name": DOCTYPE,
        "module": MODULE,
        "custom": 0,
        "autoname": "field:branch_name",
        "naming_rule": "By fieldname",
        "has_web_view": 1,
        "is_published_field": "published",
        "allow_rename": 1,
        "track_changes": 1,
        "sort_field": "branch_name",
        "sort_order": "ASC",
        "fields": [
            {"fieldname": "branch_name", "label": "Branch Name", "fieldtype": "Data",
             "reqd": 1, "unique": 1, "in_list_view": 1},
            {"fieldname": "published", "label": "Published", "fieldtype": "Check",
             "default": "0", "in_list_view": 1},
            {"fieldname": "route", "label": "Route", "fieldtype": "Data",
             "read_only": 1},
            {"fieldname": "col_1", "fieldtype": "Column Break"},
            {"fieldname": "warehouse", "label": "Warehouse", "fieldtype": "Link",
             "options": "Warehouse", "in_list_view": 1},
            {"fieldname": "province", "label": "Province", "fieldtype": "Data",
             "in_list_view": 1},
            {"fieldname": "region", "label": "Region", "fieldtype": "Select",
             "options": "North\nSouth"},

            {"fieldname": "sec_contact", "label": "Contact", "fieldtype": "Section Break"},
            {"fieldname": "street_address", "label": "Street Address",
             "fieldtype": "Small Text",
             "description": "Plot number, road, area. Shown on the page and used for local SEO."},
            {"fieldname": "city", "label": "City or Town", "fieldtype": "Data"},
            {"fieldname": "col_2", "fieldtype": "Column Break"},
            {"fieldname": "phone", "label": "Phone", "fieldtype": "Data",
             "default": COMPANY_PHONE},
            {"fieldname": "whatsapp", "label": "WhatsApp Number", "fieldtype": "Data",
             "description": "International format without + or spaces, e.g. 260960787777"},
            {"fieldname": "email", "label": "Email", "fieldtype": "Data"},

            {"fieldname": "sec_hours", "label": "Opening Hours", "fieldtype": "Section Break"},
            {"fieldname": "hours_weekday", "label": "Monday to Friday",
             "fieldtype": "Data", "default": "08:00 - 17:00"},
            {"fieldname": "hours_saturday", "label": "Saturday",
             "fieldtype": "Data", "default": "08:00 - 13:00"},
            {"fieldname": "col_3", "fieldtype": "Column Break"},
            {"fieldname": "hours_sunday", "label": "Sunday",
             "fieldtype": "Data", "default": "Closed"},
            {"fieldname": "hours_note", "label": "Note", "fieldtype": "Data"},

            {"fieldname": "sec_map", "label": "Location", "fieldtype": "Section Break"},
            {"fieldname": "latitude", "label": "Latitude", "fieldtype": "Float",
             "precision": "6"},
            {"fieldname": "longitude", "label": "Longitude", "fieldtype": "Float",
             "precision": "6"},
            {"fieldname": "col_4", "fieldtype": "Column Break"},
            {"fieldname": "maps_url", "label": "Google Maps Link", "fieldtype": "Data"},
            {"fieldname": "gbp_url", "label": "Google Business Profile", "fieldtype": "Data"},

            {"fieldname": "sec_content", "label": "Page Content", "fieldtype": "Section Break"},
            {"fieldname": "intro", "label": "Intro", "fieldtype": "Small Text",
             "description": "One or two sentences shown under the heading."},
            {"fieldname": "meta_description", "label": "Meta Description",
             "fieldtype": "Small Text"},
        ],
        "permissions": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "Website Manager", "read": 1, "write": 1, "create": 1},
            {"role": "Area Business Manager", "read": 1, "write": 1},
            {"role": "Guest", "read": 1},
        ],
    }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("created %s" % DOCTYPE)


# --------------------------------------------------------------- seed
def _branches():
    rows = frappe.get_all(
        "Warehouse",
        filters={"is_group": 0, "disabled": 0},
        fields=["name", "parent_warehouse"],
        order_by="name",
    )
    out = []
    for r in rows:
        if not r.parent_warehouse or r.parent_warehouse in SKIP_PARENTS:
            continue
        clean = r.name
        for suffix in (" - %s" % ABBR, " - ALZ"):
            while clean.endswith(suffix):
                clean = clean[: -len(suffix)]
        province = r.parent_warehouse.replace(" - %s" % ABBR, "").replace(" Province", "")
        region = "North" if frappe.db.get_value(
            "Warehouse", r.parent_warehouse, "parent_warehouse") == "Northern Region - AZL" \
            else "South"
        out.append({"branch": clean, "warehouse": r.name,
                    "province": province, "region": region})
    return out


def seed():
    """Create one unpublished Branch Location per active branch warehouse.

    Left unpublished on purpose: a branch page with no address helps nobody.
    Publish each one as its address and hours are filled in.
    """
    created = skipped = 0
    for b in _branches():
        if frappe.db.exists(DOCTYPE, b["branch"]):
            skipped += 1
            continue
        doc = frappe.get_doc({
            "doctype": DOCTYPE,
            "branch_name": b["branch"],
            "warehouse": b["warehouse"],
            "province": b["province"],
            "region": b["region"],
            "city": b["branch"],
            "phone": COMPANY_PHONE,
            "published": 0,
            "route": "branches/%s" % slug(b["branch"]),
            "intro": "Tiles, tile fix, PVC ceiling boards and fertilizer at "
                     "AABrick %s in %s Province." % (b["branch"], b["province"]),
            "meta_description": "AABrick %s - tiles, tile fix, PVC ceiling boards "
                                "and fertilizer in %s, Zambia. Visit us or call %s."
                                % (b["branch"], b["province"], COMPANY_PHONE),
        })
        doc.insert(ignore_permissions=True)
        created += 1
    frappe.db.commit()
    print("branch locations created : %d" % created)
    print("already present          : %d" % skipped)
    print("total                    : %d" % frappe.db.count(DOCTYPE))
    return created


def status():
    total = frappe.db.count(DOCTYPE)
    pub = frappe.db.count(DOCTYPE, {"published": 1})
    no_addr = frappe.db.count(DOCTYPE, {"street_address": ["in", ["", None]]})
    print("branch locations : %d" % total)
    print("published        : %d" % pub)
    print("missing address  : %d" % no_addr)
    print("\nready to publish (have an address):")
    for r in frappe.get_all(DOCTYPE,
                            filters={"street_address": ["not in", ["", None]]},
                            fields=["branch_name", "published"], limit=20):
        print("   %-22s published=%s" % (r.branch_name, bool(r.published)))
    if not no_addr == total:
        return
    print("   (none yet - fill in addresses, then publish)")


def publish_ready():
    """Publish every branch that has an address. Safe to re-run."""
    rows = frappe.get_all(DOCTYPE,
                          filters={"street_address": ["not in", ["", None]],
                                   "published": 0},
                          pluck="name")
    for name in rows:
        frappe.db.set_value(DOCTYPE, name, "published", 1)
    frappe.db.commit()
    frappe.clear_cache()
    print("published %d branch pages" % len(rows))
    return len(rows)


def install_debug():
    """bench execute masks the real error behind a NameError from its eval
    fallback. This prints the actual traceback."""
    import traceback
    try:
        install()
    except Exception:
        traceback.print_exc()


def seed_debug():
    import traceback
    try:
        seed()
    except Exception:
        traceback.print_exc()


def grant_guest_read():
    """Website generator doctypes need a Guest read permission.

    Without it the path resolver hands anonymous visitors a NotFoundPage and
    every branch page 404s, while it renders fine when logged in as
    Administrator - which makes it easy to miss.
    """
    from frappe.permissions import add_permission, update_permission_property
    add_permission(DOCTYPE, "Guest", 0)
    update_permission_property(DOCTYPE, "Guest", 0, "read", 1)
    frappe.db.commit()
    frappe.clear_cache()
    rows = frappe.get_all("Custom DocPerm",
                          filters={"parent": DOCTYPE},
                          fields=["role", "read"], order_by="role")
    print("permissions on %s:" % DOCTYPE)
    for r in rows:
        print("   %-24s read=%s" % (r.role, r.read))
    return len(rows)
