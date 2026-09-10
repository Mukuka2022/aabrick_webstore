/* Tile calculator.
 *
 * Pure ASCII: this file is served without a charset, so anything else arrives
 * as mojibake.
 *
 * Boxes are worked out from the area a box covers rather than from a tile
 * count, which is the same arithmetic with one rounding step instead of two.
 * Nothing is rounded until the end, and then only upwards: you cannot buy
 * four fifths of a box.
 */
(function () {
	"use strict";

	var tiles = {};
	var picked = null;
	var waste = 10;
	var mode = "lw";

	function $(id) {
		return document.getElementById(id);
	}

	function money(n) {
		return "ZMW " + n.toLocaleString(undefined, {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		});
	}

	function num(n, dp) {
		return n.toLocaleString(undefined, {
			minimumFractionDigits: dp,
			maximumFractionDigits: dp
		});
	}

	/* ---------------------------------------------------------------- rooms */
	function roomRow(a, b, removable) {
		var row = document.createElement("div");
		row.className = mode === "m2" ? "aab-room is-area" : "aab-room";

		if (mode === "m2") {
			row.innerHTML =
				'<label class="aab-field"><span>Area (m\u00B2)</span>' +
				'<input type="number" class="room-m2" min="0" step="0.01" inputmode="decimal" value="' + a + '"></label>' +
				'<button type="button" class="aab-room-drop" aria-label="Remove this area">&times;</button>';
		} else {
			row.innerHTML =
				'<label class="aab-field"><span>Length (m)</span>' +
				'<input type="number" class="room-l" min="0" step="0.01" inputmode="decimal" value="' + a + '"></label>' +
				'<label class="aab-field"><span>Width (m)</span>' +
				'<input type="number" class="room-w" min="0" step="0.01" inputmode="decimal" value="' + b + '"></label>' +
				'<button type="button" class="aab-room-drop" aria-label="Remove this area">&times;</button>';
		}

		if (!removable) {
			row.querySelector(".aab-room-drop").style.visibility = "hidden";
		}
		return row;
	}

	function addRoom() {
		var rooms = $("rooms");
		rooms.appendChild(roomRow("", "", rooms.children.length > 0));
		calculate();
	}

	function setMode(next) {
		if (next === mode) {
			return;
		}
		// Carry the total across rather than throwing it away: someone who has
		// measured a room and then switches should see the number they had.
		var carried = totalArea();
		mode = next;

		var rooms = $("rooms");
		rooms.innerHTML = "";
		if (mode === "m2") {
			rooms.appendChild(roomRow(carried ? round2(carried) : "", "", false));
		} else {
			rooms.appendChild(roomRow(5, 4, false));
		}
		calculate();
	}

	function round2(n) {
		return Math.round(n * 100) / 100;
	}

	function totalArea() {
		var total = 0;
		var rows = document.querySelectorAll("#rooms .aab-room");
		for (var i = 0; i < rows.length; i++) {
			var direct = rows[i].querySelector(".room-m2");
			if (direct) {
				total += parseFloat(direct.value) || 0;
				continue;
			}
			var l = parseFloat(rows[i].querySelector(".room-l").value) || 0;
			var w = parseFloat(rows[i].querySelector(".room-w").value) || 0;
			total += l * w;
		}
		return total;
	}

	/* ------------------------------------------------------------ the sums */
	function calculate() {
		var area = totalArea();
		var withWaste = area * (1 + waste / 100);

		var tw = parseFloat($("tileW").value) || 0;
		var th = parseFloat($("tileH").value) || 0;
		var pcs = parseInt($("pcs").value, 10) || 0;
		var price = parseFloat($("price").value) || 0;

		var boxCover = pcs * (tw / 1000) * (th / 1000);
		var boxes = boxCover > 0 ? Math.ceil(withWaste / boxCover) : 0;

		$("area").textContent = num(area, 2) + " m\u00B2";
		$("areaPlus").textContent = num(withWaste, 2) + " m\u00B2";
		$("boxCover").textContent = boxCover > 0 ? num(boxCover, 2) + " m\u00B2" : "\u2014";
		$("boxes").textContent = boxes;
		$("tiles").textContent = boxes * pcs;
		$("cost").textContent = price > 0 && boxes > 0 ? money(boxes * price) : "\u2014";

		var btn = $("addCart");
		btn.disabled = !(picked && boxes > 0);
		btn.textContent = picked && boxes > 0
			? "Add " + boxes + (boxes === 1 ? " box" : " boxes") + " to cart"
			: "Add boxes to cart";
		btn.setAttribute("data-qty", boxes);
	}

	/* ------------------------------------------------------------ the tile */
	function choose(code) {
		picked = tiles[code] || null;
		var view = $("viewTile");

		if (!picked) {
			view.setAttribute("href", "/all-products");
			view.textContent = "Browse tiles";
			$("disclaimer").textContent =
				"An estimate. Confirm quantities with your branch before ordering, "
				+ "and buy the whole job in one go so the shade matches.";
			calculate();
			return;
		}

		$("tileW").value = picked.w;
		$("tileH").value = picked.h;
		if (picked.pcs) {
			$("pcs").value = picked.pcs;
		}
		if (picked.price) {
			$("price").value = picked.price;
		}

		view.setAttribute("href", picked.route);
		view.textContent = "View " + picked.code;

		// The fourteen items whose description disagrees with their own range
		// arrive without a piece count, so say so rather than quietly using
		// whatever was in the box last time.
		$("disclaimer").textContent = picked.pcs
			? "An estimate. Confirm quantities with your branch before ordering, "
				+ "and buy the whole job in one go so the shade matches."
			: "We do not have a confirmed piece count for " + picked.code
				+ ". Check the box, or ask your branch, before you order.";

		calculate();
	}

	/* ---------------------------------------------------------------- cart */
	function addToCart() {
		var btn = $("addCart");
		var qty = parseInt(btn.getAttribute("data-qty"), 10) || 0;
		if (!picked || qty < 1) {
			return;
		}
		btn.disabled = true;
		if (window.webshop && window.webshop.webshop && window.webshop.webshop.shopping_cart) {
			window.webshop.webshop.shopping_cart.update_cart({
				item_code: picked.code,
				qty: qty,
				callback: function (r) {
					btn.disabled = false;
					if (r.message) {
						btn.textContent = qty + (qty === 1 ? " box" : " boxes") + " in cart";
					}
				}
			});
		} else {
			window.location.href = picked.route;
		}
	}

	/* ---------------------------------------------------------------- wire */
	function start() {
		if (!$("aab-calc") || $("aab-calc").__aabBound) {
			return;
		}
		$("aab-calc").__aabBound = true;

		tiles = {};
		var list = window.AAB_TILES || [];
		for (var i = 0; i < list.length; i++) {
			tiles[list[i].code] = list[i];
		}

		$("rooms").appendChild(roomRow(5, 4, false));

		$("addRoom").addEventListener("click", addRoom);
		$("rooms").addEventListener("input", calculate);
		$("rooms").addEventListener("click", function (e) {
			if (e.target.classList.contains("aab-room-drop")) {
				e.target.closest(".aab-room").remove();
				calculate();
			}
		});

		$("tilePick").addEventListener("change", function (e) {
			choose(e.target.value);
		});

		var manual = ["tileW", "tileH", "pcs", "price"];
		for (var j = 0; j < manual.length; j++) {
			$(manual[j]).addEventListener("input", calculate);
		}

		var modes = document.querySelectorAll(".aab-modes .aab-chip");
		for (var m = 0; m < modes.length; m++) {
			modes[m].addEventListener("click", function (e) {
				for (var n = 0; n < modes.length; n++) {
					modes[n].classList.remove("is-on");
				}
				e.target.classList.add("is-on");
				setMode(e.target.getAttribute("data-mode"));
			});
		}

		var chips = document.querySelectorAll(".aab-chiprow:not(.aab-modes) .aab-chip");
		for (var k = 0; k < chips.length; k++) {
			chips[k].addEventListener("click", function (e) {
				for (var n = 0; n < chips.length; n++) {
					chips[n].classList.remove("is-on");
				}
				e.target.classList.add("is-on");
				waste = parseFloat(e.target.getAttribute("data-waste")) || 0;
				calculate();
			});
		}

		$("addCart").addEventListener("click", addToCart);

		calculate();
	}

	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
