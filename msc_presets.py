## msc_presets.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.

import os
import json
import bpy
from .msc_translation import _


# ---------------------------------------------------------------------------
# Paths / helpers
# ---------------------------------------------------------------------------

def _preset_dir():
    """Config folder for MoCast presets."""
    base = bpy.utils.user_resource(
        'CONFIG',
        path="momentum_screencast_overlay",
        create=True,
    )
    return bpy.path.abspath(base)


# Public helper for UI label
def preset_folder_display():
    try:
        return _preset_dir()
    except Exception:
        return _("(unavailable)")


def _preset_path_from_name(name: str) -> str:
    """Map a preset name to its JSON file path."""
    folder = _preset_dir()
    filename = f"{name}.json"
    return os.path.join(folder, filename)


# ---------------------------------------------------------------------------
# Settings <-> dict
# ---------------------------------------------------------------------------

def _settings_to_dict(s):
    """Serialize the current MoCast settings to a plain dict."""
    return {
        "ui_show_advanced": bool(s.ui_show_advanced),

        # Events appearance / behaviour
        "show_keys": s.show_keys,
        "show_mouse": s.show_mouse,
        "show_modifiers": s.show_modifiers,
        "history_count": int(s.history_count),
        "fade_seconds": float(s.fade_seconds),
        "font_size": int(s.font_size),
        "text_color": tuple(s.text_color),

        "bg_color": tuple(s.bg_color),
        "bg_opacity": float(s.bg_opacity),
        "corner_radius": int(s.corner_radius),

        # Branding
        "show_title": s.show_title,
        "title_text": s.title_text,
        "title_icon_mode": s.title_icon_mode,
        "title_builtin_icon": getattr(s, "title_builtin_icon", "BEACON"),
        "title_icon_path": s.title_icon_path,
        "title_icon_auto": s.title_icon_auto,
        "title_icon_size": int(s.title_icon_size),
        "title_icon_pad": int(s.title_icon_pad),
        "title_font_size": int(s.title_font_size),
        "title_text_color": tuple(s.title_text_color),


        # Idle overlay
        "show_idle_hint": s.show_idle_hint,
        "idle_hint_text": s.idle_hint_text,

        # Transform monitor / placement / drag
        "show_transform_axis": s.show_transform_axis,
        "position": s.position,
        "offset_x": int(s.offset_x),
        "offset_y": int(s.offset_y),
        "drag_enable": s.drag_enable,
        "drag_requires_shift": s.drag_requires_shift,

        # Mouse glyph
        "show_mouse_glyph": s.show_mouse_glyph,
        "mouse_glyph_size": int(s.mouse_glyph_size),
        "mouse_sidecar_gap": int(s.mouse_sidecar_gap),
        "mouse_hide_when_idle": bool(s.mouse_hide_when_idle),
        "mirror_mouse_lr": s.mirror_mouse_lr,

        "mouse_use_custom_body": s.mouse_use_custom_body,
        "mouse_body_color": tuple(s.mouse_body_color),
        "mouse_outline_shade": int(s.mouse_outline_shade),
        "mouse_show_tail": bool(s.mouse_show_tail),

        # Screen behaviour
        #"limit_one_per_screen": bool(s.limit_one_per_screen),
    }


def _clamp_color_tuple(v):
    """Clamp a 3- or 4-tuple of floats into [0, 1]."""
    try:
        return tuple(max(0.0, min(1.0, float(c))) for c in v)
    except Exception:
        return v


def _apply_settings_from_dict(s, data: dict):
    """Apply a preset dict to the MSC_Settings instance."""
    color_keys = {
        "bg_color",
        "text_color",
        "title_text_color",
        "mouse_body_color",
    }

    for k, v in data.items():
        # Clamp colors defensively so we don't re-break the color pickers
        if k in color_keys:
            v = _clamp_color_tuple(v)

        if hasattr(s, k):
            try:
                setattr(s, k, v)
            except Exception:
                # Ignore bad or outdated fields quietly
                pass


