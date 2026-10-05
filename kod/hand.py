"""
hand.py — The hand that draws.

The drawings of the nephron are not ruled: every line wanders a little, the outline is
found in two passes that do not quite agree, and graphite does not cover the paper evenly.

A browser can do all of that with a filter laid over a finished drawing, and until 2026-10
it did. But a filter is worked out again for every frame in which anything under it
changes, and in Safari that made the figures stutter under the pointer. So the unevenness
is put into the drawing itself, here, once:

- `Hand` moves a point by a smooth field that depends only on where the point is. Two
  lines through the same place are moved alike, so joints stay closed and a lumen stays
  inside its wall; a second hand, with a field of its own, gives the looser pass.
- `tooth()` is a small tile of specks in the colour of the paper. Laid over a line it lets
  the paper show through, the way the tooth of a sheet does.

Everything here is geometry and one tile; nothing is left for the browser to compute.
"""
import base64
import binascii
import math
import random
import re
import struct
import zlib
from functools import lru_cache


# ============================================================
#  A smooth field
# ============================================================
def _lattice(ix, iy, seed):
    """A fixed number between -1 and 1 for a point of the grid."""
    n = (ix * 374761393 + iy * 668265263 + seed * 362437) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFF) / 32767.5 - 1.0


def _smooth(x, y, seed):
    """Between the points of the grid the field is blended, without creases."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    top = _lattice(ix, iy, seed) + (_lattice(ix + 1, iy, seed) - _lattice(ix, iy, seed)) * fx
    low = _lattice(ix, iy + 1, seed) + (_lattice(ix + 1, iy + 1, seed) - _lattice(ix, iy + 1, seed)) * fx
    return top + (low - top) * fy


# ============================================================
#  A path as points
# ============================================================
_TOKEN = re.compile(r"[MLCAZ]|[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?", re.IGNORECASE)


def _arc(start, rx, ry, large, sweep, end, step):
    """Points along an elliptical arc (axes along x and y), the end included."""
    (x0, y0), (x1, y1) = start, end
    dx, dy = (x0 - x1) / 2, (y0 - y1) / 2
    stretch = dx * dx / (rx * rx) + dy * dy / (ry * ry)
    if stretch > 1:                                # too small to reach: grown until it does
        rx, ry = rx * math.sqrt(stretch), ry * math.sqrt(stretch)
    over = rx * rx * dy * dy + ry * ry * dx * dx
    k = math.sqrt(max((rx * rx * ry * ry - over) / over, 0.0)) if over else 0.0
    if bool(large) == bool(sweep):
        k = -k
    cxp, cyp = k * rx * dy / ry, -k * ry * dx / rx
    cx, cy = cxp + (x0 + x1) / 2, cyp + (y0 + y1) / 2
    a0 = math.atan2((dy - cyp) / ry, (dx - cxp) / rx)
    a1 = math.atan2((-dy - cyp) / ry, (-dx - cxp) / rx)
    turn = a1 - a0
    if sweep and turn < 0:
        turn += 2 * math.pi
    elif not sweep and turn > 0:
        turn -= 2 * math.pi
    n = max(2, round(abs(turn) * max(rx, ry) / step))
    return [(cx + rx * math.cos(a0 + turn * i / n), cy + ry * math.sin(a0 + turn * i / n))
            for i in range(1, n + 1)]


def along(d, step=6.0, straight=None):
    """Points along a path, about `step` apart, and whether it is closed. A straight piece
    needs fewer points than a bend: `straight` is the distance between them there (twice
    `step` if not given).

    Understands what the drawings here are made of: one stroke per path, in absolute
    M, L, C and A commands (A with its axes along x and y), and Z."""
    straight = straight or 2 * step
    tokens = _TOKEN.findall(d)
    points, closed, i = [], False, 0

    def take(n):
        nonlocal i
        values = [float(t) for t in tokens[i:i + n]]
        i += n
        return values

    while i < len(tokens):
        command = tokens[i].upper()
        i += 1
        if command == "M":
            points.append(tuple(take(2)))
        elif command == "L":
            (x0, y0), (x, y) = points[-1], take(2)
            n = max(1, round(math.hypot(x - x0, y - y0) / straight))
            points += [(x0 + (x - x0) * k / n, y0 + (y - y0) * k / n) for k in range(1, n + 1)]
        elif command == "C":
            (x0, y0), (x1, y1, x2, y2, x, y) = points[-1], take(6)
            length = (math.hypot(x1 - x0, y1 - y0) + math.hypot(x2 - x1, y2 - y1)
                      + math.hypot(x - x2, y - y2) + math.hypot(x - x0, y - y0)) / 2
            n = max(2, round(length / step))
            for k in range(1, n + 1):
                t = k / n
                a, b, c, e = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
                points.append((a * x0 + b * x1 + c * x2 + e * x, a * y0 + b * y1 + c * y2 + e * y))
        elif command == "A":
            rx, ry, _, large, sweep, x, y = take(7)
            points += _arc(points[-1], rx, ry, large, sweep, (x, y), step)
        elif command == "Z":
            closed = True
        else:
            raise ValueError(f"not a path this hand can follow: {d!r}")
    return points, closed


def through(points, closed=False, before=None, after=None):
    """A smooth path through the points (Catmull-Rom, written as cubic Beziers).

    `before` and `after` are the points the line comes from and goes on to: they are not
    drawn, they only set the direction at its two ends. Two lines that are given each
    other's neighbouring points meet without a corner. Without them a line keeps, at each
    end, the direction it had."""
    pts = [(round(x, 1), round(y, 1)) for x, y in points]
    if closed:
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        ring = [pts[-1]] + pts + pts[:2]
    else:
        ahead = before or (2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])
        beyond = after or (2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])
        ring = [ahead] + pts + [beyond]
    last = len(pts) if closed else len(pts) - 1
    d = [f"M{pts[0][0]:g},{pts[0][1]:g}"]
    for i in range(1, last + 1):
        p0, p1, p2, p3 = ring[i - 1], ring[i], ring[i + 1], ring[i + 2]
        d.append(f"C{p1[0] + (p2[0] - p0[0]) / 6:.1f},{p1[1] + (p2[1] - p0[1]) / 6:.1f} "
                 f"{p2[0] - (p3[0] - p1[0]) / 6:.1f},{p2[1] - (p3[1] - p1[1]) / 6:.1f} "
                 f"{p2[0]:g},{p2[1]:g}")
    return " ".join(d) + ("Z" if closed else "")


# ============================================================
#  The hand
# ============================================================
class Hand:
    """A way of not drawing straight.

    reach:      how far (in the units of the drawing) a point may be moved;
    wavelength: the distance over which the hand drifts from one side to the other.
    """

    def __init__(self, seed, wavelength, reach):
        self.seed, self.wavelength, self.reach = seed, wavelength, reach

    def at(self, x, y):
        """Where the hand puts the point (x, y)."""
        u, v, s = x / self.wavelength, y / self.wavelength, self.seed
        dx = _smooth(u, v, s) + 0.5 * _smooth(2 * u, 2 * v, s + 1)
        dy = _smooth(u, v, s + 2) + 0.5 * _smooth(2 * u, 2 * v, s + 3)
        return x + self.reach * dx / 1.5, y + self.reach * dy / 1.5

    @lru_cache(maxsize=None)
    def path(self, d, step=6.0, straight=None):
        """The path `d` as this hand draws it."""
        points, closed = along(d, step, straight)
        return through([self.at(x, y) for x, y in points], closed)

    def chain(self, paths, step=6.0):
        """Paths that follow one another (each starts where the one before it ends), as this
        hand draws them: one line, in pieces that meet without a corner."""
        samples = [along(d, step)[0] for d in paths]
        drawn = []
        for i, points in enumerate(samples):
            before = self.at(*samples[i - 1][-2]) if i else None
            after = self.at(*samples[i + 1][1]) if i < len(samples) - 1 else None
            drawn.append(through([self.at(x, y) for x, y in points], before=before, after=after))
        return drawn

    def line(self, x1, y1, x2, y2, step=12.0):
        return self.path(f"M{x1:g},{y1:g} L{x2:g},{y2:g}", step, step)

    def circle(self, cx, cy, r):
        """A circle, which a hand does not quite close into a circle."""
        n = max(8, round(2 * math.pi * r / 6))
        points = [self.at(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
                  for i in range(n)]
        return through(points, closed=True)


# The firm pass and the looser one under it. (As the filters they replace: the firm line
# drifts by about a unit over some fifty, the loose one by a little more over thirty.)
FIRM = Hand(seed=4, wavelength=46, reach=1.5)
LOOSE = Hand(seed=23, wavelength=31, reach=2.0)


# ============================================================
#  The tooth of the paper
# ============================================================
def _png(size, colour, alphas):
    """A square picture of one colour whose opacity varies: `alphas` is one number (0-15)
    per pixel, row by row. An indexed PNG with sixteen levels of opacity."""
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", binascii.crc32(body) & 0xFFFFFFFF)

    rgb = bytes(int(colour[i:i + 2], 16) for i in (1, 3, 5))
    rows = b"".join(b"\x00" + bytes(alphas[y * size:(y + 1) * size]) for y in range(size))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 3, 0, 0, 0))
            + chunk(b"PLTE", rgb * 16)
            + chunk(b"tRNS", bytes(round(255 * level / 15) for level in range(16)))
            + chunk(b"IDAT", zlib.compress(rows, 9))
            + chunk(b"IEND", b""))


@lru_cache(maxsize=None)
def tooth(colour, name="nd-tooth", units=36, pixels=84, cover=0.5, cell=2, seed=9):
    """A pattern (to go in <defs>) of specks in `colour`, the colour of the paper. A line
    stroked with it, over a pencil line, lets the paper show through unevenly.

    units:  the size of the tile in the units of the drawing;
    pixels: its size as a picture (about one pixel of the screen per pixel of the tile);
    cover:  how strongly the specks cover (0 to 1): the weight of the tooth;
    cell:   the size of the grain, in pixels of the tile (`pixels` must be a multiple of it).
            A fine grain greys a line evenly; a coarse one breaks it up, as charcoal does.
    """
    rng = random.Random(seed)
    n = pixels // cell
    coarse = [[rng.random() for _ in range(n)] for _ in range(n)]
    alphas = []
    for y in range(pixels):
        gy = y / cell
        y0, fy = int(gy) % n, gy - int(gy)
        fy = fy * fy * (3 - 2 * fy)
        for x in range(pixels):
            gx = x / cell
            x0, fx = int(gx) % n, gx - int(gx)
            fx = fx * fx * (3 - 2 * fx)
            x1, y1 = (x0 + 1) % n, (y0 + 1) % n
            top = coarse[y0][x0] + (coarse[y0][x1] - coarse[y0][x0]) * fx
            low = coarse[y1][x0] + (coarse[y1][x1] - coarse[y1][x0]) * fx
            # grain at two scales: the cell (blended, and stretched back to its full range)
            # and the single pixel
            blended = min(max(0.5 + (top + (low - top) * fy - 0.5) * 1.35, 0.0), 1.0)
            grain = 0.6 * blended + 0.4 * rng.random()
            alphas.append(min(15, max(0, round(15 * cover * (grain - 0.36) / 0.64))))
    data = base64.b64encode(_png(pixels, colour, alphas)).decode("ascii")
    return (f"<pattern id='{name}' width='{units}' height='{units}' patternUnits='userSpaceOnUse'>"
            f"<image href='data:image/png;base64,{data}' width='{units}' height='{units}' "
            f"preserveAspectRatio='none'/></pattern>")
