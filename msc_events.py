## msc_events.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.


import math, bpy, blf
from time import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
from . import msc_mouse, msc_branding
from .msc_translation import _ as _, _active_locale as _active_locale  # explicit import of locale getter

# ---------- Constants ----------
WHEEL_ACTIVE_MS = 80
SCROLL_GROUP_MS = 80

# Soft cap for viewport redraws (prevents slider stutter)
_REDRAW_MIN_INTERVAL = 0.05  # seconds (~20 FPS)
_last_redraw_ts = 0.0

# ---------- State & datatypes ----------

def _now():
    return time()


@dataclass
class InputEvent:
    text: str
    t0: float


class MSCState:
    handler = None
    running = False
    events: List[InputEvent] = []
    box_rect: Optional[Tuple[int, int, int, int]] = None
    dragging = False
    drag_dx = 0
    drag_dy = 0

    transform_active = False
    transform_kind = None
    transform_axis = None

    buttons_down: Set[str] = set()
    button_times: Dict[str, float] = {}     # when each mouse button was pressed
    STUCK_TIMEOUT: float = 0.6              # seconds before we auto-release a stuck highlight
    suppress_buttons_until_mouseup: bool = False

    wheel_active_until: float = 0.0

    mod_times: Dict[str, float] = {}

    scroll_dir: Optional[str] = None
    scroll_count: int = 0
    scroll_last_t: float = 0.0

    active_area: Optional[bpy.types.Area] = None

    # track current locale to clear history on change
    current_locale: Optional[str] = None


# ---------- Maps (logical → localized at runtime) ----------

def _mouse_labels_runtime(s):
    left = _("Left Click")
    right = _("Right Click")
    mid = _("Middle Click")
    if getattr(s, "mirror_mouse_lr", False):
        left, right = right, left
    return {"LEFTMOUSE": left, "RIGHTMOUSE": right, "MIDDLEMOUSE": mid}


_WHEEL_TYPES = {"WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE"}
_MOUSE_BUTTONS = {"LEFTMOUSE", "RIGHTMOUSE", "MIDDLEMOUSE"}
_LR_BUTTONS = {"LEFTMOUSE", "RIGHTMOUSE"}

_LETTER_KEYS = {chr(k) for k in range(65, 91)}
_TOPROW_NUMS = {"ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE",
                "SIX", "SEVEN", "EIGHT", "NINE"}

_IGNORE_UP = (
    {f"F{i}" for i in range(1, 25)}
    | {
        "ESC", "TAB", "RET", "RETURN", "ENTER", "PAGE_UP", "PAGE_DOWN",
        "HOME", "END", "DEL", "DELETE", "BACK_SPACE",
        "UP_ARROW", "DOWN_ARROW", "LEFT_ARROW", "RIGHT_ARROW",
    }
    | {f"NUMPAD_{i}" for i in range(10)} | {"NUMPAD_ENTER"}
    | _LETTER_KEYS | _TOPROW_NUMS
)

# Localized modifier names for standalone display and combo prefixes
_MOD_KEYS = {
    "LEFT_SHIFT": _("Shift"), "RIGHT_SHIFT": _("Shift"),
    "LEFT_CTRL": _("Ctrl"), "RIGHT_CTRL": _("Ctrl"),
    "LEFT_ALT": _("Alt"), "RIGHT_ALT": _("Alt"),
    "OSKEY": _("Win"),
}


# ---------- Helpers ----------

def _append_event(t: str):
    MSCState.events.append(InputEvent(t, _now()))


def _bump_wheel_active():
    MSCState.wheel_active_until = _now() + max(0.08, WHEEL_ACTIVE_MS / 1000.0)


def _handle_scroll_grouping(direction: str, s):
    """Group rapid wheel events and show localized arrow text."""
    now = _now()
    window = max(0.08, SCROLL_GROUP_MS / 1000.0)
    _bump_wheel_active()
    up_lbl = _("Scroll (↑)")
    dn_lbl = _("Scroll (↓)")
    base_lbl = up_lbl if direction == "UP" else dn_lbl
    if MSCState.scroll_dir == direction and (now - MSCState.scroll_last_t) <= window:
        MSCState.scroll_count += 1
        MSCState.scroll_last_t = now
        if MSCState.events:
            ev = MSCState.events[-1]
            ev.text = f"{base_lbl} ×{MSCState.scroll_count}"
        return
    MSCState.scroll_dir = direction
    MSCState.scroll_count = 1
    MSCState.scroll_last_t = now
    _append_event(base_lbl)


