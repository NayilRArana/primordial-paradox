#!/usr/bin/env python3
"""battle_art.py: shared pixel helpers for the battle screen art (scenes, enemies, HUD atlas).

Everything is authored as indices into data/nes_palette.json (the 2C02 palette, entry numbers 00 to 3F) and written
as PNGs. Two rules are enforced by code, not by hope:
  * background: every 16x16 attribute area carries at most 3 colours besides the shared backdrop 0F (cap_cells)
  * sprite: every 8x8 tile carries at most 3 opaque colours, the black outline included (cap_tiles)
No gradients: dither is the 2 pixel checker or the 25 percent grid only (spec 13). Original art, procedural.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T = 255          # transparent (sprites only)
K = 0x0F         # the shared backdrop, black

GRY, LGR, WHT = 0x00, 0x10, 0x30
BLU, BLB, AZU, LBL, PBL = 0x02, 0x12, 0x11, 0x21, 0x31
VIO, PNK, RED, DRD, CRM = 0x03, 0x25, 0x16, 0x06, 0x05
BRN, ORG, GLD, DGO, PGD, CRE, PCR = 0x08, 0x27, 0x28, 0x18, 0x38, 0x36, 0x37
TEA, GRN, LGN = 0x0C, 0x1A, 0x2A


def _nes():
    with open(os.path.join(ROOT, "data", "nes_palette.json"), encoding="utf-8-sig") as handle:
        data = json.load(handle)
    out = []
    for value in data["colours"]:
        value = value.lstrip("#")
        out.append((int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)))
    return out


NES = _nes()
_LOOKUP = {}
for _i, _rgb in enumerate(NES):
    if _rgb != (0, 0, 0):
        _LOOKUP.setdefault(_rgb, _i)
_LOOKUP[(0, 0, 0)] = K
_PAL = np.array(NES + [(0, 0, 0)] * (256 - len(NES)), dtype=np.uint8)


def dist(i, j):
    a, b = NES[i], NES[j]
    return 3 * (a[0] - b[0]) ** 2 + 4 * (a[1] - b[1]) ** 2 + 2 * (a[2] - b[2]) ** 2


def nearest(rgb):
    best, bi = None, K
    for i, c in enumerate(NES):
        if c == (0, 0, 0) and i != K:
            continue
        d = 3 * (c[0] - rgb[0]) ** 2 + 4 * (c[1] - rgb[1]) ** 2 + 2 * (c[2] - rgb[2]) ** 2
        if best is None or d < best:
            best, bi = d, i
    return bi


class Canvas:
    def __init__(self, w, h, fill=K):
        self.w, self.h = w, h
        self.a = np.full((h, w), fill, dtype=np.uint8)

    def put(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = col

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return int(self.a[y, x])
        return T

    def rect(self, x0, y0, x1, y1, col):
        x0, y0, x1, y1 = max(int(x0), 0), max(int(y0), 0), min(int(x1), self.w - 1), min(int(y1), self.h - 1)
        if x1 >= x0 and y1 >= y0:
            self.a[y0:y1 + 1, x0:x1 + 1] = col

    def frame(self, x0, y0, x1, y1, col):
        self.rect(x0, y0, x1, y0, col)
        self.rect(x0, y1, x1, y1, col)
        self.rect(x0, y0, x0, y1, col)
        self.rect(x1, y0, x1, y1, col)

    def dither(self, x0, y0, x1, y1, col, phase=0):
        for y in range(max(y0, 0), min(y1, self.h - 1) + 1):
            for x in range(max(x0, 0), min(x1, self.w - 1) + 1):
                if (x + y + phase) % 2 == 0:
                    self.a[y, x] = col

    def dither25(self, x0, y0, x1, y1, col, phase=0):
        for y in range(max(y0, 0), min(y1, self.h - 1) + 1):
            for x in range(max(x0, 0), min(x1, self.w - 1) + 1):
                if (x + phase) % 2 == 0 and (y + phase) % 2 == 0:
                    self.a[y, x] = col

    def line(self, x0, y0, x1, y1, col, thick=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            for ox in range(thick):
                for oy in range(thick):
                    self.put(x0 + ox, y0 + oy, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, col):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1.0:
                    self.put(x, y, col)

    def poly(self, pts, col):
        pts = [(float(x), float(y)) for x, y in pts]
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                    self.put(x, y, col)

    def blit(self, arr, x, y):
        h, w = arr.shape
        for j in range(h):
            for i in range(w):
                v = int(arr[j, i])
                if v != T:
                    self.put(x + i, y + j, v)


def to_image(a):
    rgb = _PAL[a]
    alpha = np.where(a == T, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def from_image(img):
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    out = np.full((h, w), T, dtype=np.uint8)
    cache = {}
    for y in range(h):
        for x in range(w):
            r, g, b, al = (int(v) for v in arr[y, x])
            if al < 128:
                continue
            key = (r, g, b)
            if key not in cache:
                cache[key] = _LOOKUP[key] if key in _LOOKUP else nearest(key)
            out[y, x] = cache[key]
    return out


def cap_cells(a, cell=16, limit=3, protect=(), backdrop=K):
    """Keep at most `limit` colours besides the backdrop in every attribute area; remap the rest to the nearest kept."""
    out = a.copy()
    fixed = 0
    h, w = out.shape
    for y0 in range(0, h, cell):
        for x0 in range(0, w, cell):
            blk = out[y0:y0 + cell, x0:x0 + cell]
            cols, counts = np.unique(blk, return_counts=True)
            pairs = [(int(c), int(n)) for c, n in zip(cols, counts) if int(c) not in (backdrop, T)]
            if len(pairs) <= limit:
                continue
            pairs.sort(key=lambda p: (p[0] in protect, p[1]), reverse=True)
            keep = [p[0] for p in pairs[:limit]] + [backdrop]
            for c, n in pairs[limit:]:
                near = min(keep, key=lambda k: dist(c, k))
                blk[blk == c] = near
                fixed += n
    return out, fixed


def cap_tiles(a, tile=8, limit=3, outline_col=K):
    """Sprite rule: at most `limit` opaque colours per 8x8 tile, the outline colour included."""
    out = a.copy()
    fixed = 0
    h, w = out.shape
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            blk = out[y0:y0 + tile, x0:x0 + tile]
            cols, counts = np.unique(blk, return_counts=True)
            pairs = [(int(c), int(n)) for c, n in zip(cols, counts) if int(c) != T]
            if len(pairs) <= limit:
                continue
            has_out = any(c == outline_col for c, _ in pairs)
            rest = sorted([p for p in pairs if p[0] != outline_col], key=lambda p: p[1], reverse=True)
            room = limit - (1 if has_out else 0)
            keep = ([outline_col] if has_out else []) + [p[0] for p in rest[:room]]
            for c, n in rest[room:]:
                near = min(keep, key=lambda k: dist(c, k))
                blk[blk == c] = near
                fixed += n
    return out, fixed


def audit_cells(a, cell=16, backdrop=K):
    bad, worst = [], 0
    h, w = a.shape
    for y0 in range(0, h, cell):
        for x0 in range(0, w, cell):
            s = set(np.unique(a[y0:y0 + cell, x0:x0 + cell]).tolist()) - {backdrop, T}
            worst = max(worst, len(s))
            if len(s) > 3:
                bad.append((x0, y0, sorted(s)))
    return worst, bad


def audit_tiles(a, tile=8, limit=3):
    bad = []
    h, w = a.shape
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            s = set(np.unique(a[y0:y0 + tile, x0:x0 + tile]).tolist()) - {T}
            if len(s) > limit:
                bad.append((x0, y0, sorted(s)))
    return bad


def colours_used(a):
    return sorted(set(np.unique(a).tolist()) - {T})


def outline(a, col=K):
    """1 pixel outline around every opaque pixel, on transparent pixels only (spec 13 line and shape)."""
    op = a != T
    grown = np.zeros_like(op)
    grown[1:, :] |= op[:-1, :]
    grown[:-1, :] |= op[1:, :]
    grown[:, 1:] |= op[:, :-1]
    grown[:, :-1] |= op[:, 1:]
    out = a.copy()
    out[(~op) & grown] = col
    return out


QUAY_TILE_NAMES = (
    "roof_ridge_a roof_eave_a roof_ridge_b roof_eave_b chimney_a chimney_b wall wall_boards "
    "pilaster window_lit window_dark door sign_board awning gable_clock ticket_window "
    "finial band_stripe open_ground paving paving_alt paving_drain tree_canopy_a tree_canopy_b "
    "tree_canopy_c fence_rail fence_post plaza_centrepiece water_mid water_deep water_foam coping "
    "quay_wall_face pier_plank_light pier_plank_dark bollard step_light step_mid step_dark pier_rail "
    "lamp_head lamp_pole bench market_counter crate barrel container_blue container_green "
    "tarp_pile hull deck_plank cabin mast funnel bow gangway "
    "crane_mast crane_jib crane_hook crane_base lighthouse_gall"
).split()


def load_quay_tiles():
    path = os.path.join(ROOT, "game", "sprites_src", "env", "quay", "quay_v2_tiles.png")
    arr = from_image(Image.open(path))
    cols = arr.shape[1] // 16
    tiles = {}
    for i, name in enumerate(QUAY_TILE_NAMES):
        x, y = (i % cols) * 16, (i // cols) * 16
        tiles[name] = arr[y:y + 16, x:x + 16].copy()
    return tiles
