/* Paint calculator.
 *
 * Pure ASCII: served without a charset, so anything above 127 arrives as
 * mojibake. Non-ascii characters are escaped.
 *
 * Two things here are easy to get wrong and are worth saying out loud.
 *
 * Wall area is the perimeter times the height, not the floor area. A 5m by 4m
 * room has 20 square metres of floor and 54 of wall at 3m, and treating one as
 * the other is the mistake that sends somebody home with a third of the paint.
 *
 * Tins round up per job, not per coat. Two coats needing 11 litres is one 20
 * litre tin, not two of anything, and rounding at the wrong moment turns a
 * sensible answer into an expensive one.
 */
(function () {
	"use strict";

	var surfaces = [];
	var coats = 2;
	var mode = "lw";
	var what = "walls";

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

	function round2(n) {
		return Math.round(n * 100) / 100;
	}

	/* ------------------------------------------------------------- the room */
	function roomRow(l, w, h, removable) {
		var row = document.createElement("div");
		// Two fields in area mode, three when measuring a room, and the grid
		// is told which it is getting.
		row.className = mode === "m2" ? "aab-room" : "aab-room is-walls";

		if (mode === "m2") {
			row.innerHTML =
				'<label class="aab-field"><span>Wall area (m\u00B2)</span>' +
				'<input type="number" class="room-m2" min="0" step="0.01" inputmode="decimal" value="' + l + '"></label>' +
				'<label class="aab-field"><span>Floor area (m\u00B2)</span>' +
				'<input type="number" class="room-floor" min="0" step="0.01" inputmode="decimal" value="' + w + '"></label>' +
				'<button type="button" class="aab-room-drop" aria-label="Remove this room">&times;</button>';
		} else {
			row.innerHTML =
				'<label class="aab-field"><span>Length (m)</span>' +
				'<input type="number" class="room-l" min="0" step="0.01" inputmode="decimal" value="' + l + '"></label>' +
				'<label class="aab-field"><span>Width (m)</span>' +
				'<input type="number" class="room-w" min="0" step="0.01" inputmode="decimal" value="' + w + '"></label>' +
				'<label class="aab-field"><span>Height (m)</span>' +
				'<input type="number" class="room-h" min="0" step="0.01" inputmode="decimal" value="' + h + '"></label>' +
				'<button type="button" class="aab-room-drop" aria-label="Remove this room">&times;</button>';
		}

		if (!removable) {
			row.querySelector(".aab-room-drop").style.visibility = "hidden";
		}
		return row;
	}

	function addRoom() {
		var rooms = $("rooms");
		var more = rooms.children.length > 0;
		rooms.appendChild(mode === "m2"
			? roomRow("", "", "", more)
			: roomRow("", "", 3, more));
		calculate();
	}

	function setMode(next) {
		if (next === mode) {
			return;
		}
		var carried = areas();
		mode = next;
		var rooms = $("rooms");
		rooms.innerHTML = "";
		if (mode === "m2") {
			rooms.appendChild(roomRow(
				carried.wall ? round2(carried.wall) : "",
				carried.floor ? round2(carried.floor) : "", "", false));
		} else {
			rooms.appendChild(roomRow(5, 4, 3, false));
		}
		calculate();
	}

	/* Wall and floor are carried separately all the way through: the ceiling is
	 * the floor, and it is only painted when asked for. */
	function areas() {
		var wall = 0;
		var floor = 0;
		var rows = document.querySelectorAll("#rooms .aab-room");
		for (var i = 0; i < rows.length; i++) {
			var direct = rows[i].querySelector(".room-m2");
			if (direct) {
				wall += parseFloat(direct.value) || 0;
				var f = rows[i].querySelector(".room-floor");
				floor += f ? (parseFloat(f.value) || 0) : 0;
				continue;
			}
			var l = parseFloat(rows[i].querySelector(".room-l").value) || 0;
			var w = parseFloat(rows[i].querySelector(".room-w").value) || 0;
			var h = parseFloat(rows[i].querySelector(".room-h").value) || 0;
			// Perimeter times height. Not the floor area, which is the mistake
			// this page exists to stop somebody making.
			wall += 2 * (l + w) * h;
			floor += l * w;
		}
		return { wall: wall, floor: floor };
	}

	/* ------------------------------------------------------------- the sums */
	function calculate() {
		var a = areas();

		var doors = parseFloat($("doors").value) || 0;
		var windows = parseFloat($("windows").value) || 0;
		var doorM2 = parseFloat($("doorM2").value) || 0;
		var windowM2 = parseFloat($("windowM2").value) || 0;
		var off = doors * doorM2 + windows * windowM2;
		// Openings come off the walls, and cannot take the walls below nothing.
		if (off > a.wall) {
			off = a.wall;
		}

		var ceiling = what === "both" ? a.floor : 0;
		var net = (a.wall - off) + ceiling;

		var cover = parseFloat($("cover").value) || 0;
		var litres = cover > 0 ? (net * coats) / cover : 0;

		var tin = parseFloat($("tinPick").value) || 0;
		// Rounded once, over the whole job. Rounding per coat would buy a tin
		// nobody needs.
		var tins = tin > 0 && litres > 0 ? Math.ceil(litres / tin) : 0;
		var price = parseFloat($("price").value);

		$("wall").textContent = num(a.wall, 2) + " m\u00B2";
		$("openings").textContent = off > 0 ? "\u2212 " + num(off, 2) + " m\u00B2" : "\u2014";
		$("ceiling").textContent = ceiling > 0 ? "+ " + num(ceiling, 2) + " m\u00B2" : "\u2014";
		$("net").textContent = num(net, 2) + " m\u00B2";
		$("coatsOut").textContent = coats;
		$("litres").textContent = litres > 0 ? num(litres, 1) : "0";
		$("tins").textContent = tins > 0
			? tins + " \u00D7 " + (tin % 1 === 0 ? tin : num(tin, 1)) + "L"
				+ " (" + num(tins * tin, 0) + "L)"
			: "\u2014";
		$("cost").textContent = (price > 0 && tins > 0) ? money(tins * price) : "\u2014";

		var ask = $("askQuote");
		if (ask) {
			var q = [];
			if (litres > 0) {
				q.push("qty=" + encodeURIComponent(num(litres, 1) + " litres of paint"
					+ (tins > 0 ? ", about " + tins + " x " + tin + "L" : "")));
			}
			if (net > 0) {
				q.push("area=" + encodeURIComponent(num(net, 2) + " m\u00B2 to paint"));
			}
			ask.setAttribute("href", "/contact" + (q.length ? "?" + q.join("&") : ""));
		}
	}

	/* ---------------------------------------------------------- the surface */
	function chooseSurface(value) {
		if (value === "custom") {
			return;
		}
		var s = surfaces[parseInt(value, 10)];
		if (!s) {
			return;
		}
		$("cover").value = s.cover;
		var note = $("surfaceNote");
		if (note && s.note) {
			note.textContent = s.note;
		}
		calculate();
	}

	function markCustom() {
		var sel = $("surfacePick");
		var c = parseFloat($("cover").value) || 0;
		for (var i = 0; i < surfaces.length; i++) {
			if (surfaces[i].cover === c) {
				sel.value = String(i);
				chooseSurface(String(i));
				return;
			}
		}
		sel.value = "custom";
		var note = $("surfaceNote");
		if (note) {
			note.textContent = "Whatever the tin says it covers, for one coat.";
		}
		calculate();
	}

	function chips(selector, attr, onPick) {
		var all = document.querySelectorAll(selector + " .aab-chip");
		for (var i = 0; i < all.length; i++) {
			all[i].addEventListener("click", function (e) {
				for (var n = 0; n < all.length; n++) {
					all[n].classList.remove("is-on");
				}
				e.target.classList.add("is-on");
				onPick(e.target.getAttribute(attr));
			});
		}
	}

	/* ----------------------------------------------------------------- wire */
	function start() {
		var form = $("aab-calc");
		if (!form || form.__aabBound) {
			return;
		}
		form.__aabBound = true;

		surfaces = window.AAB_SURFACES || [];

		$("rooms").appendChild(roomRow(5, 4, 3, false));

		$("addRoom").addEventListener("click", addRoom);
		$("rooms").addEventListener("input", calculate);
		$("rooms").addEventListener("click", function (e) {
			if (e.target.classList.contains("aab-room-drop")) {
				e.target.closest(".aab-room").remove();
				calculate();
			}
		});

		$("surfacePick").addEventListener("change", function (e) {
			chooseSurface(e.target.value);
		});
		$("cover").addEventListener("input", markCustom);

		var live = ["doors", "windows", "doorM2", "windowM2", "price"];
		for (var i = 0; i < live.length; i++) {
			$(live[i]).addEventListener("input", calculate);
		}
		$("tinPick").addEventListener("change", calculate);

		chips(".aab-modes", "data-mode", setMode);
		chips(".aab-coats", "data-coats", function (v) {
			coats = parseFloat(v) || 1;
			calculate();
		});
		chips(".aab-surfaces-what", "data-what", function (v) {
			what = v;
			var label = $("ceilingLabel");
			if (label) {
				label.textContent = v === "both" ? "Ceiling" : "Ceiling (not painted)";
			}
			calculate();
		});

		chooseSurface($("surfacePick").value);
		calculate();
	}

	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