def _is_view3d_window(context) -> bool:
    try:
        return (context.area and context.area.type == 'VIEW_3D' and
                context.region and context.region.type == 'WINDOW')
    except Exception:
        return False


def _format_key_from_type(t: str) -> str:
    # Numpad
    if t.startswith("NUMPAD_"):
        return f"{_('Numpad')} {t.split('_', 1)[1]}"
    # Function keys F1..F24
    if t.startswith("F") and t[1:].isdigit():
        return t
    # Common specials
    SPECIAL = {
        "SPACE": _("Space"),
        "TAB": _("Tab"),
        "ESC": _("Esc"), "ESCAPE": _("Esc"),
        "RET": _("Enter"), "RETURN": _("Enter"), "ENTER": _("Enter"),
        "UP_ARROW": _("Up Arrow"),
        "DOWN_ARROW": _("Down Arrow"),
        "LEFT_ARROW": _("Left Arrow"),
        "RIGHT_ARROW": _("Right Arrow"),
    }
    if t in SPECIAL:
        return SPECIAL[t]
    return t.replace("_", " ").title()


def _label_from_event(event, s) -> Optional[str]:
    t, v = event.type, event.value
    if t == "TEXTINPUT" or v not in {"PRESS", "RELEASE"}:
        return None
    if getattr(event, "is_repeat", False):
        return None

    # Modifiers
    if t in _MOD_KEYS:
        name = _MOD_KEYS[t]
        if v == "PRESS":
            MSCState.mod_times[name] = _now()
            if getattr(s, "show_modifiers", True):
                return f"{name} ↓"
            return None
        else:
            MSCState.mod_times.pop(name, None)
            if getattr(s, "show_modifiers", True):
                return f"{name} ↑"
            return None

    # Combo prefixes
    mods = []
    if getattr(s, "show_modifiers", True):
        if event.ctrl:
            mods.append(_("Ctrl"))
        if event.shift:
            mods.append(_("Shift"))
        if event.alt:
            mods.append(_("Alt"))
        if getattr(event, "oskey", False):
            mods.append(_("Win"))

    labels = _mouse_labels_runtime(s)

    glyph_visible = getattr(s, "show_mouse_glyph", True)
    allow_lr_text = (not glyph_visible) or bool(getattr(s, "show_mouse", True))
    allow_mmb_text = True

    base = None

    # Scroll
    if t in _WHEEL_TYPES and v == "PRESS":
        _handle_scroll_grouping("UP" if t in {"WHEELUPMOUSE", "WHEELINMOUSE"} else "DOWN", s)
        return None

    # Middle mouse
    if t == "MIDDLEMOUSE":
        if v == "PRESS":
            _bump_wheel_active()
            MSCState.button_times["MIDDLEMOUSE"] = _now()
            if allow_mmb_text:
                base = f"{labels.get('MIDDLEMOUSE', _('Middle Click'))} ↓"
        else:
            MSCState.button_times.pop("MIDDLEMOUSE", None)
            return None

    # Left/Right mouse
    if t in _LR_BUTTONS:
        label_lr = labels.get(t, t)
        if MSCState.suppress_buttons_until_mouseup and v == "PRESS":
            return None
        if v == "PRESS":
            duplicate = t in MSCState.buttons_down
            MSCState.buttons_down.add(t)
            MSCState.button_times[t] = _now()
            if allow_lr_text and not duplicate:
                base = f"{label_lr} ↓"
        else:
            MSCState.buttons_down.discard(t)
            MSCState.button_times.pop(t, None)
            if allow_lr_text:
                base = f"{label_lr} ↑"

    # Keyboard fallback
    if base is None:
        if t in _MOUSE_BUTTONS or t in _WHEEL_TYPES:
            return None
        if getattr(s, "show_keys", True):
            base = _format_key_from_type(t)

    if v == "RELEASE" and t in _IGNORE_UP:
        return None
    return " + ".join(mods + [base]) if (base and mods) else base


