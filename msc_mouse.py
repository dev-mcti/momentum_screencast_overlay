## msc_mouse.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.

import math, gpu
from gpu_extras.batch import batch_for_shader

_STROKE_TH = 2

# ---------- Cached shaders (perf) ----------
_SH_UNI = gpu.shader.from_builtin("UNIFORM_COLOR")

# ---------- GPU helpers ----------

def _tri_fan(points, color):
    ba = batch_for_shader(_SH_UNI, "TRI_FAN", {"pos": points})
    gpu.state.blend_set("ALPHA"); _SH_UNI.bind(); _SH_UNI.uniform_float("color", color)
    ba.draw(_SH_UNI); gpu.state.blend_set("NONE")

def _tris(points, color):
    if not points: return
    ba = batch_for_shader(_SH_UNI, "TRIS", {"pos": points})
    gpu.state.blend_set("ALPHA"); _SH_UNI.bind(); _SH_UNI.uniform_float("color", color)
    ba.draw(_SH_UNI); gpu.state.blend_set("NONE")

# ---------- Rounded rects ----------

def rounded_rect_fill(x, y, w, h, r, color, seg=14):
    r = max(0, min(r, int(min(w, h) / 2)))
    if r == 0:
        _tris([(x, y), (x+w, y), (x+w, y+h), (x, y), (x+w, y+h), (x, y+h)], color); return

    def arc(cx, cy, a0, a1):
        pts = []; a0 = math.radians(a0); a1 = math.radians(a1)
        step = (a1 - a0) / seg
        for i in range(seg + 1):
            a = a0 + step * i
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    cx_bl, cy_bl = x + r,     y + r
    cx_br, cy_br = x + w - r, y + r
    cx_tr, cy_tr = x + w - r, y + h - r
    cx_tl, cy_tl = x + r,     y + h - r

    ring  = arc(cx_br, cy_br, 270, 360)
    ring += arc(cx_tr, cy_tr, 0,   90)
    ring += arc(cx_tl, cy_tl, 90,  180)
    ring += arc(cx_bl, cy_bl, 180, 270)

    cx, cy = x + w * 0.5, y + h * 0.5
    _tri_fan([(cx, cy)] + ring + [ring[0]], color)

def rounded_rect_stroke(x, y, w, h, r, th, color, seg=22):
    th = max(1, int(th))
    r  = max(0, min(r, int(min(w, h) / 2)))
    if th >= r and r > 0:
        th = r  # keep inner radius non-negative

    def arc(cx, cy, rad, a0, a1, steps):
        pts = []; a0 = math.radians(a0); a1 = math.radians(a1)
        step = (a1 - a0) / steps
        for i in range(steps + 1):
            a = a0 + step * i
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        return pts

    cx_bl, cy_bl = x + r,     y + r
    cx_br, cy_br = x + w - r, y + r
    cx_tr, cy_tr = x + w - r, y + h - r
    cx_tl, cy_tl = x + r,     y + h - r

    cx_bl_i, cy_bl_i = x + th + (r - th), y + th + (r - th)
    cx_br_i, cy_br_i = x + w - th - (r - th), y + th + (r - th)
    cx_tr_i, cy_tr_i = x + w - th - (r - th), y + h - th - (r - th)
    cx_tl_i, cy_tl_i = x + th + (r - th), y + h - th - (r - th)

    outer = []; inner = []; steps = seg
    outer += arc(cx_br, cy_br, r,     270, 360, steps); inner += arc(cx_br_i, cy_br_i, r - th, 270, 360, steps)
    outer += arc(cx_tr, cy_tr, r,       0,  90, steps); inner += arc(cx_tr_i, cy_tr_i, r - th,   0,  90, steps)
    outer += arc(cx_tl, cy_tl, r,      90, 180, steps); inner += arc(cx_tl_i, cy_tl_i, r - th,  90, 180, steps)
    outer += arc(cx_bl, cy_bl, r,     180, 270, steps); inner += arc(cx_bl_i, cy_bl_i, r - th, 180, 270, steps)

    tris = []
    for i in range(len(outer) - 1):
        o0, o1 = outer[i], outer[i+1]
        i0, i1 = inner[i], inner[i+1]
        tris += [o0, o1, i1,  o0, i1, i0]
    _tris(tris, color)

