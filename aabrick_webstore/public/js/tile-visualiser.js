// Lay an AABrick tile on the floor of a photographed room.
//
// There is no AI here and there does not need to be. A room is photographed
// once, somebody traces the floor once, and from then on the browser draws
// the tile onto that floor with a ground plane projection. It runs offline,
// costs nothing per view, and answers instantly on a phone on a Zambian
// mobile network, which a model behind an upload does not.
//
// The projection is the ordinary pinhole one. For a camera at height H with
// the horizon on image row Yh, a floor pixel (x, y) is
//
//     depth   = focal * H / (y - Yh)
//     lateral = (x - cx) * H / (y - Yh)
//
// in metres. Those two numbers index the tile, so a 600mm tile covers 600mm
// of floor wherever it lands and shrinks with distance on its own. Four
// numbers per room, each meaning something a person can reason about, which
// beats dragging the corners of a quad about until it looks right.
//
// What sells it is not the geometry though, it is the light. The new tile is
// multiplied by the brightness of the floor it replaces, so the shadows, the
// window reflections and the dark line under a sofa all come through onto
// the new tile. That is also the one demand this makes of a photograph: the
// floor being replaced has to be plain and evenly lit, because whatever is
// on it comes through.

(function () {
	"use strict";

	var MAX_W = 1100;        // a room is drawn no wider than this
	var GROUT_MM = 2;        // the line between tiles
	var SOFT_PX = 8;         // below this, a tile is too small to draw honestly
	var HIGHLIGHT = 0.75;   // how hard a reflection is put back onto the tile

	var scenes = [];
	var tiles = [];

	var scene = null;        // the room on screen
	var tile = null;         // the tile on the floor
	var turned = false;      // laid on the diagonal
	var grout = true;

	var canvas, ctx, out;
	var base = null;         // the room, untouched
	var mask = null;         // 1 where the floor is
	var shade = null;        // the floor brightness, as a multiplier
	var U = null, V = null;  // metres across and into the room, per pixel
	var PX = null;           // pixels per metre, per pixel
	var texCache = {};

	function $(sel, root) { return (root || document).querySelector(sel); }

	function el(tag, cls, text) {
		var e = document.createElement(tag);
		if (cls) { e.className = cls; }
		if (text !== undefined) { e.textContent = text; }
		return e;
	}

	// ---- the room -------------------------------------------------------

	function inside(poly, x, y) {
		var n = poly.length, hit = false, i, j;
		for (i = 0, j = n - 1; i < n; j = i++) {
			var xi = poly[i][0], yi = poly[i][1];
			var xj = poly[j][0], yj = poly[j][1];
			if ((yi > y) !== (yj > y)
				&& x < (xj - xi) * (y - yi) / (yj - yi) + xi) {
				hit = !hit;
			}
		}
		return hit;
	}

	function prepare(s, img, done) {
		var w = Math.min(MAX_W, img.naturalWidth);
		var k = w / img.naturalWidth;
		var h = Math.round(img.naturalHeight * k);

		canvas.width = w;
		canvas.height = h;
		ctx.drawImage(img, 0, 0, w, h);
		base = ctx.getImageData(0, 0, w, h);
		out = ctx.createImageData(w, h);
		out.data.set(base.data);

		var n = w * h;
		mask = new Uint8Array(n);
		shade = new Float32Array(n);
		U = new Float32Array(n);
		V = new Float32Array(n);
		PX = new Float32Array(n);

		var poly = s.floor.map(function (p) { return [p[0] * k, p[1] * k]; });
		// A room is calibrated by eye, so the three numbers that decide how
		// the tile sits can be pushed in from the address bar while that is
		// being done: ?horizon=300&height=2.2&focal=900. Nothing reads them
		// in normal use.
		var q = new URLSearchParams(location.search);
		var num = function (name, fallback) {
			var v = parseFloat(q.get(name));
			return isNaN(v) ? fallback : v;
		};
		var yh = num("horizon", s.horizon) * k;
		var cx = num("cx", s.cx === undefined ? img.naturalWidth / 2 : s.cx) * k;
		var focal = num("focal", s.focal || img.naturalWidth) * k;
		var camH = num("height", s.height || 1.45);

		var lum = new Float32Array(n);
		var sum = 0, count = 0;
		var d = base.data;
		var x, y, i;

		for (y = 0; y < h; y++) {
			for (x = 0; x < w; x++) {
				i = y * w + x;
				var dy = y - yh;
				if (dy <= 2 || !inside(poly, x, y)) { continue; }
				mask[i] = 1;
				var p = i * 4;
				var L = (0.299 * d[p] + 0.587 * d[p + 1] + 0.114 * d[p + 2]) / 255;
				lum[i] = L;
				sum += L;
				count++;
				V[i] = focal * camH / dy;
				U[i] = (x - cx) * camH / dy;
				// A metre of floor at this depth covers about this many
				// pixels, which is what says when a tile has become too
				// small to draw honestly.
				PX[i] = dy * dy / (focal * camH);
			}
		}

		var ref = count ? sum / count : 0.6;
		for (i = 0; i < n; i++) {
			if (!mask[i]) { continue; }
			var f = lum[i] / ref;
			shade[i] = f < 0.25 ? 0.25 : (f > 1.7 ? 1.7 : f);
		}

		done();
	}

	// ---- the tile -------------------------------------------------------

	function texture(t, done) {
		if (texCache[t.code]) { return done(texCache[t.code]); }
		var img = new Image();
		img.onload = function () {
			var side = 512;
			var c = document.createElement("canvas");
			c.width = side;
			c.height = side;
			var cc = c.getContext("2d");
			cc.drawImage(img, 0, 0, side, side);
			var data = cc.getImageData(0, 0, side, side);
			// The average is what a tile fades to once it is too far away to
			// resolve, which is what stops the back of the room boiling.
			var r = 0, g = 0, b = 0, i;
			for (i = 0; i < data.data.length; i += 4) {
				r += data.data[i];
				g += data.data[i + 1];
				b += data.data[i + 2];
			}
			var px = data.data.length / 4;
			var tex = {
				side: side,
				data: data.data,
				avg: [r / px, g / px, b / px]
			};
			texCache[t.code] = tex;
			done(tex);
		};
		img.onerror = function () { done(null); };
		img.src = t.image;
	}

	// ---- drawing --------------------------------------------------------

	function draw() {
		if (!base || !tile) { return; }
		texture(tile, function (tex) {
			if (!tex) { return; }
			var w = canvas.width, h = canvas.height;
			var src = base.data, dst = out.data, td = tex.data;
			var side = tex.side;
			var S = tile.w / 1000;          // tile size in metres
			var Sv = tile.h / 1000;
			var gu = grout ? (GROUT_MM / 1000) / S : 0;
			var gv = grout ? (GROUT_MM / 1000) / Sv : 0;
			var ca = turned ? Math.SQRT1_2 : 1;
			var sa = turned ? Math.SQRT1_2 : 0;
			var avg = tex.avg;
			var i, n = w * h;

			dst.set(src);

			for (i = 0; i < n; i++) {
				if (!mask[i]) { continue; }
				var u = U[i], v = V[i];
				if (turned) {
					var ur = u * ca - v * sa;
					v = u * sa + v * ca;
					u = ur;
				}
				var fu = u / S, fv = v / Sv;
				fu = fu - Math.floor(fu);
				fv = fv - Math.floor(fv);

				var tp = (((fv * side) | 0) * side + ((fu * side) | 0)) * 4;
				var r = td[tp], g = td[tp + 1], b = td[tp + 2];

				// Far enough away and a tile is smaller than a pixel, so it
				// is drawn as its own average rather than as noise.
				var px = S * PX[i];
				if (px < SOFT_PX) {
					var m = px / SOFT_PX;
					if (m < 0) { m = 0; }
					r = r * m + avg[0] * (1 - m);
					g = g * m + avg[1] * (1 - m);
					b = b * m + avg[2] * (1 - m);
				} else if (gu && (fu < gu || fv < gv)) {
					r *= 0.82; g *= 0.82; b *= 0.82;
				}

				// Darker than the floor average is a shadow, and multiplying
				// is right for it. Brighter is a reflection, and multiplying
				// is useless for it: a black tile times anything is still
				// black, so a polished black floor came out as a hole in the
				// picture with every window reflection gone. Highlights are
				// screened towards white instead, which is the one way to put
				// light back onto a dark tile.
				var f = shade[i];
				if (f > 1) {
					var t = (f - 1) * HIGHLIGHT;
					if (t > 1) { t = 1; }
					r = r + (255 - r) * t;
					g = g + (255 - g) * t;
					b = b + (255 - b) * t;
				} else {
					r *= f; g *= f; b *= f;
				}
				var p = i * 4;
				dst[p] = r > 255 ? 255 : r;
				dst[p + 1] = g > 255 ? 255 : g;
				dst[p + 2] = b > 255 ? 255 : b;
				dst[p + 3] = 255;
			}

			ctx.putImageData(out, 0, 0);
		});
	}

	// ---- the page -------------------------------------------------------

	function loadScene(s) {
		scene = s;
		var wrap = $(".aab-vis-stage");
		if (wrap) { wrap.classList.add("is-loading"); }
		var img = new Image();
		img.onload = function () {
			prepare(s, img, function () {
				if (wrap) { wrap.classList.remove("is-loading"); }
				draw();
			});
		};
		img.src = s.image;
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-room"),
			function (b) {
				b.classList.toggle("is-on", b.getAttribute("data-room") === s.id);
			});
	}

	function loadTile(t) {
		tile = t;
		draw();
		var link = $(".aab-vis-product");
		if (link) {
			link.href = t.route;
			link.textContent = "View " + t.name;
		}
		var cap = $(".aab-vis-caption");
		if (cap) {
			cap.textContent = t.name + "  " + t.w + "x" + t.h + "mm"
				+ (t.price ? "  ZK " + Number(t.price).toFixed(2) : "");
		}
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-swatch"),
			function (b) {
				b.classList.toggle("is-on", b.getAttribute("data-code") === t.code);
			});
	}

	function build() {
		var rooms = $(".aab-vis-rooms");
		scenes.forEach(function (s) {
			var b = el("button", "aab-vis-room", s.label);
			b.type = "button";
			b.setAttribute("data-room", s.id);
			b.addEventListener("click", function () { loadScene(s); });
			rooms.appendChild(b);
		});

		var strip = $(".aab-vis-swatches");
		tiles.forEach(function (t) {
			var b = el("button", "aab-vis-swatch");
			b.type = "button";
			b.title = t.name + " " + t.w + "x" + t.h;
			b.setAttribute("data-code", t.code);
			var im = document.createElement("img");
			im.src = t.image;
			im.alt = t.name;
			im.loading = "lazy";
			b.appendChild(im);
			b.appendChild(el("span", null, t.code));
			b.addEventListener("click", function () { loadTile(t); });
			strip.appendChild(b);
		});

		var turn = $(".aab-vis-turn");
		if (turn) {
			turn.addEventListener("click", function () {
				turned = !turned;
				turn.classList.toggle("is-on", turned);
				draw();
			});
		}
		var gr = $(".aab-vis-grout");
		if (gr) {
			gr.classList.toggle("is-on", grout);
			gr.addEventListener("click", function () {
				grout = !grout;
				gr.classList.toggle("is-on", grout);
				draw();
			});
		}
	}

	function start() {
		var host = $("#aab-visualiser");
		if (!host) { return; }
		try {
			scenes = JSON.parse($("#aab-vis-scenes").textContent);
			tiles = JSON.parse($("#aab-vis-tiles").textContent);
		} catch (e) {
			return;
		}
		if (!scenes.length || !tiles.length) { return; }

		canvas = $(".aab-vis-canvas");
		ctx = canvas.getContext("2d", { willReadFrequently: true });

		build();
		loadTile(tiles[0]);
		loadScene(scenes[0]);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start);
	} else {
		start();
	}
})();