# ---------- Transform monitor ----------

def _active_transform_info(context) -> Optional[Tuple[str, Optional[str]]]:
    wm = context.window_manager
    ops = getattr(wm, "operators", None)
    if not ops:
        return None
    for op in reversed(ops):
        try:
            idname = op.bl_idname
        except Exception:
            continue
        if not idname.startswith("TRANSFORM_OT_"):
            continue
        kind = idname.split("_")[-1].capitalize()
        axis = None
        try:
            ca = op.properties.constraint_axis
            if len(ca) >= 3:
                if ca[0]:
                    axis = "X"
                elif ca[1]:
                    axis = "Y"
                elif ca[2]:
                    axis = "Z"
        except Exception:
            pass
        return (kind, axis)
    return None


def _tick_transform_monitor(context, s):
    if not getattr(s, "show_transform_axis", True):
        if MSCState.transform_active:
            MSCState.transform_active = False
            MSCState.transform_kind = None
            MSCState.transform_axis = None
        return
    info = _active_transform_info(context)
    if info is None:
        if MSCState.transform_active:
            MSCState.transform_active = False
            MSCState.transform_kind = None
            MSCState.transform_axis = None
        return
    kind, axis = info
    if not MSCState.transform_active:
        MSCState.transform_active = True
        MSCState.transform_kind = kind
        MSCState.transform_axis = axis
        _append_event(f"{_('Transform: ')}{kind}")
        return
    if MSCState.transform_axis != axis:
        MSCState.transform_axis = axis
        _append_event(f"{_('Axis ')}{axis if axis else _('Free')}")


# ---------- Measurement & brand ----------

def _title_icon_metrics(s) -> Tuple[int, int, int, str]:
    """Compute metrics for the brand icon + title row."""
    if not getattr(s, "show_title", False):
        return 0, 0, 0, ""

    mode = getattr(s, "title_icon_mode", "DEFAULT")
    if mode == "NONE":
        icon_path = ""
    elif mode == "CUSTOM":
        # User-chosen file path
        icon_path = (getattr(s, "title_icon_path", "") or "").strip()
    else:
        # Built-in MoCast icon (Beacon, Camera, etc.)
        icon_key = getattr(s, "title_builtin_icon", "BEACON")
        icon_path = msc_branding.builtin_icon_path(icon_key)


    title_fs = int(getattr(s, "title_font_size", 28))
    size = int(getattr(s, "title_icon_size", 56))  # always respect slider, no auto-scale
    pad = int(getattr(s, "title_icon_pad", 6))

    icon_sz = size if (icon_path and size > 0) else 0
    pre = (icon_sz + pad) if icon_sz > 0 else 0

    has_text = bool((getattr(s, "title_text", "") or "").strip())
    if not has_text and icon_sz == 0:
        return 0, 0, 0, ""

    title_line_h = int(title_fs * 1.4)
    top = max(title_line_h, icon_sz, int(max(14, title_fs * 1.2)))
    return pre, top, icon_sz, icon_path


def _measure_brand_box(s) -> Tuple[int, int, int, int, int, str]:
    pad = 6
    if not getattr(s, "show_title", False):
        return 0, 0, pad, 0, 0, ""
    title_pre, top_h, icon_sz, icon_path = _title_icon_metrics(s)
    if top_h == 0:
        return 0, 0, pad, 0, 0, ""
    blf.size(0, int(getattr(s, "title_font_size", 28)))
    tw, _ = blf.dimensions(0, getattr(s, "title_text", "") or "")
    content_w = max(int(tw) + title_pre, icon_sz)
    bw = content_w + pad * 2
    bh = top_h + pad * 2
    return bw, bh, pad, title_pre, icon_sz, icon_path


def _measure_events_box(lines: List[str], s) -> Tuple[int, int, int, int]:
    pad = 6
    ev_h = int(getattr(s, "font_size", 16) * 1.4)
    max_w = 0
    for tx in lines:
        blf.size(0, int(getattr(s, "font_size", 16)))
        w, _ = blf.dimensions(0, tx)
        max_w = max(max_w, int(w))
    spacer = ev_h
    extra_bottom = max(6, int(ev_h * 0.40))
    other = len(lines)
    ew = max_w + pad * 2
    eh = spacer + other * ev_h + pad * 2 + extra_bottom
    return ew, eh, pad, ev_h


