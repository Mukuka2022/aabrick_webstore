// Sending the basket to a branch.
//
// The basket is in this browser, so the enquiry form cannot know about it
// unless it is told. Arriving at /contact?basket=1, the list is written
// into the message the customer is about to send: what they chose, how many,
// and what it comes to. They can edit every word of it before it goes.
//
// Nothing is sent anywhere until they press the button themselves.

(function () {
	"use strict";

	function wanted() {
		return location.pathname.split("/")[1] === "contact"
			&& location.search.indexOf("basket=1") !== -1;
	}

	function fill(data) {
		var box = document.getElementById("fMessage");
		if (!box) {
			return;
		}

		var lines = ["Please quote me for:", ""];
		data.items.forEach(function (item) {
			var line = "- " + item.qty + " x " + item.name;
			if (item.amount_display) {
				line += "  (" + item.amount_display + ")";
			}
			lines.push(line);
		});
		if (data.total_display) {
			lines.push("");
			lines.push("Total on the website: " + data.total_display);
		}
		lines.push("");

		// Anything they have already typed is theirs and stays.
		var typed = (box.value || "").trim();
		box.value = lines.join("\n") + (typed ? "\n" + typed : "");

		var note = document.createElement("p");
		note.className = "aab-enquiry-msg aab-basket-note";
		note.textContent = "Your basket has been written into the message below."
			+ " Edit it however you like before sending.";
		box.parentNode.insertBefore(note, box);

		box.scrollIntoView({ block: "center" });
	}

	function start() {
		if (!wanted() || !window.aabCart || !window.aabCart.isGuest()) {
			return;
		}
		var basket = window.aabCart.items();
		if (!Object.keys(basket).length) {
			return;
		}
		frappe.call({
			method: "aabrick_webstore.guest_cart.summary",
			args: { items: JSON.stringify(basket) },
			callback: function (r) {
				if (r && r.message && r.message.items && r.message.items.length) {
					fill(r.message);
				}
			}
		});
	}

	if (window.frappe && frappe.ready) {
		frappe.ready(start);
	} else {
		document.addEventListener("DOMContentLoaded", start);
	}
})();