def outline_col(s, alpha):
    steps = getattr(s, "mouse_outline_shade", 0)
    shade = max(0.0, min(1.0, int(steps) / 10.0))
    return (shade, shade, shade, alpha)

def polyline_thick(points, widths, color):
    if len(points) < 2: return
    verts = ()
    verts = []
    for i, p in enumerate(points):
        if i == 0:
            nx, ny = points[i+1][0] - p[0], points[i+1][1] - p[1]
        elif i == len(points) - 1:
            nx, ny = p[0] - points[i-1][0], p[1] - points[i-1][1]
        else:
            nx, ny = points[i+1][0] - points[i-1][0], points[i+1][1] - points[i-1][1]
        ln = max(1e-6, math.hypot(nx, ny)); nx, ny = nx / ln, ny / ln
        px, py = -ny, nx
        w = widths[i] * 0.5
        verts.append((p[0] + px * w, p[1] + py * w))
        verts.append((p[0] - px * w, p[1] - py * w))
    tris = []
    for i in range(0, len(verts) - 3, 2):
        a, b, c, d = verts[i], verts[i+1], verts[i+2], verts[i+3]
        tris += [a, c, b,  b, c, d]
    _tris(tris, color)

def rounded_bg(bx, by, bw, bh, s):
    br, bg, bb, ba = getattr(s, "bg_color", (0, 0, 0, 1.0))
    # sRGB -> linear (for more consistent opacity blending)
    def conv(u): return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    lr, lg, lb = conv(br), conv(bg), conv(bb)
    alpha = max(0.0, min(1.0, ba)) * max(0.0, min(1.0, getattr(s, "bg_opacity", 0.35)))
    rounded_rect_fill(bx, by, bw, bh, int(getattr(s, "corner_radius", 8)), (lr, lg, lb, alpha))

# ---------- Mouse glyph (visual) ----------

def _draw_mouse_tail_block(x:int, y:int, size:int, line_col):
    tail_w = max(6, int(size * 0.26))
    tail_h = max(4, int(size * 0.18))
    tx = x + (size - tail_w) // 2
    ty = y - int(tail_h * 0.55)
    rounded_rect_fill(tx, ty, tail_w, tail_h, int(tail_h * 0.45), (0, 0, 0, 0.28))
    rounded_rect_stroke(tx, ty, tail_w, tail_h, int(tail_h * 0.45), _STROKE_TH, line_col)

def _draw_mouse_tail_s(x:int, y:int, size:int, s, alpha_scale:float, line_col, *, body_fn=polyline_thick):
    length = int(size * 1.55)
    base_x = x + size // 2 - int(size * 0.04)
    base_y = y - 2
    pts = []; widths = []; steps = 12
    for i in range(steps + 1):
        t = i / steps
        yy = base_y - t * length
        sway = math.sin(t * math.pi * 0.9 + 0.25) * (size * 0.14) * (1.0 - 0.4 * t)
        xx = base_x + sway
        pts.append((xx, yy))
        widths.append(max(1.2, size * 0.095 * (1.0 - 0.65 * t)))
    body_col = (0.12, 0.12, 0.12, 0.30 * alpha_scale)
    body_fn(pts, widths, body_col)
    body_fn(pts, [w + _STROKE_TH * 0.25 for w in widths],
            (line_col[0], line_col[1], line_col[2], 0.32 * alpha_scale))