def _resolve_position(rw: int, rh: int, bw: int, bh: int, s) -> Tuple[int, int]:
    pos = getattr(s, "position", "BOTTOM_LEFT")
    ox = int(getattr(s, "offset_x", 64))
    oy = int(getattr(s, "offset_y", 77))
    margin = 10

    # X
    if pos.endswith("_LEFT"):
        bx = margin + ox
    elif pos.endswith("_CENTER"):
        bx = (rw - bw) // 2 + ox
    else:
        bx = (rw - bw) - margin - ox

    # Y
    if pos.startswith("TOP_"):
        by = (rh - bh) - margin - oy
    elif pos.startswith("MIDDLE_"):
        by = (rh - bh) // 2 + oy
    else:
        by = margin + oy

    bx = int(max(margin, min(rw - bw - margin, bx)))
    by = int(max(margin, min(rh - bh - margin, by)))
    return bx, by


def _draw_two_box_overlay(lines: List[str], s) -> Tuple[int, int, int, int, int, int, int, int]:
    region = bpy.context.region

    brand_w, brand_h, bpad, title_pre, icon_sz, icon_path = _measure_brand_box(s)
    ev_w, ev_h, epad, line_h = _measure_events_box(lines, s)
    gutter = 6 if brand_h > 0 else 0
    bw = max(brand_w, ev_w)
    bh = brand_h + gutter + ev_h

    bx, by = _resolve_position(region.width, region.height, bw, bh, s)

    evx, evy, evw, evh = bx, by, bw, ev_h
    brx, bry, brw, brh = bx, by + ev_h + gutter, bw, brand_h

    if brand_h > 0:
        msc_mouse.rounded_bg(brx, bry, brw, brh, s)
    msc_mouse.rounded_bg(evx, evy, evw, evh, s)

    tr, tg, tb, ta = getattr(s, "title_text_color", (1, 1, 1, 1))
    er, eg, eb, ea = getattr(s, "text_color", (1, 1, 1, 1))

    if brand_h > 0:
        if icon_path and icon_sz > 0:
            msc_branding.ensure_icon_loaded(icon_path)
            msc_branding.draw_image_icon(brx + bpad, bry + brh - bpad - icon_sz, icon_sz)

        title_str = (getattr(s, "title_text", "") or "").strip()
        if title_str:
            blf.size(0, int(getattr(s, "title_font_size", 28)))
            title_baseline = int(bry + (brh - int(getattr(s, "title_font_size", 28))) * 0.55) + 1
            line_x = brx + bpad + title_pre
            blf.position(0, line_x, title_baseline, 0)
            blf.color(0, tr, tg, tb, ta)
            blf.draw(0, title_str)

    blf.size(0, int(getattr(s, "font_size", 16)))
    ty = evy + evh - epad - line_h
    for tx in lines:
        blf.position(0, evx + epad, ty, 0)
        blf.color(0, er, eg, eb, ea)
        blf.draw(0, tx)
        ty -= line_h

    return bx, by, bw, bh, brx, bry, brw, brh


def _point_in_rect(px, py, rect):
    if not rect:
        return False
    x, y, w, h = rect
    return (x <= px <= x + w) and (y <= py <= y + h)


def gather_lines(s) -> Tuple[List[str], bool]:
    now = _now()
    ttl = getattr(s, "fade_seconds", 4.0)
    MSCState.events[:] = [ev for ev in MSCState.events if now - ev.t0 <= ttl]
    entries = MSCState.events[-getattr(s, "history_count", 5):]
    lines = [ev.text for ev in entries]
    idle = False
    if not lines and getattr(s, "show_idle_hint", True):
        lines = [getattr(s, "idle_hint_text", "Momentum Screencast Overlay")]
        idle = True
    return lines, idle


# ---------- Draw callback ----------

