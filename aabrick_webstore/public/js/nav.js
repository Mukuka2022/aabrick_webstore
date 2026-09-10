/* Navbar behaviour.
 *
 * Pure ASCII: served without a charset.
 *
 * Panels open on click rather than on hover. Hover menus are unusable on a
 * touch screen and awkward for anyone using a keyboard, and this menu has to
 * work on a phone in a branch as much as on a desktop.
 */
(function () {
	"use strict";

	function closeAll(except) {
		var open = document.querySelectorAll(".aab-nav-has-panel.is-open");
		for (var i = 0; i < open.length; i++) {
			if (open[i] !== except) {
				open[i].classList.remove("is-open");
				var b = open[i].querySelector(".aab-nav-link");
				if (b) {
					b.setAttribute("aria-expanded", "false");
				}
			}
		}
	}

	function start() {
		var nav = document.getElementById("aab-nav");
		if (!nav || nav.__aabBound) {
			return;
		}
		nav.__aabBound = true;

		var toggle = document.getElementById("aab-nav-toggle");
		var menu = document.getElementById("aab-nav-menu");

		if (toggle && menu) {
			toggle.addEventListener("click", function () {
				var open = nav.classList.toggle("is-menu-open");
				toggle.setAttribute("aria-expanded", open ? "true" : "false");
				if (!open) {
					closeAll(null);
				}
			});
		}

		var holders = nav.querySelectorAll(".aab-nav-has-panel");
		for (var i = 0; i < holders.length; i++) {
			(function (holder) {
				var btn = holder.querySelector(".aab-nav-link");
				if (!btn) {
					return;
				}
				btn.addEventListener("click", function (e) {
					e.preventDefault();
					var willOpen = !holder.classList.contains("is-open");
					closeAll(holder);
					holder.classList.toggle("is-open", willOpen);
					btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
				});
			})(holders[i]);
		}

		document.addEventListener("click", function (e) {
			if (!nav.contains(e.target)) {
				closeAll(null);
			}
		});

		document.addEventListener("keydown", function (e) {
			if (e.key === "Escape") {
				closeAll(null);
				nav.classList.remove("is-menu-open");
				if (toggle) {
					toggle.setAttribute("aria-expanded", "false");
				}
			}
		});

		// A shadow once the page has moved, so the bar separates from whatever
		// is scrolling under it.
		function onScroll() {
			nav.classList.toggle("is-stuck", window.scrollY > 4);
		}
		window.addEventListener("scroll", onScroll, { passive: true });
		onScroll();
	}

	document.addEventListener("DOMContentLoaded", start);
	window.addEventListener("load", start);
	if (document.readyState !== "loading") {
		start();
	}
})();
