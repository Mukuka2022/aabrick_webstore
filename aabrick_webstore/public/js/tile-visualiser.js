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

	// How many pixels of room to draw. It used to be 1100 whatever the
	// screen, which is two mistakes at once: a laptop with a 737 pixel
	// column was drawing 1100 and showing 691 of them, and a phone with a
	// 390 pixel column was doing the same work for a quarter of the use.
	// Drawn from the column it sits in instead, with a third over for the
	// enlarged view to have something to enlarge, and never below a floor
	// that keeps a small window honest.
	//
	// It used to stop at the photograph's own width as well, on the
	// reasoning that drawing more pixels than the picture holds cannot add
	// detail. That is true of the room and false of the floor: the tile and
	// its joints are not in the photograph, they are drawn here, and on a
	// retina screen a 1448 pixel canvas stretched over 2300 device pixels
	// was softening the one part of the picture we make ourselves. So the
	// room is enlarged, which costs it nothing it had, and the floor is
	// drawn at the pixels the screen actually has.
	var MIN_W = 900;         // ...and never smaller than this
	var MAX_W = 2200;        // ...nor larger, whatever the screen asks for
	var OVER = 1.3;          // the spare the enlarged view draws on
	var SHARPEN = 0.8;       // how hard the photograph is sharpened back up
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
	// How the tile is laid. "h" is the tile as it comes, "v" is the same
	// tile stood on its end, and "d" is the forty-five degree lay. Only
	// "d" turns the coordinates; "v" swaps the tile's own two
	// measurements, which is what laying it the other way round means and
	// is why a square tile has nothing to show for it.
	var lay = "h";
	var grout = true;

	var canvas, ctx, out;
	var base = null;         // the room, untouched
	var mask = null;
	var cov = null;         // 1 where there is a surface to tile
	var plane = null;        // 0 floor, 1 wall
	var rim = null;          // 1 at the blend where a span meets something
	var shade = null;        // the floor brightness, as a multiplier
	// On the floor, metres across and into the room. On a wall, metres along
	// it and up it. Two meanings, but the same two numbers: they index the
	// tile, and the drawing loop never has to know which surface it is on.
	var U = null, V = null;
	var PX = null;           // pixels per metre, per pixel
	// ...and the same across the surface rather than up it. On the
	// wall facing the camera the two are equal; on a wall running away
	// from it they are not, and a square tile is drawn two or three
	// times taller than it is wide. That is honest perspective, but it
	// means each drawn pixel covers several pixels of the tile's own
	// picture, and taking one of them makes a marble vein into a
	// streak. Measured on the kitchen: 169 pixels per metre both ways
	// on the back wall, 222 up against 76 across on the side one.
	var ACROSS = null;
	var texCache = {};
	var SHOW_MASK = /[?&]mask=1/.test(location.search);
	var SHOW_RIM = /[?&]rim=1/.test(location.search);
	var groups = [];

	function $(sel, root) { return (root || document).querySelector(sel); }

	function el(tag, cls, text) {
		var e = document.createElement(tag);
		if (cls) { e.className = cls; }
		if (text !== undefined) { e.textContent = text; }
		return e;
	}

	// ---- the room -------------------------------------------------------

	function roomWidth() {
		var stage = $(".aab-vis-stage");
		var css = stage ? stage.clientWidth : 0;
		if (!css) { css = MIN_W; }
		var want = Math.round(css * (window.devicePixelRatio || 1) * OVER);
		if (want < MIN_W) { want = MIN_W; }
		if (want > MAX_W) { want = MAX_W; }
		return want;
	}

	function prepare(s, img, done) {
		var w = roomWidth();
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
		rim = new Uint8Array(n);
		shade = new Float32Array(n);
		U = new Float32Array(n);
		V = new Float32Array(n);
		PX = new Float32Array(n);
		ACROSS = new Float32Array(n);

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

		// The outline is filled a row at a time rather than by asking of
		// every pixel "are you inside?". That question costs a walk of all
		// eighty-odd sides of the polygon, and asking it a million and a
		// half times was most of what loading a room took. A row crosses
		// the outline in a handful of places, so find those and fill
		// between them. A side counts where the row passes between its
		// ends, and a pixel is inside when an odd number of crossings lie
		// to the right of it, which is the ray test done a row at a time.
		var cuts = new Float64Array(poly.length + 1);
		var np = poly.length;
		for (y = 0; y < h; y++) {
			var dy = y - yh;
			if (dy <= 2) { continue; }
			var cn = 0, pi, pj;
			for (pi = 0, pj = np - 1; pi < np; pj = pi++) {
				var yi = poly[pi][1], yj = poly[pj][1];
				if ((yi > y) === (yj > y)) { continue; }
				cuts[cn++] = (poly[pj][0] - poly[pi][0]) * (y - yi)
					/ (yj - yi) + poly[pi][0];
			}
			if (cn < 2) { continue; }
			cuts.subarray(0, cn).sort();
			var V0 = focal * camH / dy;
			// A metre of floor at this depth covers about this many pixels
			// up the picture, which is what says when a tile has become too
			// small to draw honestly...
			var pxUp = dy * dy / (focal * camH);
			// ...and this many across it, which is a different number. A
			// metre of width at this depth covers dy / camH pixels, growing
			// with the depth and not with its square. Taking the up-the-
			// picture figure for both claimed the floor was two to six
			// times more foreshortened across than it is, which averaged
			// the tile's own pattern into mush and let the joints running
			// away from the camera widen with distance instead of narrow.
			var pxAcross = dy / camH;
			for (var ci = 0; ci + 1 < cn; ci += 2) {
				var xa = Math.ceil(cuts[ci]);
				var xb = Math.ceil(cuts[ci + 1]) - 1;
				if (xa < 0) { xa = 0; }
				if (xb > w - 1) { xb = w - 1; }
				for (x = xa; x <= xb; x++) {
					i = y * w + x;
					mask[i] = 1;
					var p = i * 4;
					var L = (0.299 * d[p] + 0.587 * d[p + 1]
						+ 0.114 * d[p + 2]) / 255;
					lum[i] = L;
					sum += L;
					count++;
					V[i] = V0;
					U[i] = (x - cx) * camH / dy;
					PX[i] = pxUp;
					ACROSS[i] = pxAcross;
				}
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
				if (yTop[x] >= 0 && yTop[x] - yh <= 2) { yTop[x] = -1; }
			}

			// Something standing on the floor can hide the skirting all the
			// way to the bottom of the frame. The toilet and the plant beside
			// it take the last dozen columns of the ensuite that way, and a
			// column with no skirting has no depth, so it was left bare and a
			// strip of the old paint showed down the edge of the picture.
			//
			// A wall does not change depth abruptly behind the thing standing
			// in front of it, so the nearest column that can still see its
			// skirting is a good enough stand-in. A continuous wall at very
			// slightly the wrong depth beats an honest gap.
			var lend = new Int32Array(w);
			var away = new Int32Array(w);
			var last = -1, gap = 0;
			for (x = 0; x < w; x++) {
				if (yTop[x] >= 0) { last = yTop[x]; gap = 0; } else { gap++; }
				lend[x] = last;
				away[x] = last < 0 ? w : gap;
			}
			last = -1; gap = 0;
			for (x = w - 1; x >= 0; x--) {
				if (yTop[x] >= 0) { last = yTop[x]; gap = 0; } else { gap++; }
				if (last >= 0 && gap < away[x]) { lend[x] = last; }
			}
			for (x = 0; x < w; x++) {
				if (yTop[x] < 0) { yTop[x] = lend[x]; }
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
					// ...and along the wall, which on a side wall is a
					// different number: it is how far the skirting walked
					// for this one pixel of picture.
					var walk = xx > 0 ? along[xx] - along[xx - 1] : 0;
					if (walk < 0) { walk = -walk; }
					var apm = walk > 1e-6 ? 1 / walk : ppm;
					if (apm > ppm) { apm = ppm; }
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
							ACROSS[j] = apm;
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

		// Every edge of a surface is a junction, and a junction carries no
		// light of its own. A wall does not stop at a line where it meets a
		// cabinet: there are three or four pixels that are part wall and
		// part cabinet, and the mask is grown over them on purpose, because
		// an uncovered ramp shows as a fringe of the old paint along the
		// join. Covering them is right. Reading them as wall is not. They
		// carry the cabinet's brightness, and shading measures every pixel
		// against its own surface's average, so against a deep red wall a
		// pale cabinet measures three or four times it. Anything above the
		// average is screened towards white rather than multiplied, which is
		// the only way to put a reflection onto a dark tile, so a pale tile
		// in that band went to pure white.
		//
		// The band is found here rather than handed over by the tracer,
		// because it is the same thing on all four sides of a surface and
		// the tracer only knows about two of them. Each pixel within a few
		// of the mask's edge is given the shading of the surface just
		// inside it. Clamping it to the average is not enough: the band then
		// sits unshaded against a wall that is in shadow, which is a paler
		// line in place of a white one.
		var band = Math.ceil(2 * k) + 1;
		for (y = 0; y < h; y++) {
			for (x = 0; x < w; x++) {
				i = y * w + x;
				if (!mask[i]) { continue; }
				var atEdge = false, k2;
				for (k2 = 1; k2 <= band && !atEdge; k2++) {
					atEdge = (y - k2 < 0 || !mask[i - k2 * w]
						|| plane[i - k2 * w] !== plane[i])
						|| (y + k2 >= h || !mask[i + k2 * w]
							|| plane[i + k2 * w] !== plane[i])
						|| (x - k2 < 0 || !mask[i - k2]
							|| plane[i - k2] !== plane[i])
						|| (x + k2 >= w || !mask[i + k2]
							|| plane[i + k2] !== plane[i]);
				}
				if (atEdge) { rim[i] = 1; }
			}
		}
		// How far the mixture runs is not fixed. Two pixels is the blend
		// against a cabinet, but where a wall meets a ceiling the ceiling
		// catches the wall's colour and fades into it over four or five,
		// and all of it passes the colour test because all of it is partly
		// the paint. So the band is followed inward for as long as it stays
		// above the wall's own average, which is the only part that can be
		// screened, and never further than six pixels.
		//
		// Above the average at all, not comfortably above it. The first
		// try asked for fifteen per cent, and the bathroom's ceiling ramp
		// read 1.45, 1.32, 1.18, 1.13 going down and then 1.07 in the row
		// the canvas scaling blends: just under the bar, still screened,
		// and still a white line two rows deep. Within six pixels of a
		// junction a reading above the surface's own average is the
		// junction far more often than it is a reflection.
		var reach = 6;
		while (reach-- > 0) {
			var edge = [];
			for (i = 0; i < n; i++) {
				if (rim[i] || !mask[i]) { continue; }
				var avg = plane[i] ? wref : ref;
				if (lum[i] <= avg) { continue; }
				if ((i >= w && rim[i - w]) || (i + w < n && rim[i + w])
					|| (i > 0 && rim[i - 1]) || (i + 1 < n && rim[i + 1])) {
					edge.push(i);
				}
			}
			if (!edge.length) { break; }
			for (var e = 0; e < edge.length; e++) { rim[edge[e]] = 1; }
		}

		for (x = 0; x < w; x++) {
			for (y = 0; y < h; y++) {
				i = y * w + x;
				if (!rim[i]) { continue; }
				// Far enough to cross a mirror or a window and find the
				// same wall on the other side. A strip of wall five pixels
				// wide, which is what is left beside the bathroom mirror,
				// is rim all the way through and has no inside of its own
				// to ask.
				var from = -1, step;
				for (step = 1; step <= 30 && from < 0; step++) {
					var side = [
						y - step >= 0 ? i - step * w : -1,
						y + step < h ? i + step * w : -1,
						x - step >= 0 ? i - step : -1,
						x + step < w ? i + step : -1
					];
					for (var si = 0; si < 4; si++) {
						var c = side[si];
						if (c >= 0 && mask[c] && !rim[c]
							&& plane[c] === plane[i]) {
							from = c;
							break;
						}
					}
				}
				if (from >= 0) {
					shade[i] = shade[from];
				} else if (shade[i] > 1) {
					// Nothing to ask at all. Then at least do not invent a
					// reflection: the surface's own average is as much as
					// a junction may claim.
					shade[i] = 1;
				}
			}
		}

		// A mask is all or nothing, so wherever its edge runs at a shallow
		// angle it lands on the pixel grid as a staircase. That is what
		// makes a tiled wall look chewed along the top where it meets the
		// ceiling: the trace is right to within a pixel, and the eye
		// follows the steps anyway.
		//
		// So the edge gets a pixel of softness. Coverage is how much of a
		// pixel's own neighbourhood is inside the mask, which is 1 well
		// inside it and somewhere between 0 and 1 along the edge, and the
		// tile is mixed with the photograph in that proportion. A straight
		// edge loses nothing it had; a stepped one stops reading as steps.
		cov = new Float32Array(n);
		for (y = 0; y < h; y++) {
			for (x = 0; x < w; x++) {
				i = y * w + x;
				if (!mask[i]) { continue; }
				var hit = 0, seen = 0;
				for (var dy = -1; dy <= 1; dy++) {
					var yy = y + dy;
					if (yy < 0 || yy >= h) { continue; }
					for (var dx = -1; dx <= 1; dx++) {
						var xx = x + dx;
						if (xx < 0 || xx >= w) { continue; }
						seen++;
						if (mask[yy * w + xx]) { hit++; }
					}
				}
				cov[i] = seen ? hit / seen : 1;
			}
		}

		// The rooms are 1448 pixels wide and were not crisp to begin with,
		// and they are drawn wider than that now, so the photograph arrives
		// soft. Sharpen it back up. Everything the room means -- the
		// outline, the shading, the junctions -- was measured above from
		// the pixels as they came, so this changes how the room looks and
		// nothing about what it is.
		sharpen(base.data, w, h, SHARPEN);

		done();
	}

	// An unsharp mask: blur a copy, then push every pixel away from the
	// blur by the amount asked for, which returns the edge that resizing
	// and JPEG between them took off. Three taps each way is the right
	// radius at this scale, and running the two directions one after the
	// other makes it six reads a pixel rather than nine.
	function sharpen(data, w, h, amount) {
		if (!(amount > 0)) { return; }
		var n = w * h;
		var mid = new Uint8ClampedArray(n * 3);
		var x, y, i, c;

		for (y = 0; y < h; y++) {
			for (x = 0; x < w; x++) {
				i = y * w + x;
				var xl = (x > 0 ? i - 1 : i) * 4;
				var xr = (x < w - 1 ? i + 1 : i) * 4;
				var pc = i * 4;
				for (c = 0; c < 3; c++) {
					mid[i * 3 + c] = (data[xl + c] + 2 * data[pc + c]
						+ data[xr + c]) / 4;
				}
			}
		}

		for (y = 0; y < h; y++) {
			for (x = 0; x < w; x++) {
				i = y * w + x;
				var yu = (y > 0 ? i - w : i) * 3;
				var yd = (y < h - 1 ? i + w : i) * 3;
				var q = i * 3, p = i * 4;
				for (c = 0; c < 3; c++) {
					var blur = (mid[yu + c] + 2 * mid[q + c]
						+ mid[yd + c]) / 4;
					// The picture's own array clamps and rounds, so an
					// overshot highlight needs no minding here.
					data[p + c] = data[p + c]
						+ (data[p + c] - blur) * amount;
				}
			}
		}
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
		var diag = lay === "d";
		var swap = lay === "v";
		var ca = diag ? Math.SQRT1_2 : 1;
		var sa = diag ? Math.SQRT1_2 : 0;
		// One entry per surface, floor first, so the loop only has to pick.
		// A surface with no texture is one the customer left bare.
		var TEX = [ftex, wtex];
		// Horizontal and vertical are a decision about the tile rather
		// than about the floor, so both surfaces take them: on a wall, u
		// runs along the wall and v up it, and swapping the pair lays a
		// 300x600 the long way along instead of the long way up. The
		// diagonal is still the floor's alone -- see the note in the loop.
		var TW = [tile ? (swap ? tile.h : tile.w) / 1000 : 0,
			wallTile ? (swap ? wallTile.h : wallTile.w) / 1000 : 0];
		var TH = [tile ? (swap ? tile.w : tile.h) / 1000 : 0,
			wallTile ? (swap ? wallTile.w : wallTile.h) / 1000 : 0];
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
			if (diag && !pl) {
				var ur = u * ca - v * sa;
				v = u * sa + v * ca;
				u = ur;
			}
			var fu = u / S, fv = v / Sv;
			fu = fu - Math.floor(fu);
			fv = fv - Math.floor(fv);

			var ui = (fu * side) | 0, vi = (fv * side) | 0;
			var tp = (vi * side + ui) * 4;
			var r = td[tp], g = td[tp + 1], b = td[tp + 2];

			// Where the surface is foreshortened, one pixel of picture
			// covers several of the tile's own, and taking one of them is
			// what turns a vein into a streak. Average them instead. The
			// wall facing the camera asks for one sample and is untouched.
			var spread = side / (S * ACROSS[i]);
			if (spread > 1.4) {
				var k2 = spread | 0;
				if (k2 > 8) { k2 = 8; }
				var rr = 0, gg = 0, bb = 0;
				for (var t2 = 0; t2 < k2; t2++) {
					var uu = ui + t2;
					if (uu >= side) { uu -= side; }
					var p3 = (vi * side + uu) * 4;
					rr += td[p3];
					gg += td[p3 + 1];
					bb += td[p3 + 2];
				}
				r = rr / k2;
				g = gg / k2;
				b = bb / k2;
			}

			// Far enough away and a tile is smaller than a pixel, so it
			// is drawn as its own average rather than as noise.
			// The tile as drawn, at its narrower of the two, because that
			// is the one that runs out first.
			var px = S * ACROSS[i];
			var pxv = Sv * PX[i];
			if (pxv < px) { px = pxv; }
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
				// Each family of joints is measured along the direction
				// it is seen in: the ones running away from the camera are
				// squeezed across the picture, the ones running across it
				// are squeezed up it. Measuring both up the picture drew
				// the first family two pixels wide at the middle of the
				// floor and six at the back of it, which is the one thing
				// a joint never does: it is the same millimetre of grout
				// all the way, and the far end of a room is where it
				// disappears.
				var pu = ACROSS[i], pv = PX[i];
				if (diag && !pl) {
					// A diagonal joint is seen partly across the picture
					// and partly up it, so neither figure is its own.
					pu = pv = Math.sqrt(pu * pv);
				}
				var gu = gm * pu, gv = gm * pv;
				var bu = gu > 1 ? gu : 1, bv = gv > 1 ? gv : 1;
				var hu = fu < (bu / pu) / S;
				var hv = fv < (bv / pv) / Sv;
				if (hu || hv) {
					var ku = gu / bu, kv = gv / bv;
					// At a corner both joints are under the pixel, and the
					// stronger of the two is the one to draw.
					var k = hu ? ku : kv;
					if (hu && hv && kv > k) { k = kv; }
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
			if (SHOW_RIM) {
				// The junction band, the same way ?mask=1 shows the mask.
				var qr = i * 4;
				dst[qr] = rim[i] ? 40 : 200;
				dst[qr + 1] = rim[i] ? 230 : 200;
				dst[qr + 2] = rim[i] ? 40 : 200;
				dst[qr + 3] = 255;
				continue;
			}
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
			var a = cov[i];
			if (a < 1) {
				r = r * a + src[p] * (1 - a);
				g = g * a + src[p + 1] * (1 - a);
				b = b * a + src[p + 2] * (1 - a);
			}
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

	function layTo(name) {
		lay = name;
		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-lay-opt"),
			function (b) {
				b.classList.toggle("is-on",
					b.getAttribute("data-lay") === name);
			});
		draw();
	}

	// A square tile laid the other way round is the same tile, so the
	// option is switched off rather than left to do nothing when somebody
	// presses it. Same handling as the walls of a room nobody has traced.
	// Vertical is worth offering when anything on screen would move for
	// it, which means either tile, not just the floor's: a square floor
	// under an oblong wall tile still has something to turn.
	function layOptions() {
		var laid = [], square = true, k;
		if (tile) { laid.push(tile); }
		if (wallTile) { laid.push(wallTile); }
		for (k = 0; k < laid.length; k++) {
			if (laid[k].w !== laid[k].h) { square = false; }
		}
		var none = laid.length === 0;
		var vb = $('.aab-vis-lay-opt[data-lay="v"]');
		if (vb) {
			vb.disabled = none || square;
			vb.title = (none || square)
				? "Every tile laid here is square, so there is nothing to turn"
				: "Lay the tile the other way round";
		}
		if ((none || square) && lay === "v") { layTo("h"); }
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
		layOptions();
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

		Array.prototype.forEach.call(
			document.querySelectorAll(".aab-vis-lay-opt"),
			function (b) {
				b.addEventListener("click", function () {
					layTo(b.getAttribute("data-lay"));
				});
			});
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

	// ---- the room, opened larger ---------------------------------------
	//
	// A picture of the canvas, taken when it opens, rather than a second
	// canvas: nothing has to be drawn twice and the browser does the
	// scaling.
	//
	// One step, about two and a bit times whatever the picture is showing
	// at, which is the same jump on a phone as on a desk. Never less than
	// the canvas's own pixels, because up to there the enlargement is free
	// and exact, and never more than twice them, because past that there
	// is nothing further in the file to show.
	var STEP = 2.2;

	function zoomWidth(fitted) {
		var w = fitted * STEP;
		if (w < canvas.width) { w = canvas.width; }
		if (w > canvas.width * 2) { w = canvas.width * 2; }
		return Math.round(w);
	}

	function zoomer() {
		var box = $(".aab-vis-zoom");
		var stage = $(".aab-vis-stage");
		var img = $(".aab-vis-zoom-img");
		var hint = $(".aab-vis-zoom-hint");
		var shut = $(".aab-vis-zoom-close");
		var scroll = $(".aab-vis-zoom-scroll");
		if (!box || !stage || !img || !scroll) { return; }

		var big = false;

		var touch = !(window.matchMedia
			&& window.matchMedia("(hover: hover) and (pointer: fine)").matches);
		var tap = touch ? "Tap" : "Click";

		function say() {
			if (!hint) { return; }
			hint.textContent = big
				? (touch ? "Drag to look around. Tap the room to stand back."
					: "Drag to look around. Click the room to stand back.")
				: tap + " the room to look closer.";
		}

		function fit() {
			big = false;
			box.classList.remove("is-big");
			img.style.width = "";
			img.style.height = "";
			say();
		}

		// Zoom about the point that was clicked, so the thing being looked
		// at stays under the finger rather than jumping to the middle.
		function closer(e) {
			var r = img.getBoundingClientRect();
			var fx = r.width ? (e.clientX - r.left) / r.width : 0.5;
			var fy = r.height ? (e.clientY - r.top) / r.height : 0.5;
			big = true;
			box.classList.add("is-big");
			img.style.width = zoomWidth(r.width) + "px";
			img.style.height = "auto";
			say();
			var sw = scroll.clientWidth, sh = scroll.clientHeight;
			scroll.scrollLeft = fx * img.offsetWidth - sw / 2;
			scroll.scrollTop = fy * img.offsetHeight - sh / 2;
		}

		function open() {
			if (!canvas.width) { return; }
			img.src = canvas.toDataURL("image/jpeg", 0.92);
			box.hidden = false;
			document.documentElement.classList.add("aab-vis-locked");
			fit();
			if (shut) { shut.focus(); }
		}

		function close() {
			box.hidden = true;
			document.documentElement.classList.remove("aab-vis-locked");
			img.removeAttribute("src");
			stage.focus();
		}

		stage.addEventListener("click", open);
		stage.addEventListener("keydown", function (e) {
			if (e.key === "Enter" || e.key === " ") {
				e.preventDefault();
				open();
			}
		});
		img.addEventListener("click", function (e) {
			e.stopPropagation();
			if (big) { fit(); } else { closer(e); }
		});
		if (shut) { shut.addEventListener("click", close); }
		// Anywhere off the picture closes it, which is what everyone tries.
		box.addEventListener("click", function (e) {
			if (e.target === box || e.target === scroll) { close(); }
		});
		document.addEventListener("keydown", function (e) {
			if (!box.hidden && e.key === "Escape") { close(); }
		});

		// Dragging to look around. Touch scrolls the container on its own,
		// so this is for a mouse.
		var from = null;
		img.addEventListener("mousedown", function (e) {
			if (!big) { return; }
			e.preventDefault();
			from = {
				x: e.clientX, y: e.clientY,
				l: scroll.scrollLeft, t: scroll.scrollTop
			};
			box.classList.add("is-dragging");
		});
		window.addEventListener("mousemove", function (e) {
			if (!from) { return; }
			scroll.scrollLeft = from.l - (e.clientX - from.x);
			scroll.scrollTop = from.t - (e.clientY - from.y);
		});
		window.addEventListener("mouseup", function (e) {
			if (!from) { return; }
			var moved = Math.abs(e.clientX - from.x) + Math.abs(e.clientY - from.y);
			from = null;
			box.classList.remove("is-dragging");
			// A drag is not a click, or looking around would stand you back.
			if (moved > 4) { e.stopPropagation(); }
		}, true);
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
		zoomer();
		loadTile(tiles[0]);
		loadScene(scenes[0]);
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start);
	} else {
		start();
	}
})();