def _draw_mouse_sidecar_for_events(evx, evy, evw, evh, s, idle_only):
    """Draw the ergonomic mouse glyph next to the event box."""
    hide_when_idle = getattr(s, "mouse_hide_when_idle", False)
    if idle_only and hide_when_idle:
        return

    gsize = int(getattr(s, "mouse_glyph_size", 46))
    gh = int(gsize * 1.35)
    gap = int(getattr(s, "mouse_sidecar_gap", 14))
    region = bpy.context.region

    gx = evx + evw + gap
    gy = evy + evh - gh

    if gx + gsize > region.width:
        gx = evx - gap - gsize
    gy = max(0, min(region.height - gh, gy))

    wheel_on = (_now() <= MSCState.wheel_active_until)
    msc_mouse.draw_mouse_glyph_ergonomic(
        gx, gy, gsize, s,
        alpha_scale=1.0,
        state=MSCState,
        wheel_active=wheel_on,
    )


def draw_callback_2d():
    s = bpy.context.window_manager.msc_settings

    # If language changed, clear history so future lines appear localized
    loc = _active_locale()
    if MSCState.current_locale != loc:
        MSCState.current_locale = loc
        MSCState.events.clear()

    # enforce single-overlay-per-screen
    if getattr(s, "limit_one_per_screen", True):
        if MSCState.active_area is None:
            MSCState.active_area = bpy.context.area
        if bpy.context.area != MSCState.active_area:
            return

    lines, idle_only = gather_lines(s)

    title_pre, top_h, icon_sz, icon_p = _title_icon_metrics(s)
    has_brand = (top_h > 0)
    if not lines and not has_brand:
        lines = [""]

    try:
        bx, by, bw, bh, brx, bry, brw, brh = _draw_two_box_overlay(lines, s)
        MSCState.box_rect = (bx, by, bw, bh)

        if getattr(s, "show_mouse_glyph", True):
            gutter = 6 if brh > 0 else 0
            evh = bh - brh - gutter
            evx, evy, evw = bx, by, bw
            _draw_mouse_sidecar_for_events(evx, evy, evw, evh, s, idle_only)

    except Exception as e:
        print("[MoCast] draw error:", e)


# ---------- Modal & input ----------

