"""AABrick's own product page.

Webshop's Website Item controller is subclassed rather than patched, so all of
its shopping-cart, pricing and breadcrumb work still runs; only the template
changes, and the context gains what our page needs.

The descriptive parts are derived from the item group at render time rather
than written into 232 records. Item groups already carry the finish and the
size, which is what people actually search for: "600x600 glazed porcelain
tiles". Deriving means a better rule improves all 232 pages at once, and the
work travels with a git deploy instead of sitting in the database.
"""

import json
import os
import re

import frappe
from webshop.webshop.doctype.website_item.website_item import WebsiteItem

COMPANY = "AABrick Zambia Limited"
LEAD_TIME_DAYS = 7

# "Glazed Porcelain Tiles (600X1200) - 1268/9XX" -> name, size, code range.
# The space before the bracket is optional: one group is "Wall Tiles(250X400)".
GROUP_RE = re.compile(
    r"^(?P<name>.*?)\s*\(\s*(?P<w>\d+)\s*[xX]\s*(?P<h>\d+)\s*\)\s*$"
)


def _split_group(item_group):
    """The group without its code range, e.g. 'Wall Tiles (300X600)'."""
    return (item_group or "").split(" - ")[0].strip()


def describe_group(item_group):
    """Return (label, size, finish, grade) for an item group.

    label   what to call one of these, e.g. "Glazed Porcelain Tile 600x1200"
    size    "600 x 1200 mm", or None
    finish  "Glazed Porcelain", or None
    grade   "B" for the D groups, otherwise None

    D is the internal name for the second grade and the staff use it, so the
    groups keep it. A customer has no idea what D means, so the page says
    B Grade instead and the label drops the letter.
    """
    base = _split_group(item_group)
    if not base:
        return ("Product", None, None, None)

    m = GROUP_RE.match(base)
    if not m:
        # Tile Fix, Fertilizer, PVC ceiling boards: no size in the name.
        name = base.rstrip("s") if base.endswith("s") else base
        name, grade = _degrade(name)
        return (name, None, None, grade)

    name = m.group("name").strip()
    name, grade = _degrade(name)
    size = "%s x %s mm" % (m.group("w"), m.group("h"))
    singular = re.sub(r"\bTiles\b", "Tile", name)
    finish = re.sub(r"\s*Tiles?\s*$", "", name).strip() or None
    return ("%s %sx%s" % (singular, m.group("w"), m.group("h")), size, finish, grade)


def _degrade(name):
    """Strip a trailing D and report the grade it stood for."""
    stripped = re.sub(r"\s+D$", "", name)
    return (stripped, "B") if stripped != name else (name, None)


def _image_path(url):
    rel = (url or "").lstrip("/")
    if not rel:
        return None
    if rel.startswith("files/"):
        return frappe.get_site_path("public", rel)
    if rel.startswith("private/files/"):
        return frappe.get_site_path(rel)
    return None


UNITS = {"box": "box", "nos": "each", "unit": "unit", "pcs": "piece",
         "piece": "piece", "sqm": "m2", "square meter": "m2"}


def unit_label(item_code):
    """What one price buys, in words a customer uses.

    sales_uom is unset across the catalogue, so this falls back to stock_uom,
    which is Box on 423 of the 436 published items. "Nos" is ERP shorthand for
    a count and is shown as "each".
    """
    uom = (
        frappe.db.get_value("Item", item_code, "sales_uom")
        or frappe.db.get_value("Item", item_code, "stock_uom")
        or ""
    )
    return UNITS.get(uom.strip().lower(), uom.strip().lower() or None)


def image_shape(url):
    """wide, tall or square. The card and the page give each different room."""
    path = _image_path(url)
    if not path or not os.path.exists(path):
        return "square"
    try:
        from PIL import Image

        with Image.open(path) as im:
            ratio = im.width / float(im.height or 1)
    except Exception:
        return "square"
    if ratio >= 1.4:
        return "wide"
    if ratio <= 0.8:
        return "tall"
    return "square"


