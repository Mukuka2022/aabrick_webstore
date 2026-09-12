// A cart that does not ask who you are.
//
// Webshop's cart is a Quotation attached to a Customer, built from the
// signed in user, so adding to it demanded a login. Until somebody commits
// to an order there is no reason to know who they are, and the worst of it
// was the calculator: measure a floor, choose a tile, learn you need
// sixteen boxes, and get thrown to a login form that loses all of it.
//
// So a guest basket lives in this browser. Every button on the site and the
// calculator all call webshop.webshop.shopping_cart.update_cart, and our
// scripts load after webshop's bundle, so wrapping that one function covers
// the whole site without touching a single template.
//
// The basket holds item codes and quantities and nothing else. Every price
// on the page is worked out by the server.

(function () {
	"use strict";

	var KEY = "aab_guest_cart";
	var MAX_LINES = 40;

	function isGuest() {
		// Anything other than a known, named, non-Guest user counts as a
		// guest. An undefined user is the session not being filled in yet,
		// and reading that as "signed in" hands the basket to a server cart
		// the visitor may not touch.
		var user = window.frappe && frappe.session && frappe.session.user;
		return !user || user === "Guest";
	}

	function read() {
		try {
			var raw = localStorage.getItem(KEY);
			if (!raw) {
				return {};
			}
			var obj = JSON.parse(raw);
			return (obj && typeof obj === "object" && !Array.isArray(obj)) ? obj : {};
		} catch (e) {
			// A private window, or storage turned off. The cart is simply not
			// kept, which is better than the page failing.
			return {};
		}
	}

	function write(obj) {
		try {
			localStorage.setItem(KEY, JSON.stringify(obj));
		} catch (e) {
			return;
		}
	}

	function count(obj) {
		var c = 0;
		obj = obj || read();
		for (var k in obj) {
			if (Object.prototype.hasOwnProperty.call(obj, k)) {
				c += Number(obj[k]) || 0;
			}
		}
		return c;
	}

	var cart = {
		isGuest: isGuest,
		items: read,
		count: function () { return count(); },
		qty: function (code) { return Number(read()[code]) || 0; },

		// Webshop treats qty as the quantity the line should end up at, not
		// as an amount to add, and the calculator depends on that: asking for
		// sixteen boxes twice still means sixteen.
		set: function (code, qty) {
			var obj = read();
			qty = Math.max(0, Math.min(999, Math.floor(Number(qty) || 0)));
			if (!qty) {
				delete obj[code];
			} else {
				if (!obj[code] && Object.keys(obj).length >= MAX_LINES) {
					return false;
				}
				obj[code] = qty;
			}
			write(obj);
			paintCount();
			return true;
		},

		clear: function () {
			try {
				localStorage.removeItem(KEY);
			} catch (e) {
				return;
			}
			paintCount();
		}
	};

	window.aabCart = cart;

	// ---------------------------------------------------------------- badge
	function paintCount() {
		var n = isGuest() ? count() : null;
		var holder = document.querySelector(".aab-nav-cart");
		if (!holder || n === null) {
			return;
		}
		var tag = holder.querySelector(".aab-cart-count");
		if (!n) {
			if (tag) {
				tag.parentNode.removeChild(tag);
			}
			return;
		}
		if (!tag) {
			tag = document.createElement("span");
			tag.className = "aab-cart-count";
			holder.appendChild(tag);
		}
		tag.textContent = String(n);
	}

	// ------------------------------------------------------- the one wrapper
	function shoppingCart() {
		return window.webshop && webshop.webshop && webshop.webshop.shopping_cart;
	}

	function wrap() {
		var sc = shoppingCart();
		if (!sc || sc.aabWrapped) {
			return !!sc;
		}
		var original = sc.update_cart;

		sc.update_cart = function (opts) {
			if (!isGuest()) {
				return original.call(this, opts);
			}
			opts = opts || {};
			var ok = cart.set(opts.item_code, opts.qty);
			if (!ok && window.frappe && frappe.msgprint) {
				frappe.msgprint("That is as many different items as one basket holds. "
					+ "Send this list to a branch and start another.");
			}
			// Our buttons read r.message to decide whether to flip to
			// "view in cart", so answer in the shape they expect.
			if (typeof opts.callback === "function") {
				opts.callback({ message: { name: "guest-basket" } });
			}
			return;
		};

		sc.aabWrapped = true;
		return true;
	}

	// ------------------------------------------- handing it over at sign in
	//
	// Once they are known, the basket becomes a real cart and stops being
	// kept here. One item at a time, in series, because each call writes the
	// same Quotation and firing them together makes them fight.
	function handOver(done) {
		var obj = read();
		var codes = Object.keys(obj);
		if (!codes.length) {
			return done && done(false);
		}
		var sc = shoppingCart();
		if (!sc || !sc.update_cart) {
			return done && done(false);
		}

		var i = 0;
		function next() {
			if (i >= codes.length) {
				cart.clear();
				return done && done(true);
			}
			var code = codes[i];
			i += 1;
			sc.update_cart({
				item_code: code,
				qty: obj[code],
				callback: next
			});
		}
		next();
	}

	window.aabCart.handOver = handOver;

	function start() {
		wrap();
		paintCount();
		if (!isGuest() && count()) {
			handOver(function (moved) {
				if (moved && location.pathname.split("/")[1] === "cart") {
					location.reload();
				}
			});
		}
	}

	// webshop's bundle is above ours, but frappe.ready is what tells us the
	// page is actually assembled.
	if (window.frappe && frappe.ready) {
		frappe.ready(start);
	}
	document.addEventListener("DOMContentLoaded", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
