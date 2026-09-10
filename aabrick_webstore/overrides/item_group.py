"""AABrick's own category page.

Webshop's Item Group controller is subclassed rather than patched, so its
filter engine and breadcrumb work still runs, and only the template changes.

The important difference from webshop's page is that the products are rendered
on the server. Webshop ships an empty card and fills the grid from JavaScript
afterwards, which means the page source a crawler sees contains no products at
all. These groups hold at most 56 items, so the whole grid fits in one page
with no pagination and no second request.
"""

import frappe
from webshop.webshop.doctype.override_doctype.item_group import WebshopItemGroup

from aabrick_webstore.overrides.website_item import describe_group, image_shape

LEAD_TIME_DAYS = 7


class AABrickItemGroup(WebshopItemGroup):
	website = frappe._dict(
		condition_field="show_in_website",
		template="templates/generators/aab_item_group.html",
		no_cache=1,
		no_breadcrumbs=1,
	)

	def get_context(self, context):
		context = super().get_context(context)

		label, size, finish, grade = describe_group(self.name)
		context.aab_label = label
		context.aab_size = size
		context.aab_finish = finish
		context.aab_grade = grade
		context.aab_group = self.name.split(" - ")[0].strip()

		# "Glazed Porcelain Tile 600x600" reads better as a heading than
		# "Glazed Porcelain Tiles (600X600) - 86XXX", which is a stock code.
		plural = _plural(label)
		context.aab_heading = "%s%s" % (plural, " (B Grade)" if grade else "")

		products = self._products()
		context.aab_products = products
		context.aab_count = len(products)
		context.aab_price_from = min(
			[p.price_value for p in products if p.price_value] or [0]
		) or None

		context.aab_twin = self._twin()
		context.aab_lead_time = LEAD_TIME_DAYS
		context.aab_branch_count = frappe.db.count("Branch Location") or 46

		context.title = "%s | AABrick Zambia" % context.aab_heading
		context.aab_canonical = frappe.utils.get_url(self.route or "")
		context.aab_description = self._description(context, products)
		context.metatags = context.metatags or frappe._dict()
		context.metatags.update({
			"title": context.title,
			"description": context.aab_description,
		})
		return context

	# ------------------------------------------------------------------
	def _products(self):
		rows = frappe.db.sql(
			"""
			SELECT wi.item_code, wi.route, wi.website_image, wi.item_group,
			       ip.price_list_rate
			FROM `tabWebsite Item` wi
			LEFT JOIN `tabItem Price` ip
			  ON ip.item_code = wi.item_code AND ip.price_list = 'Web Price List'
			WHERE wi.published = 1 AND wi.item_group = %s
			ORDER BY wi.item_code
			""",
			(self.name,),
			as_dict=True,
		)
		for r in rows:
			r["shape"] = image_shape(r.website_image)
			r["price_value"] = r.price_list_rate
			r["price"] = (
				frappe.utils.fmt_money(r.price_list_rate, currency="ZMW")
				if r.price_list_rate else None
			)
		return rows

	def _twin(self):
		"""The same tile in the other grade, which is a real alternative rather
		than a related product.

		Matched by normalising rather than by editing the string: one group is
		written "Wall Tiles(250X400)" with no space while its twin is
		"Wall Tiles D (250X400)" with one, so inserting " D " into the first
		produces a name that does not exist.
		"""
		mine = _key(self.name)
		for row in frappe.get_all(
			"Item Group",
			filters={"is_group": 0, "show_in_website": 1},
			fields=["name", "route"],
		):
			if row.name == self.name or not row.route:
				continue
			if _key(row.name) != mine:
				continue
			_, _, _, grade = describe_group(row.name)
			return frappe._dict({
				"route": "/" + row.route,
				"grade": grade or "A",
				"count": frappe.db.count(
					"Website Item", {"item_group": row.name, "published": 1}
				),
			})
		return None

	def _description(self, context, products):
		bits = [context.aab_heading]
		if context.aab_size:
			bits.append(context.aab_size)
		money = ""
		if context.aab_price_from:
			money = " From %s." % frappe.utils.fmt_money(
				context.aab_price_from, currency="ZMW"
			)
		return (
			"%s at AABrick Zambia. %d designs in stock.%s Available at %s branches "
			"nationwide, or delivered within %s days."
			% (", ".join(bits), len(products), money,
			   context.aab_branch_count, LEAD_TIME_DAYS)
		)


def _key(name):
	"""A group name with its grade letter and its spacing taken out, so the two
	grades of the same tile land on the same key."""
	import re

	out = re.sub(r"\s+D\s*\(", "(", name)
	out = re.sub(r"\s+D\s*$", "", out)
	return re.sub(r"\s+", "", out).lower()


def _plural(label):
	"""describe_group returns the singular, which suits one product page; a
	category page is talking about all of them.

	Only the tile ranges pluralise, and they are the labels shaped
	"<finish> Tile <size>". Matching any word "Tile" turned the adhesive,
	"Tile Fix", into "Tiles Fix".
	"""
	import re

	return re.sub(r"\bTile\b(?=\s+\d+\s*x\s*\d+$)", "Tiles", label)
