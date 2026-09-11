"""Context for our login page.

The page is Frappe's. This exists only because a www template is paired
with the .py file sitting next to it, and ours sits in this app rather
than in frappe, so the context would otherwise be empty.

Every decision about authentication stays where it is. This delegates and
adds nothing: the form, the rate limiting, the OAuth providers, the email
link and the LDAP branch are all Frappe's, and our template wraps that
markup rather than replacing it.
"""

from frappe.www.login import get_context as frappe_login_context

no_cache = True


def get_context(context):
	return frappe_login_context(context)
