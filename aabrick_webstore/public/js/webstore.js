// Storefront behaviour for AABrick.
//
// 1. PRESENTATION
//    The webshop product grid is rendered in JS (webshop/public/js/product_ui/grid.js)
//    and prints item_group verbatim, which includes the internal code range that
//    staff rely on for picking, e.g. "Matt Porcelain Tiles (800X800) - 89XXX".
//    Customers do not need it; the item code is already the card title. This strips
//    only the trailing " - <range>" for display. No data is changed -- item groups
//    keep their full names in the desk and in POS.
//
// 2. LEAD TIME
//    Stock status is deliberately hidden (Webshop Settings) because anything can be
//    ordered from the manufacturer within 7 days. Say so, rather than leaving the
//    customer to guess.
//
// 3. E-COMMERCE TRACKING
//    Pushes GA4-shaped events into window.dataLayer so Tag Manager can forward them.
//    Silent no-op until a container or measurement ID is set in Web Analytics
//    Settings. Keep this file pure ASCII: it is served without an explicit charset,
//    so non-ASCII bytes render as mojibake.

(function () {
	var CATEGORY = ".product-category:not([data-aab-clean])";
	var LEAD_TIME_TEXT = "Available to order - delivered within 7 days";
	var CURRENCY = "ZMW";

	// ---------------------------------------------------------- presentation
	function tidyCategory(el) {
		var text = (el.textContent || "").trim();
		var cut = text.lastIndexOf(" - ");
		// only strip a genuine trailing suffix, never the whole label
		if (cut > 0 && cut < text.length - 3) {
			el.textContent = text.slice(0, cut);
		}
		el.setAttribute("data-aab-clean", "1");
	}

	function addLeadTime() {
		var price = document.querySelector(".product-price");
		if (!price || document.querySelector(".aab-lead-time")) {
			return;
		}
		var note = document.createElement("div");
		note.className = "aab-lead-time";
		note.textContent = LEAD_TIME_TEXT;
		note.style.cssText =
			"margin-top:.35rem;font-size:.85rem;opacity:.75;letter-spacing:.01em;";
		price.parentNode.insertBefore(note, price.nextSibling);
	}

	// ---------------------------------------------------------- tracking
	function push(payload) {
		if (!window.aabTrackEcommerce) {
			return; // tracking not configured; stay silent
		}
		window.dataLayer = window.dataLayer || [];
		window.dataLayer.push({ ecommerce: null });
		window.dataLayer.push(payload);
	}

	function toNumber(text) {
		var m = (text || "").replace(/,/g, "").match(/[\d.]+/);
		return m ? parseFloat(m[0]) : undefined;
	}

	function currentProduct() {
		var code = document.querySelector(".product-code, .product-item-code");
		var title = document.querySelector(".product-title");
		var group = document.querySelector(".product-item-group, .product-category");
		var price = document.querySelector(".product-price");
		var id = (code && code.textContent.trim()) ||
			(title && title.textContent.trim());
		if (!id) {
			return null;
		}
		return {
			item_id: id.replace(/^Item Code\s*:\s*/i, "").trim(),
			item_name: title ? title.textContent.trim() : id,
			item_category: group ? group.textContent.trim() : undefined,
			price: price ? toNumber(price.textContent) : undefined,
			currency: CURRENCY
		};
	}

	function trackViewItem() {
		if (window.__aabViewSent || !document.querySelector(".product-page")) {
			return;
		}
		var item = currentProduct();
		if (!item) {
			return;
		}
		window.__aabViewSent = true;
		push({
			event: "view_item",
			ecommerce: { currency: CURRENCY, value: item.price, items: [item] }
		});
	}

	function trackListView() {
		if (window.__aabListSent) {
			return;
		}
		var cards = document.querySelectorAll(".product-category");
		if (!cards.length) {
			return;
		}
		window.__aabListSent = true;
		push({
			event: "view_item_list",
			ecommerce: {
				item_list_name: document.title || "Products",
				items_count: cards.length
			}
		});
	}

	function trackAddToCart(e) {
		var btn = e.target.closest &&
			e.target.closest(".btn-add-to-cart, .btn-add-to-cart-list, [data-item-code]");
		if (!btn) {
			return;
		}
		var code = btn.getAttribute("data-item-code");
		var item = currentProduct() || {};
		push({
			event: "add_to_cart",
			ecommerce: {
				currency: CURRENCY,
				value: item.price,
				items: [{
					item_id: code || item.item_id,
					item_name: item.item_name || code,
					item_category: item.item_category,
					price: item.price,
					quantity: 1
				}]
			}
		});
	}

	function trackCheckout() {
		if (window.__aabCheckoutSent) {
			return;
		}
		var p = window.location.pathname;
		if (p.indexOf("/cart") !== 0 && p.indexOf("/checkout") !== 0) {
			return;
		}
		window.__aabCheckoutSent = true;
		push({ event: "begin_checkout", ecommerce: { currency: CURRENCY } });
	}

	// ---------------------------------------------------------- wiring
	function sweep() {
		document.querySelectorAll(CATEGORY).forEach(tidyCategory);
		addLeadTime();
		trackViewItem();
		trackListView();
		trackCheckout();
	}

	function observe() {
		if (window.MutationObserver && document.body && !window.__aabObserving) {
			window.__aabObserving = true;
			new MutationObserver(sweep).observe(document.body, {
				childList: true,
				subtree: true
			});
		}
		if (document.body && !window.__aabClickBound) {
			window.__aabClickBound = true;
			document.body.addEventListener("click", trackAddToCart, true);
		}
	}

	function start() {
		window.__aabStorefront = true;
		sweep();
		observe();
	}

	// Run on every hook: the product page is server-rendered but this script can
	// load before it, while the listing grid arrives later via JS. Belt and braces
	// is cheaper than a race that silently drops events.
	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
