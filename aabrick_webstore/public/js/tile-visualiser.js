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
	var GROUT_MM = 1;        // the line between tiles
	var GROUT_DARK = 0.82;  // how dark a joint is, at full strength
	var GROUT_FAINT = 0.5;  // ...and at its faintest, when sub pixel
	var SOFT_PX = 8;         // below this, a tile is too small to draw honestly
	var HIGHLIGHT = 0.75;   // how hard a reflection is put back onto the tile

	var scenes = [];
	var tiles = [];

	var scene = null;        // the room on screen
	var tile = null;         // the tile on the floor
	var wallTile = null;     // the tile on the walls, null to leave them bare
	var target = "floor";    // which surface the next swatch is picked for
	var turned = false;      // laid on the diagonal
	var grout = true;

	var canvas, ctx, out;
	var base = null;         // the room, untouched
	var mask = null;         // 1 where there is a surface to tile
	var plane = null;        // 0 floor, 1 wall
	var shade = null;        // the floor brightness, as a multiplier
	// On the floor, metres across and into the room. On a wall, metres along
	// it and up it. Two meanings, but the same two numbers: they index the
	// tile, and the drawing loop never has to know which surface it is on.
	var U = null, V = null;
	var PX = null;           // pixels per metre, per pixel
	var texCache = {};
	var SHOW_MASK = /[?&]mask=1/.test(location.search);
	var groups = [];

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
		plane = new Uint8Array(n);
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

		// ---- the walls --------------------------------------------------
		//
		// A wall needs no camera of its own. It stands on the floor, so the
		// line the floor trace already found is the skirting, and the depth
		// of the wall in any column is the depth of the floor directly below
		// it. From that one number both wall coordinates follow: height is
		// how far the pixel sits above the skirting, converted at that
		// depth, and distance along the wall is the world length of the
		// skirting walked from the left edge. A corner needs no special
		// case, because walking the skirting turns the corner on its own.
		//
		// A wall is given as spans rather than as an outline, because a wall
		// has a window punched through it and a mirror hung on it, and an
		// outline has no way to say "not here".
		var wsum = 0, wcount = 0;
		var walls = s.walls;
		if (walls && walls.cols && walls.cols.length) {
			// the skirting, per drawn column
			var yTop = new Int32Array(w);
			for (x = 0; x < w; x++) {
				yTop[x] = -1;
				for (y = 0; y < h; y++) {
					if (mask[y * w + x]) { yTop[x] = y; break; }
				}
			}

			// how far along the wall each column is, in metres
			var along = new Float32Array(w);
			var pu = 0, pv = 0, has = false, acc = 0;
			for (x = 0; x < w; x++) {
				along[x] = acc;
				var dyt = yTop[x] - yh;
				if (yTop[x] < 0 || dyt <= 2) { has = false; continue; }
				var cv = focal * camH / dyt;
				var cu = (x - cx) * camH / dyt;
				if (has) {
					var du = cu - pu, dv = cv - pv;
					var stp = Math.sqrt(du * du + dv * dv);
					// A traced skirting wobbles by a pixel or two, and at the
					// back of the room a pixel is a long way, so an unchecked
					// walk accumulates noise as length and the tiles narrow
					// towards the horizon. A real corner is still gradual in
					// the picture, so this ceiling costs nothing and the
					// wobble has nowhere to go.
					acc += stp > 0.05 ? 0.05 : stp;
				}
				pu = cu; pv = cv; has = true;
				along[x] = acc;
			}

			var kw = w / walls.size[0];
			var wstep = walls.step;
			walls.cols.forEach(function (col) {
				var xa = Math.round(col[0] * kw);
				var xb = Math.round((col[0] + wstep) * kw);
				if (xb > w) { xb = w; }
				var sp, xx, yy, j;
				for (xx = xa; xx < xb; xx++) {
					if (xx < 0) { continue; }
					var yt = yTop[xx];
					if (yt < 0 || yt - yh <= 2) { continue; }
					var depth = focal * camH / (yt - yh);
					var ppm = focal / depth;   // pixels per metre up there
					for (sp = 1; sp + 1 < col.length; sp += 2) {
						var ya = Math.round(col[sp] * kw);
						var yb2 = Math.round(col[sp + 1] * kw);
						if (yb2 >= yt) { yb2 = yt - 1; }
						for (yy = ya; yy <= yb2; yy++) {
							if (yy < 0) { continue; }
							j = yy * w + xx;
							if (mask[j]) { continue; }
							mask[j] = 1;
							plane[j] = 1;
							U[j] = along[xx];
							V[j] = (yt - yy) / ppm;
							PX[j] = ppm;
							var q = j * 4;
							var WL = (0.299 * d[q] + 0.587 * d[q + 1]
								+ 0.114 * d[q + 2]) / 255;
							lum[j] = WL;
							wsum += WL;
							wcount++;
						}
					}
				}
			});
		}

		// Each surface is shaded against its own average. The walls catch
		// far more light than the floor in every one of these rooms, so one
		// shared average would have put the floor's shadow onto them.
		var ref = count ? sum / count : 0.6;
		var wref = wcount ? wsum / wcount : ref;
		for (i = 0; i < n; i++) {
			if (!mask[i]) { continue; }
			var f = lum[i] / (plane[i] ? wref : ref);
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

	function withTex(t, done) {
		if (!t) { return done(null); }
		texture(t, done);
	}

	function draw() {
		if (!base) { return; }
		withTex(tile, function (ftex) {
			withTex(wallTile, function (wtex) {
				paint(ftex, wtex);
			});
		});
	}

	function paint(ftex, wtex) {
		var w = canvas.width, h = canvas.height;
		var src = base.data, dst = out.data;
		var gm = GROUT_MM / 1000;   // grout, in metres
		var ca = turned ? Math.SQRT1_2 : 1;
		var sa = turned ? Math.SQRT1_2 : 0;
		// One entry per surface, floor first, so the loop only has to pick.
		// A surface with no texture is one the customer left bare.
		var TEX = [ftex, wtex];
		var TW = [tile ? tile.w / 1000 : 0, wallTile ? wallTile.w / 1000 : 0];
		var TH = [tile ? tile.h / 1000 : 0, wallTile ? wallTile.h / 1000 : 0];
		var i, n = w * h;

		dst.set(src);

		for (i = 0; i < n; i++) {
			if (!mask[i]) { continue; }
			var pl = plane[i];
			var tex = TEX[pl];
			if (!tex) { continue; }
			var td = tex.data, side = tex.side, avg = tex.avg;
			var S = TW[pl], Sv = TH[pl];

			var u = U[i], v = V[i];
			// The diagonal is a floor lay. A wall tile turned forty five
			// degrees is a different decision, and not one that was asked for.
			if (turned && !pl) {
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
			} else if (grout) {
				// A 1mm joint on a 600mm tile is a quarter of a pixel at
				// the size these rooms are drawn, so it cannot be drawn
				// narrow: nothing is thinner than a pixel. It is drawn a
				// pixel wide and paid for in strength instead, so it
				// reads as the hairline it is rather than as a grid
				// pencilled over the floor. Where the tile is close
				// enough for the joint to cover a pixel honestly, full
				// strength returns.
				var ppm = PX[i];
				var gpx = gm * ppm;
				var band = gpx > 1 ? gpx : 1;
				var g2 = band / ppm;
				if (fu < g2 / S || fv < g2 / Sv) {
					var k = gpx / band;
					if (k < GROUT_FAINT) { k = GROUT_FAINT; }
					var d2 = 1 - (1 - GROUT_DARK) * k;
					r *= d2; g *= d2; b *= d2;
				}
			}

			// Darker than the surface average is a shadow, and multiplying
			// is right for it. Brighter is a reflection, and multiplying
			// is useless for it: a black tile times anything is still
			// black, so a polished black floor came out as a hole in the
			// picture with every window reflection gone. Highlights are
			// screened towards white instead, which is the one way to put
			// light back onto a dark tile.
			if (SHOW_MASK) {
				// Tracing by eye is guesswork until you can see what you
				// traced. ?mask=1 paints the floor red and the walls blue.
				var q = i * 4;
				dst[q] = pl ? 40 : 230;
				dst[q + 1] = 40;
				dst[q + 2] = pl ? 230 : 40;
				dst[q + 3] = 255;
				continue;
			}
			var f = shade[i];
			if (f > 1) {
				var hi = (f - 1) * HIGHLIGHT;
				if (hi > 1) { hi = 1; }
				r = r + (255 - r) * hi;
				g = g + (255 - g) * hi;
				b = b + (255 - b) * hi;
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
	}

	// ---- the page -------------------------------------------------------

	function wallsFor(s, done) {
		if (s.walls !== undefined || !s.wallsUrl) { return done(); }
		fetch(s.wallsUrl)
			.then(function (r) { return r.ok ? r.json() : null; })
			.then(function (j) { s.walls = j; done(); })
			.catch(function () { s.walls = null; done(); });
	}

	function loadScene(s) {
		scene = s;
		// Three of the rooms were photographed with their walls painted for
		// tracing; the rest were not, and offering Walls there would be a
		// button that does nothing.
		var hasWalls = !!(s.wallsUrl || (s.walls && s.walls.cols));
		var wb = $('.aab-vis-face[data-face="wall"]');
		if (wb) {
			wb.disabled = !hasWalls;
			wb.title = hasWalls ? "Tile the walls"
				: "The walls of this room are not traced yet";
		}
		if (!hasWalls && target === "wall") { faceTo("floor"); }
		var wrap = $(".aab-vis-stage");
		if (wrap) { wrap.classList.add("is-loading"); }
		var img = new Image();
		img.onload = function () {
			// The wall spans are a file of their own, so a room that has
			// them waits for both. A fetch that fails leaves the room with
			// its floor, which is what it had before any of this.
			wallsFor(s, function () {
				prepare(s, img, function () {
					if (wrap) { wrap.classList.remove("is-loading"); }
					draw();
				});
			});
		};
		img.src = s.image;
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-room"),
			function (b) {
				b.classList.toggle("is-on", b.getAttribute("data-room") === s.id);
			});
	}

	// One picker, two surfaces. A second grid of 228 tiles alongside the
	// first would be a wall of pictures nobody can read, so the grid stays
	// as it is and the Floor and Walls buttons say which surface the next
	// swatch is for. Each surface keeps its own choice, which is the point:
	// almost nobody puts the same tile on both.
	function loadTile(t) {
		if (target === "wall") { wallTile = t; } else { tile = t; }
		draw();
		showPick();
	}

	function showPick() {
		var onWall = target === "wall";
		var t = onWall ? wallTile : tile;

		var link = $(".aab-vis-product");
		if (link) {
			link.hidden = !t;
			if (t) {
				link.href = t.route;
				link.textContent = "View " + t.name;
			}
		}
		var cap = $(".aab-vis-caption");
		if (cap) {
			cap.textContent = !t
				? "Walls left as they are"
				: (onWall ? "Walls: " : "Floor: ") + t.name
					+ (t.wall ? "  wall tile" : "")
					+ "  " + t.w + "x" + t.h + "mm"
					+ (t.price ? "  ZK " + Number(t.price).toFixed(2) : "");
		}
		var code = t ? t.code : "";
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-swatch"),
			function (b) {
				b.classList.toggle("is-on",
					b.getAttribute("data-code") === code);
			});
		var bare = $(".aab-vis-bare");
		if (bare) {
			bare.hidden = !onWall;
			bare.classList.toggle("is-on", onWall && !t);
		}
	}

	function faceTo(name) {
		target = name;
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-face"),
			function (b) {
				b.classList.toggle("is-on",
					b.getAttribute("data-face") === name);
			});
		showPick();
	}

	function build() {
		// A room is a photograph, so it is picked as one. A row of words
		// made people miss that there was a choice at all.
		var rooms = $(".aab-vis-rooms");
		scenes.forEach(function (s) {
			var b = el("button", "aab-vis-room");
			b.type = "button";
			b.title = s.label;
			b.setAttribute("data-room", s.id);
			var im = document.createElement("img");
			im.src = s.image;
			im.alt = s.label;
			im.loading = "lazy";
			b.appendChild(im);
			b.appendChild(el("span", null, s.label));
			b.addEventListener("click", function () { loadScene(s); });
			rooms.appendChild(b);
		});

		/* The picker holds 228 tiles across seven ranges. One grid of 228
		 * is a wall of pictures nobody can navigate, so each range gets a
		 * heading and its own grid, and both grades of a range sit under the
		 * one heading because they are the same tile. */
		function swatch(t) {
			var b = el("button", "aab-vis-swatch");
			b.type = "button";
			b.title = t.name + " " + t.w + "x" + t.h
				+ (t.grade ? " (B grade)" : "")
				+ (t.wall ? " - a wall tile, not rated for floors" : "");
			b.setAttribute("data-code", t.code);
			var im = document.createElement("img");
			// The small one, and only when it scrolls into view.
			im.loading = "lazy";
			im.src = t.thumb || t.image;
			im.alt = t.name;
			b.appendChild(im);
			var cap = el("span", null, t.code);
			if (t.grade) {
				// Which grade it is has to be on the swatch now that the two
				// sit side by side, or two prices appear for one picture.
				cap.appendChild(el("em", null, "B"));
			}
			if (t.wall) {
				// This one is a warning rather than a label: the floor it is
				// about to be laid on is not what it is made for.
				cap.appendChild(el("em", "is-wall", "WALL"));
			}
			b.appendChild(cap);
			b.addEventListener("click", function () { loadTile(t); });
			return b;
		}

		var holder = $(".aab-vis-groups");
		var blocks = [];
		if (holder) {
			groups.forEach(function (g) {
				var sec = el("div", "aab-vis-group");
				var head = el("p", "aab-vis-group-head", g.label);
				head.appendChild(el("span", null, g.size));
				sec.appendChild(head);
				var grid = el("div", "aab-vis-swatches");
				g.entries.forEach(function (t) { grid.appendChild(swatch(t)); });
				sec.appendChild(grid);
				holder.appendChild(sec);
				// The title as one searchable string, lower cased once here
				// rather than on every keystroke.
				blocks.push({
					node: sec,
					title: (g.label + " " + g.size).toLowerCase()
						.replace("\u00d7", "x"),
					count: g.entries.length
				});
			});
		}

		/* The search, over the range titles. Every word typed has to appear
		 * somewhere in the title, so "matt 600" finds the matt porcelains and
		 * the order of the words does not matter. */
		var box = $(".aab-vis-search");
		var clear = $(".aab-vis-clear");
		var none = $(".aab-vis-none");
		var counter = $(".aab-vis-count");

		function filter(q) {
			var words = q.toLowerCase().replace("\u00d7", "x")
				.split(/\s+/).filter(Boolean);
			var shown = 0;
			blocks.forEach(function (b) {
				var hit = words.every(function (w) {
					return b.title.indexOf(w) !== -1;
				});
				b.node.hidden = !hit;
				if (hit) { shown += b.count; }
			});
			if (none) { none.hidden = shown > 0; }
			if (counter) { counter.textContent = shown; }
			if (clear) { clear.hidden = !q; }
		}

		/* The ranges as a list under the box, each one the search it would
		 * type for you. A dropdown rather than a row of chips: seven titles
		 * at this width wrapped to four lines and pushed the tiles down the
		 * panel, and the list is only wanted while somebody is choosing. */
		var menu = $(".aab-vis-menu");
		var options = [];
		var active = -1;

		function open() {
			if (!menu || !options.length) { return; }
			menu.hidden = false;
			box.setAttribute("aria-expanded", "true");
		}

		function close() {
			if (!menu) { return; }
			menu.hidden = true;
			box.setAttribute("aria-expanded", "false");
			box.removeAttribute("aria-activedescendant");
			active = -1;
			options.forEach(function (o) { o.node.classList.remove("is-active"); });
		}

		function mark(i) {
			options.forEach(function (o) { o.node.classList.remove("is-active"); });
			var shown = options.filter(function (o) { return !o.node.hidden; });
			if (!shown.length) { active = -1; return; }
			if (i < 0) { i = shown.length - 1; }
			if (i >= shown.length) { i = 0; }
			active = i;
			shown[i].node.classList.add("is-active");
			box.setAttribute("aria-activedescendant", shown[i].node.id);
			shown[i].node.scrollIntoView({ block: "nearest" });
		}

		function pick(q) {
			box.value = q;
			filter(q);
			close();
		}

		if (menu) {
			blocks.forEach(function (b, i) {
				var g = groups[i];
				var q = g.label + " " + g.size;
				var li = el("li", "aab-vis-option");
				li.id = "aab-vis-opt-" + i;
				li.setAttribute("role", "option");
				li.setAttribute("aria-selected", "false");
				li.appendChild(el("span", null, q));
				li.appendChild(el("em", null, String(b.count)));
				// mousedown, not click: the box blurs first and the menu
				// would be gone before a click ever landed.
				li.addEventListener("mousedown", function (e) {
					e.preventDefault();
					pick(q);
				});
				menu.appendChild(li);
				options.push({ node: li, q: q, title: b.title });
			});
		}

		function narrowMenu(q) {
			var words = q.toLowerCase().replace("\u00d7", "x")
				.split(/\s+/).filter(Boolean);
			var any = false;
			options.forEach(function (o) {
				var hit = words.every(function (w) {
					return o.title.indexOf(w) !== -1;
				});
				o.node.hidden = !hit;
				o.node.setAttribute("aria-selected", o.q === box.value ? "true" : "false");
				if (hit) { any = true; }
			});
			return any;
		}

		if (box) {
			box.addEventListener("input", function () {
				filter(box.value);
				if (narrowMenu(box.value)) { open(); } else { close(); }
				active = -1;
			});
			box.addEventListener("focus", function () {
				narrowMenu(box.value);
				open();
			});
			box.addEventListener("blur", function () { close(); });
			box.addEventListener("keydown", function (e) {
				if (e.key === "ArrowDown" || e.key === "ArrowUp") {
					e.preventDefault();
					if (menu.hidden) { narrowMenu(box.value); open(); }
					mark(active + (e.key === "ArrowDown" ? 1 : -1));
				} else if (e.key === "Enter") {
					var shown = options.filter(function (o) { return !o.node.hidden; });
					if (!menu.hidden && active >= 0 && shown[active]) {
						e.preventDefault();
						pick(shown[active].q);
					} else {
						close();
					}
				} else if (e.key === "Escape") {
					close();
				}
			});
		}
		if (clear) {
			clear.addEventListener("mousedown", function (e) {
				e.preventDefault();
				box.value = "";
				filter("");
				narrowMenu("");
				box.focus();
				open();
			});
		}

		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-face"),
			function (b) {
				b.addEventListener("click", function () {
					faceTo(b.getAttribute("data-face"));
				});
			});
		var bare = $(".aab-vis-bare");
		if (bare) {
			bare.addEventListener("click", function () {
				wallTile = null;
				draw();
				showPick();
			});
		}

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
			// Headings are optional: a page served before the grouping
			// existed still has its flat list and must still draw.
			var gjson = $("#aab-vis-groups");
			groups = gjson ? JSON.parse(gjson.textContent) : [];
			if (!groups.length && tiles.length) {
				groups = [{ label: "Tiles", size: "", entries: tiles }];
			}
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