class MSC_OT_modal_capture(bpy.types.Operator):
    bl_idname = "momentum_screencast_overlay.modal_capture"
    bl_label = "Momentum Screencast Capture"

    def modal(self, context, event):
        if not MSCState.running:
            return {"CANCELLED"}
        s = context.window_manager.msc_settings

        is_v3d_win = _is_view3d_window(context)

        # Watchdog for missed RELEASE
        now = _now()
        for b in list(MSCState.button_times):
            if (now - MSCState.button_times[b]) > MSCState.STUCK_TIMEOUT:
                MSCState.buttons_down.discard(b)
                del MSCState.button_times[b]

        # Follow last-active 3D View when limited to one overlay per screen
        if getattr(s, "limit_one_per_screen", True):
            if is_v3d_win and event.type in {
                'MOUSEMOVE', 'LEFTMOUSE', 'RIGHTMOUSE', 'MIDDLEMOUSE',
                'EVT_TWEAK_L', 'EVT_TWEAK_R'
            }:
                if MSCState.active_area is not context.area:
                    MSCState.active_area = context.area
                    MSCState.buttons_down.clear()
                    MSCState.button_times.clear()

        # Dragging (Shift + LMB by default, depending on settings)
        if getattr(s, 'drag_enable', True) and is_v3d_win:
            over = _point_in_rect(event.mouse_region_x, event.mouse_region_y, MSCState.box_rect)
            req = getattr(s, 'drag_requires_shift', True)
            ok = (not req) or event.shift

            if event.type in {'LEFTMOUSE', 'EVT_TWEAK_L'} and event.value == 'PRESS':
                if over and ok and (MSCState.active_area in (None, context.area)):
                    MSCState.dragging = True
                    MSCState.suppress_buttons_until_mouseup = True
                    MSCState.buttons_down.clear()
                    MSCState.button_times.clear()
                    bx, by, bw, bh = MSCState.box_rect if MSCState.box_rect else (0, 0, 0, 0)
                    MSCState.drag_dx = event.mouse_region_x - bx
                    MSCState.drag_dy = event.mouse_region_y - by
                    return {'RUNNING_MODAL'}

            if event.type in {'LEFTMOUSE', 'EVT_TWEAK_L'} and event.value == 'RELEASE':
                MSCState.dragging = False
                MSCState.suppress_buttons_until_mouseup = False

            if event.type in {'MOUSEMOVE', 'EVT_TWEAK_L'} and MSCState.dragging:
                region = context.region
                rw, rh = region.width, region.height
                bx, by, bw, bh = MSCState.box_rect if MSCState.box_rect else (0, 0, 0, 0)

                nbx = event.mouse_region_x - MSCState.drag_dx
                nby = event.mouse_region_y - MSCState.drag_dy

                margin = 10
                pos = getattr(s, "position", "BOTTOM_LEFT")

                if pos.endswith("_LEFT"):
                    s.offset_x = int(nbx - margin)
                elif pos.endswith("_CENTER"):
                    s.offset_x = int(nbx - (rw - bw) // 2)
                else:
                    s.offset_x = int((rw - bw) - margin - nbx)

                if pos.startswith("TOP_"):
                    s.offset_y = int((rh - bh) - margin - nby)
                elif pos.startswith("MIDDLE_"):
                    s.offset_y = int(nby - (rh - bh) // 2)
                else:
                    s.offset_y = int(nby - margin)

        # Events → labels
        if _is_view3d_window(context) or (event.type not in _MOUSE_BUTTONS and event.type not in _WHEEL_TYPES):
            label = _label_from_event(event, s)
            if label:
                _append_event(label)

        _tick_transform_monitor(context, s)

        # Throttled redraw
        global _last_redraw_ts
        now2 = _now()
        if (now2 - _last_redraw_ts) >= _REDRAW_MIN_INTERVAL:
            for area in context.screen.areas:
                if area.type == "VIEW_3D":
                    area.tag_redraw()
            _last_redraw_ts = now2
        return {"PASS_THROUGH"}

    def execute(self, context):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


# ---------- Start/Stop (toggle) ----------

class MSC_OT_toggle(bpy.types.Operator):
    bl_idname = "momentum_screencast_overlay.toggle_overlay"
    bl_label = _("Start / Stop Overlay")
    bl_description = _("Toggle the keyboard & mouse overlay in the viewport")

    def execute(self, context):
        if not MSCState.running:
            MSCState.running = True
            MSCState.active_area = None
            if MSCState.handler is None:
                MSCState.handler = bpy.types.SpaceView3D.draw_handler_add(
                    draw_callback_2d, (), "WINDOW", "POST_PIXEL"
                )
            bpy.ops.momentum_screencast_overlay.modal_capture("INVOKE_DEFAULT")
            self.report({"INFO"}, "MoCast: started")
        else:
            MSCState.running = False
            if MSCState.handler is not None:
                try:
                    bpy.types.SpaceView3D.draw_handler_remove(MSCState.handler, "WINDOW")
                except Exception:
                    pass
                MSCState.handler = None
            MSCState.events.clear()
            MSCState.transform_active = False
            MSCState.transform_kind = None
            MSCState.transform_axis = None
            MSCState.buttons_down.clear()
            MSCState.button_times.clear()
            MSCState.wheel_active_until = 0.0
            MSCState.scroll_dir = None
            MSCState.scroll_count = 0
            MSCState.scroll_last_t = 0.0
            MSCState.active_area = None
            self.report({"INFO"}, "MoCast: stopped")
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()
        return {"FINISHED"}


# ---------- Registration ----------

classes = (MSC_OT_modal_capture, MSC_OT_toggle)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    if MSCState.handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(MSCState.handler, "WINDOW")
        except Exception:
            pass
        MSCState.handler = None
    MSCState.running = False
    MSCState.events.clear()
    MSCState.transform_active = False
    MSCState.transform_kind = None
    MSCState.transform_axis = None
    MSCState.buttons_down.clear()
    MSCState.button_times.clear()
    MSCState.wheel_active_until = 0.0
    MSCState.scroll_dir = None
    MSCState.scroll_count = 0
    MSCState.scroll_last_t = 0.0
    MSCState.active_area = None
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
