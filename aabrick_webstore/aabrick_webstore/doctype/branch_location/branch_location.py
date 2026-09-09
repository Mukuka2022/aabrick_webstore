# Copyright (c) 2026, Adam & Mukuka and contributors
# For license information, please see license.txt

"""One public page per branch.

Frappe scaffolds a controller extending Document even when has_web_view is set,
so this is written by hand. Extending WebsiteGenerator is what gives each record
its own URL and keeps the published checkbox meaningful.
"""

import re

import frappe
from frappe.website.website_generator import WebsiteGenerator


def slug(text):
	s = (text or "").lower().strip()
	s = re.sub(r"[^a-z0-9]+", "-", s)
	return re.sub(r"-+", "-", s).strip("-")


class BranchLocation(WebsiteGenerator):
	website = frappe._dict(
		template="templates/generators/branch_location.html",
		condition_field="published",
		page_title_field="branch_name",
		parent_website_route_field="",
	)

	def autoname(self):
		self.name = self.branch_name

	def validate(self):
		if not self.route:
			self.route = "branches/%s" % slug(self.branch_name)

	def get_context(self, context):
		context.title = "AABrick %s" % self.branch_name
		context.no_cache = 1
		context.parents = [{"name": "Branches", "route": "/branches"}]
		context.description = self.meta_description or self.intro

		# WhatsApp deep link, built only when a number is actually set
		wa = re.sub(r"\D", "", self.whatsapp or "")
		context.whatsapp_link = (
			"https://wa.me/%s?text=%s"
			% (wa, frappe.utils.quoted(
				"Hello AABrick %s, I would like to enquire about" % self.branch_name))
			if wa else None
		)

		context.tel_link = "tel:%s" % re.sub(r"[^\d+]", "", self.phone or "")
		context.schema = self.local_business_schema()
		return context

	def local_business_schema(self):
		"""LocalBusiness markup. This is what lets a branch appear in Google's
		local results rather than only the brand appearing."""
		data = {
			"@context": "https://schema.org",
			"@type": "HardwareStore",
			"name": "AABrick %s" % self.branch_name,
			"description": self.meta_description or self.intro or "",
			"url": frappe.utils.get_url(self.route),
			"telephone": self.phone or "",
			"parentOrganization": {
				"@type": "Organization",
				"name": "AABrick Zambia Limited",
				"url": frappe.utils.get_url("/"),
			},
			"address": {
				"@type": "PostalAddress",
				"streetAddress": self.street_address or "",
				"addressLocality": self.city or self.branch_name,
				"addressRegion": self.province or "",
				"addressCountry": "ZM",
			},
		}
		if self.latitude and self.longitude:
			data["geo"] = {
				"@type": "GeoCoordinates",
				"latitude": self.latitude,
				"longitude": self.longitude,
			}
		hours = []
		if self.hours_weekday and self.hours_weekday.lower() != "closed":
			hours.append(self._spec("Mo,Tu,We,Th,Fr", self.hours_weekday))
		if self.hours_saturday and self.hours_saturday.lower() != "closed":
			hours.append(self._spec("Sa", self.hours_saturday))
		if self.hours_sunday and self.hours_sunday.lower() != "closed":
			hours.append(self._spec("Su", self.hours_sunday))
		if hours:
			data["openingHoursSpecification"] = [h for h in hours if h]
		return frappe.as_json(data)

	@staticmethod
	def _spec(days, text):
		parts = re.findall(r"(\d{1,2}:\d{2})", text or "")
		if len(parts) != 2:
			return None
		return {
			"@type": "OpeningHoursSpecification",
			"dayOfWeek": days.split(","),
			"opens": parts[0],
			"closes": parts[1],
		}
