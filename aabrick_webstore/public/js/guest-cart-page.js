// The cart page, for somebody who has not signed in.
//
// Webshop's cart page shows a signed out visitor an empty basket, because
// as far as it is concerned they have one. The basket is in this browser,
// so the page is drawn from there, with every figure on it worked out by
// the server: the browser holds item codes and quantities and nothing else.

(function () {
	"use strict";

	function onCartPage() {
		return location.pathname.split("/")[1] === "cart";
	}

	function el(tag, cls, text) {
		var e = document.createElement(tag);
		if (cls) {
			e.className = cls;
		}
		if (text !== undefined) {
			e.textContent = text;
		}
		return e;
	}

	function render(data) {
		var host = document.querySelector(".cart-empty")
			|| document.querySelector(".cart-container")
			|| document.querySelector(".page_content");
		if (!host) {
			return;
		}

		var box = el("div", "aab-gcart");

		var head = el("div", "aab-gcart-head");
		head.appendChild(el("h2", null, "Your basket"));
		head.appendChild(el("p", "aab-gcart-note",
			"Nothing is reserved until you place the order or send it to a branch."));
		box.appendChild(head);

		var list = el("div", "aab-gcart-list");
		data.items.forEach(function (item) {
			var row = el("div", "aab-gcart-row");

			var shot = el("a", "aab-gcart-shot");
			shot.href = item.route;
			if (item.image) {
				var img = document.createElement("img");
				img.src = item.image;
				img.alt = item.name;
				img.loading = "lazy";
				shot.appendChild(img);
			}
			row.appendChild(shot);

			var body = el("div", "aab-gcart-body");
			var link = el("a", "aab-gcart-name", item.name);
			link.href = item.route;
			body.appendChild(link);
			if (item.rate_display) {
				body.appendChild(el("p", "aab-gcart-rate",
					item.rate_display + (item.uom ? " / " + item.uom : "")));
			} else {
				body.appendChild(el("p", "aab-gcart-rate", "Price on request"));
			}

			var qtyRow = el("div", "aab-gcart-qty");
			var minus = el("button", "aab-gcart-step", "\u2212");
			minus.type = "button";
			var num = el("span", "aab-gcart-num", String(item.qty));
			var plus = el("button", "aab-gcart-step", "+");
			plus.type = "button";
			var drop = el("button", "aab-gcart-remove", "Remove");
			drop.type = "button";

			minus.addEventListener("click", function () {
				window.aabCart.set(item.item_code, item.qty - 1);
				draw();
			});
			plus.addEventListener("click", function () {
				window.aabCart.set(item.item_code, item.qty + 1);
				draw();
			});
			drop.addEventListener("click", function () {
				window.aabCart.set(item.item_code, 0);
				draw();
			});

			qtyRow.appendChild(minus);
			qtyRow.appendChild(num);
			qtyRow.appendChild(plus);
			qtyRow.appendChild(drop);
			body.appendChild(qtyRow);
			row.appendChild(body);

			row.appendChild(el("div", "aab-gcart-amount",
				item.amount_display || ""));
			list.appendChild(row);
		});
		box.appendChild(list);

		var foot = el("div", "aab-gcart-foot");
		var totals = el("div", "aab-gcart-total");
		totals.appendChild(el("span", null, "Total"));
		totals.appendChild(el("strong", null, data.total_display));
		foot.appendChild(totals);
		if (!data.priced) {
			foot.appendChild(el("p", "aab-gcart-note",
				"Some items are priced at the branch, so this total is only "
				+ "part of the order."));
		}
		foot.appendChild(el("p", "aab-gcart-note",
			"Prices include VAT where it applies. Delivery is quoted by your "
			+ "branch."));

		var acts = el("div", "aab-gcart-actions");
		var order = el("a", "aab-btn aab-btn-primary", "Place this order");
		order.href = "/login?redirect-to=%2Fcart";
		// ghost, not outline: outline is white on white here, because it was
		// drawn to sit on the hero photograph.
		var send = el("a", "aab-btn aab-btn-ghost", "Send this to a branch");
		send.href = "/contact?basket=1";
		acts.appendChild(order);
		acts.appendChild(send);
		foot.appendChild(acts);
		foot.appendChild(el("p", "aab-gcart-note",
			"Placing the order yourself needs an account. Sending it to a "
			+ "branch does not: leave a name and a number and they will call "
			+ "you back."));

		box.appendChild(foot);

		var keep = el("a", "aab-gcart-keep", "Keep shopping");
		keep.href = "/all-products";
		box.appendChild(keep);

		host.innerHTML = "";
		host.className = "aab-gcart-host";
		host.appendChild(box);
	}

	function empty() {
		var host = document.querySelector(".cart-empty");
		if (!host) {
			return;
		}
		var msg = host.querySelector(".cart-empty-message");
		if (msg) {
			msg.textContent = "Your basket is empty";
		}
	}

	function draw() {
		if (!onCartPage() || !window.aabCart || !window.aabCart.isGuest()) {
			return;
		}
		var basket = window.aabCart.items();
		if (!Object.keys(basket).length) {
			return empty();
		}
		frappe.call({
			method: "aabrick_webstore.guest_cart.summary",
			args: { items: JSON.stringify(basket) },
			callback: function (r) {
				if (r && r.message && r.message.items && r.message.items.length) {
					render(r.message);
				} else {
					empty();
				}
			}
		});
	}

	if (window.frappe && frappe.ready) {
		frappe.ready(draw);
	} else {
		document.addEventListener("DOMContentLoaded", draw);
	}
})();
