"""Context for the how-much-to-buy guide. The text lives in index.html."""

from aabrick_webstore.guide_common import build

no_cache = 1
sitemap = 1


def get_context(context):
	return build(context, "how-much-to-buy")
