/* PVC ceiling calculator.
 *
 * Pure ASCII: served without a charset, so anything above 127 arrives as
 * mojibake. Non-ascii characters are escaped.
 *
 * The old page rounded up to whole boards and then charged the raw area times
 * a price per square metre, so it quoted less than the boards it told you to
 * buy. Here the cost is the boards multiplied by the price of a board, which
 * is what the counter will actually ring up.
 */
(function () {
	"use strict";

	var boards = [];
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

	function round2(n) {
		return Math.round(n * 100) / 100;
	}

	/* ---------------------------------------------------------------- area */
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

		var bw = parseFloat($("boardW").value) || 0;
		var bl = parseFloat($("boardL").value) || 0;
		var price = parseFloat($("price").value) || 0;

		var cover = (bw / 1000) * bl;
		var count = cover > 0 ? Math.ceil(withWaste / cover) : 0;

		$("area").textContent = num(area, 2) + " m\u00B2";
		$("areaPlus").textContent = num(withWaste, 2) + " m\u00B2";
		$("boardCover").textContent = cover > 0 ? num(cover, 2) + " m\u00B2" : "\u2014";
		$("totalCover").textContent = num(count * cover, 2) + " m\u00B2";
		$("boards").textContent = count;
		// Whole boards times the price of a board. The old page charged the raw
		// area instead, which quoted less than the boards it asked you to buy.
		$("cost").textContent = price > 0 && count > 0 ? money(count * price) : "\u2014";
	}

	/* --------------------------------------------------------- board sizes */
	function choose(value) {
		if (value === "custom") {
			return;
		}
		var b = boards[parseInt(value, 10)];
		if (!b) {
			return;
		}
		$("boardW").value = b.w;
		$("boardL").value = b.l;
		$("price").value = b.price;
		calculate();
	}

	function markCustom() {
		var sel = $("boardPick");
		var w = parseFloat($("boardW").value) || 0;
		var l = parseFloat($("boardL").value) || 0;
		for (var i = 0; i < boards.length; i++) {
			if (boards[i].w === w && boards[i].l === l) {
				sel.value = String(i);
				calculate();
				return;
			}
		}
		sel.value = "custom";
		calculate();
	}

	/* ---------------------------------------------------------------- wire */
	function start() {
		var form = $("aab-calc");
		if (!form || form.__aabBound) {
			return;
		}
		form.__aabBound = true;

		boards = window.AAB_BOARDS || [];

		$("rooms").appendChild(roomRow(5, 4, false));

		$("addRoom").addEventListener("click", addRoom);
		$("rooms").addEventListener("input", calculate);
		$("rooms").addEventListener("click", function (e) {
			if (e.target.classList.contains("aab-room-drop")) {
				e.target.closest(".aab-room").remove();
				calculate();
			}
		});

		$("boardPick").addEventListener("change", function (e) {
			choose(e.target.value);
		});

		var manual = ["boardW", "boardL"];
		for (var j = 0; j < manual.length; j++) {
			$(manual[j]).addEventListener("input", markCustom);
		}
		$("price").addEventListener("input", calculate);

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

		choose($("boardPick").value);
		calculate();
	}

	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