def _reset_settings_to_defaults(settings):
    """
    Reset all properties on the MSC_Settings instance to their RNA defaults.
    This is used for the 'Default' preset.
    """
    rna = settings.bl_rna.properties
    for prop_id in rna.keys():
        if prop_id == "rna_type":
            continue
        try:
            settings.property_unset(prop_id)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Preset loading
# ---------------------------------------------------------------------------

def load_preset(context, name: str):
    """
    Load the given preset into context.window_manager.msc_settings.

    'Default' is special: it resets everything to factory defaults (RNA).
    Returns (ok: bool, message: str).
    """
    try:
        settings = context.window_manager.msc_settings
    except Exception:
        return False, "MoCast settings not found on WindowManager"

    # Default preset: reset to RNA defaults
    if not name or name == "Default":
        _reset_settings_to_defaults(settings)
        return True, "Default preset loaded"

    path = _preset_path_from_name(name)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, f"Preset not found: {path}"
    except Exception as e:
        return False, f"Failed to load preset: {e}"

    try:
        _apply_settings_from_dict(settings, data)
    except Exception as e:
        return False, f"Failed to apply preset: {e}"

    # Force redraw of 3D Views
    screen = context.screen
    if screen:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

    return True, f"Preset loaded: {path}"


# ---------------------------------------------------------------------------
# Enum items + update callback for active_preset
# ---------------------------------------------------------------------------

def preset_enum_items(self, context):
    """
    Dynamic Enum items for the active_preset dropdown.

    Always includes 'Default', then one entry per *.json file in the preset dir
    (without the .json extension). 'Default' file is *not* required.

    IMPORTANT: Blender Enum identifiers must be identifier-like (no spaces or
    weird characters), so we skip any invalid names.
    """
    items = [("Default", "Default", _("Built-in default preset"))]

    try:
        folder = _preset_dir()
        if os.path.isdir(folder):
            for fn in sorted(os.listdir(folder)):
                if not fn.lower().endswith(".json"):
                    continue

                base = os.path.splitext(fn)[0]  # filename without .json

                if base == "Default":
                    # Default is handled specially; no need for a file entry
                    continue

                # Enum identifiers must be valid Python identifiers (no spaces,
                # no punctuation, no leading digit, etc.).
                if not base.isidentifier():
                    print(f"[MoCast] Skipping preset with invalid name for enum: {base!r}")
                    continue

                items.append((base, base, _("Preset ") + base))
    except Exception as exc:
        print("[MoCast] Error while building preset enum items:", exc)

    return items


def on_active_preset_changed(self, context):
    """
    Called whenever MSC_Settings.active_preset is changed.

    Auto-loads the selected preset (or reset to default).
    """
    name = getattr(self, "active_preset", "Default") or "Default"
    ok, msg = load_preset(context, name)
    if not ok:
        # We can't report via an Operator here, so just log to console.
        print("[MoCast] Preset load failed:", msg)


# ---------------------------------------------------------------------------
# Operators: Save / Delete presets
# ---------------------------------------------------------------------------