class AABrickWebsiteItem(WebsiteItem):
    website = frappe._dict(
        page_title_field="web_item_name",
        condition_field="published",
        template="templates/generators/aab_item.html",
    )

    def get_context(self, context):
        context = super().get_context(context)

        label, size, finish, grade = describe_group(self.item_group)
        code = self.item_code or self.name

        context.aab_label = label
        context.aab_size = size
        context.aab_finish = finish
        context.aab_grade = grade
        context.aab_grade_note = (
            "B grade stock: the same tile at a lower price than A grade."
            if grade == "B" else None
        )
        context.aab_code = code
        context.aab_group = _split_group(self.item_group)
        context.aab_group_route = self._group_route()
        context.aab_shape = image_shape(self.website_image)
        context.aab_lead_time = LEAD_TIME_DAYS
        context.aab_company_phone = "+260 960 787 777"
        context.aab_branch_count = frappe.db.count("Branch Location") or 46
        context.aab_spec = (self.web_long_description or self.description or "").strip()

        price = self._price(context)
        context.aab_price = price

        suffix = " (%s Grade)" % grade if grade else ""
        context.aab_heading = ("%s %s%s" % (code, label, suffix)) if label != "Product" else code
        context.title = "%s | AABrick Zambia" % context.aab_heading
        context.aab_description = self._meta_description(label, size, price)
        context.aab_canonical = frappe.utils.get_url(self.route or "")
        context.aab_schema = self._schema(context, label, price)
        context.aab_related = self._related()

        # Webshop's set_metatags filled these from the raw spec line. Ours are
        # written for a person reading a search result.
        context.metatags = context.metatags or frappe._dict()
        context.metatags.update({
            "title": context.title,
            "description": context.aab_description,
            "image": self.website_image or None,
            "og:type": "product",
        })
        return context

    # ------------------------------------------------------------------
    def _group_route(self):
        route = frappe.db.get_value("Item Group", self.item_group, "route")
        return "/" + route if route else "/all-products"

    def _price(self, context):
        info = (context.get("shopping_cart") or {}).get("product_info") or {}
        price = info.get("price") or {}
        if not price:
            return None
        return frappe._dict({
            "formatted": price.get("formatted_price_sales_uom") or price.get("formatted_price"),
            "value": price.get("price_list_rate"),
            "currency": price.get("currency") or "ZMW",
            "uom": unit_label(self.item_code) or info.get("uom"),
            "in_stock": info.get("in_stock"),
        })

    def _meta_description(self, label, size, price):
        bits = [label]
        if size:
            bits.append(size)
        line = ", ".join(bits)
        money = (" %s" % price.formatted) if price and price.formatted else ""
        return (
            "%s, code %s.%s from AABrick Zambia. Available at %s branches "
            "nationwide, or delivered within %s days on anything not in stock."
            % (line, self.item_code, money, self._branches(), LEAD_TIME_DAYS)
        )

    def _branches(self):
        return frappe.db.count("Branch Location") or 46

    def _schema(self, context, label, price):
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "sku": self.item_code,
            "name": context.aab_heading,
            "url": context.aab_canonical,
        }
        if self.website_image:
            data["image"] = [frappe.utils.get_url(self.website_image)]
        if context.aab_description:
            data["description"] = context.aab_description
        if getattr(self, "brand", None):
            data["brand"] = {"@type": "Brand", "name": self.brand}

        if price and price.value:
            data["offers"] = {
                "@type": "Offer",
                "url": context.aab_canonical,
                "priceCurrency": price.currency,
                "price": "%.2f" % float(price.value),
                # Anything not on a shelf today is ordered from the
                # manufacturer, so BackOrder is the honest term for it.
                "availability": "https://schema.org/InStock" if price.in_stock
                else "https://schema.org/BackOrder",
                "seller": {"@type": "Organization", "name": COMPANY},
            }
        return json.dumps(data, indent=2)

    def _related(self):
        """Four more from the same group, so a visitor can compare finishes."""
        rows = frappe.db.sql(
            """
            SELECT wi.item_code, wi.route, wi.website_image, wi.item_group,
                   ip.price_list_rate
            FROM `tabWebsite Item` wi
            LEFT JOIN `tabItem Price` ip
              ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
            WHERE wi.published = 1 AND wi.item_group = %s AND wi.name != %s
              AND IFNULL(wi.website_image, '') <> ''
            ORDER BY wi.item_code
            LIMIT 4
            """,
            (self.item_group, self.name),
            as_dict=True,
        )
        label, _size, _finish, grade = describe_group(self.item_group)
        for r in rows:
            r["shape"] = image_shape(r.website_image)
            r["label"] = label
            r["grade"] = grade
            r["uom"] = unit_label(r.item_code)
            r["price"] = (
                frappe.utils.fmt_money(r.price_list_rate, currency="ZMW")
                if r.price_list_rate else None
            )
        return rows