def draw_mouse_glyph_ergonomic(x:int, y:int, size:int, s, alpha_scale:float, state, *, wheel_active: bool):
    tr, tg, tb, ta = getattr(s, "text_color", (1, 1, 1, 1))

    if getattr(s, "mouse_use_custom_body", True):
        body = tuple(getattr(s, "mouse_body_color", (0.1333, 0.6667, 0.8863, 0.92)))
        lum_body = 0.2126 * body[0] + 0.7152 * body[1] + 0.0722 * body[2]
        plate_idle = (0.10, 0.10, 0.10, 0.12 * alpha_scale) if lum_body > 0.5 else (0.80, 0.80, 0.80, 0.15 * alpha_scale)
        plate_on   = (0.10, 0.10, 0.10, 0.65 * alpha_scale) if lum_body > 0.5 else (0.90, 0.90, 0.90, 0.70 * alpha_scale)
    else:
        lum_text = 0.2126 * tr + 0.7152 * tg + 0.0722 * tb
        if lum_text < 0.55:
            body = (0.18, 0.18, 0.18, 0.92 * alpha_scale)
            plate_idle = (0.80, 0.80, 0.80, 0.15 * alpha_scale); plate_on = (0.90, 0.90, 0.90, 0.70 * alpha_scale)
            lum_body = 0.18
        else:
            body = (0.92, 0.92, 0.92, 0.92 * alpha_scale)
            plate_idle = (0.10, 0.10, 0.10, 0.12 * alpha_scale); plate_on = (0.10, 0.10, 0.10, 0.65 * alpha_scale)
            lum_body = 0.92

    # Wheel colors
    if lum_body > 0.5:
        wheel_idle_col   = (0.10, 0.10, 0.10, 0.65 * alpha_scale)
        wheel_active_col = (0.92, 0.92, 0.92, 0.95 * alpha_scale)
    else:
        wheel_idle_col   = (0.80, 0.80, 0.80, 0.65 * alpha_scale)
        wheel_active_col = (0.10, 0.10, 0.10, 0.95 * alpha_scale)

    line = outline_col(s, 0.95 * alpha_scale)

    # Sizes
    body_h = int(size * 1.35); r_top = int(size * 0.28); r_bot = int(size * 0.22)

    # Tail
    _draw_mouse_tail_block(x, y, size, line)
    if getattr(s, "mouse_show_tail", True):
        _draw_mouse_tail_s(x, y, size, s, alpha_scale, line)

    # Body
    rounded_rect_fill(x, y, size, body_h, r_bot, body)
    rounded_rect_fill(x + 1, y + 2, size - 2, body_h - 4, r_bot, (body[0], body[1], body[2], body[3] * 0.90))
    rounded_rect_fill(x + 2, y + body_h // 5, size - 4, body_h - body_h // 5 - 2, r_top,
                      (body[0], body[1], body[2], body[3] * 0.85))

    # Button plates
    top_h   = int(body_h * 0.42)
    plate_h = max(10, top_h - 10)
    plate_y = y + body_h - top_h + 6

    # NEW: shift buttons (eyes) and wheel (nose) slightly lower inside the body
    # so they don’t intersect the outline at small glyph sizes.
    plate_y -= int(size * 0.08)

    safe_inset    = int(size * 0.06)
    plate_w_total = size - (8 + safe_inset * 2)
    plate_w       = plate_w_total // 2
    inset_x       = x + (size - plate_w_total) // 2
    sep_x         = inset_x + plate_w

    left_down  = "LEFTMOUSE"  in state.buttons_down
    right_down = "RIGHTMOUSE" in state.buttons_down
    if getattr(s, "mirror_mouse_lr", False):
        left_down, right_down = right_down, left_down

    rounded_rect_fill(inset_x,   plate_y, plate_w - 3, plate_h, int(plate_h * 0.30),
                      plate_on if left_down else plate_idle)
    rounded_rect_fill(sep_x + 3, plate_y, plate_w - 3, plate_h, int(plate_h * 0.30),
                      plate_on if right_down else plate_idle)

    # Wheel channel & wheel
    ch_h = max(6, int(plate_h * 0.46))
    ch_w = max(8, int(size * 0.26))
    ch_x = x + (size - ch_w) // 2; ch_y = plate_y - ch_h - 4
    rounded_rect_fill(ch_x, ch_y, ch_w, ch_h, int(ch_h * 0.36), (0, 0, 0, 0.12))

    wh_w = max(6, int(ch_w * 0.68))
    wh_h = max(6, int(ch_h * 0.76))
    wh_x = x + (size - wh_w) // 2; wh_y = ch_y + (ch_h - wh_h) // 2

    rounded_rect_fill(wh_x, wh_y, wh_w, wh_h, int(wh_h * 0.26),
                      wheel_active_col if wheel_active else wheel_idle_col)

    # Strokes
    rounded_rect_stroke(x, y, size, body_h, r_bot, 2, line)
    rounded_rect_stroke(inset_x, plate_y, plate_w - 3, plate_h, int(plate_h * 0.30), 2, line)
    rounded_rect_stroke(sep_x + 3, plate_y, plate_w - 3, plate_h, int(plate_h * 0.30), 2, line)
    rounded_rect_stroke(ch_x, ch_y, ch_w, ch_h, int(ch_h * 0.36), 2, line)
    rounded_rect_stroke(wh_x, wh_y, wh_w, wh_h, int(wh_h * 0.26), 2, line)

def register(): pass
def unregister(): pass