class MSC_OT_save_preset(bpy.types.Operator):
    """Save MoCast settings to a preset (overwrite or new)."""
    bl_idname = "momentum_screencast_overlay.save_preset"
    bl_label = _("Save Preset")

    mode: bpy.props.EnumProperty(
        name="Mode",
        description="How to save the preset",
        items=[
            ("OVERWRITE", "Overwrite current preset", ""),
            ("NEW", "Save as new preset", ""),
        ],
        default="OVERWRITE",
    )

    new_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name for the new preset",
        default="",
    )

    is_default: bpy.props.BoolProperty(
        name="Is Default",
        description="Internal flag to indicate the active preset is Default",
        default=False,
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        # Determine the currently active preset
        try:
            s = context.window_manager.msc_settings
            active = getattr(s, "active_preset", "Default") or "Default"
        except Exception:
            active = "Default"

        self.is_default = (active == "Default")

        if self.is_default:
            # Default cannot be overwritten: force NEW + empty name
            self.mode = "NEW"
            self.new_name = ""
        else:
            # Start on OVERWRITE by default; NEW uses current name as suggestion
            self.mode = "OVERWRITE"
            self.new_name = active

        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        layout = self.layout
        try:
            s = context.window_manager.msc_settings
            active = getattr(s, "active_preset", "Default") or "Default"
        except Exception:
            active = "Default"

        layout.label(text=_("Active preset: ") + active)

        if self.is_default:
            # Default cannot be overwritten
            layout.label(text=_("Default preset cannot be overwritten."))
            layout.label(text=_("Save current settings as a new preset:"))
            layout.prop(self, "new_name", text=_("Preset Name"))
        else:
            layout.prop(self, "mode", text=_("Action"))
            if self.mode == "NEW":
                layout.prop(self, "new_name", text=_("Preset Name"))
            else:
                layout.label(text=_("Existing preset will be overwritten."))

    def _sanitize_name(self, name_raw: str) -> str:
        """
        Clean up and validate a user-entered preset name so it is safe for:

        - Blender Enum identifiers (no spaces / weird chars)
        - File names (we keep it simple: only letters, digits, underscore)

        We also reserve the name 'Default'.
        """
        name = (name_raw or "").strip()
        if not name:
            return ""

        if name == "Default":
            # Default is reserved for the built-in preset
            return ""

        # Replace spaces with underscores to help the user
        name = name.replace(" ", "_")

        # Now enforce identifier rules: no punctuation, no leading digit, etc.
        if not name.isidentifier():
            return ""

        return name

    def execute(self, context):
        try:
            s = context.window_manager.msc_settings
            active = getattr(s, "active_preset", "Default") or "Default"
        except Exception:
            self.report({'ERROR'}, _("MoCast settings not found on WindowManager"))
            return {'CANCELLED'}

        # Decide target preset name
        if active == "Default" or self.mode == "NEW":
            # Must save as new
            name = self._sanitize_name(self.new_name)
            if not name:
                self.report(
                    {'ERROR'},
                    _("Please enter a valid preset name (not 'Default', letters/digits/underscore only)."),
                )
                return {'CANCELLED'}
        else:
            # Overwrite existing non-default preset
            name = active

        path = _preset_path_from_name(name)

        # Ensure folder exists
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception as e:
            self.report({'ERROR'}, _("Failed to create preset folder: ") + str(e))
            return {'CANCELLED'}

        # Serialize + write
        try:
            data = _settings_to_dict(s)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.report({'ERROR'}, _("Failed to save preset: ") + str(e))
            return {'CANCELLED'}

        # Update active preset name (especially important for NEW)
        s.active_preset = name

        self.report({'INFO'}, _("Preset saved: ") + path)
        return {'FINISHED'}


class MSC_OT_delete_preset(bpy.types.Operator):
    """Delete the currently selected preset (except Default)."""
    bl_idname = "momentum_screencast_overlay.delete_preset"
    bl_label = _("Delete Preset")

    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name of the preset to delete",
        default="",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        try:
            s = context.window_manager.msc_settings
            active = getattr(s, "active_preset", "Default") or "Default"
        except Exception:
            active = "Default"

        if not active or active == "Default":
            self.report({'ERROR'}, _("Default preset cannot be deleted."))
            return {'CANCELLED'}

        self.preset_name = active
        # Confirmation dialog
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        name = self.preset_name or "Default"

        if name == "Default":
            self.report({'ERROR'}, _("Default preset cannot be deleted."))
            return {'CANCELLED'}

        path = _preset_path_from_name(name)

        # Delete file if it exists
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            self.report({'ERROR'}, _("Failed to delete preset: ") + str(e))
            return {'CANCELLED'}

        # Switch back to Default and load it
        try:
            s = context.window_manager.msc_settings
            s.active_preset = "Default"
            ok, msg = load_preset(context, "Default")
            if not ok:
                print("[MoCast] Failed to reset to Default after delete:", msg)
        except Exception:
            pass

        self.report({'INFO'}, _("Preset deleted: ") + name)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    MSC_OT_save_preset,
    MSC_OT_delete_preset,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
