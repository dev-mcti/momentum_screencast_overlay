## msc_ui.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.


import bpy
from bpy.types import Panel, AddonPreferences, PropertyGroup, Operator
from bpy.props import (
    BoolProperty, StringProperty, EnumProperty, IntProperty,
    FloatProperty, FloatVectorProperty, PointerProperty
)

# Translation helpers
from .msc_translation import _, on_lang_override_update
from . import msc_presets


# ---------- Settings ----------

def _on_position_update(self, context):
    # Reset offsets when preset position changes
    self.offset_x = 0
    self.offset_y = 0


class MSC_Settings(PropertyGroup):
    # UI state (used for the Visibility & Behaviour foldout)
    ui_show_advanced: BoolProperty(
        name="", default=False,
        description="Show visibility & behaviour options"
    )

    # Branding
    show_title: BoolProperty(name="", default=True)
    title_text: StringProperty(name="", default="MoCast")
    title_icon_mode: EnumProperty(
        name="",
        # Internal values only; UI text is driven by panel buttons.
        items=[
            ("DEFAULT", "Default (Beacon)", "Use the bundled Momentum Beacon"),
            ("CUSTOM",  "Custom",           "Pick your own image file"),
            ("NONE",    "None",             "No icon"),
        ],
        default="DEFAULT",
    )
    
    # Which built-in MoCast icon to use when title_icon_mode == "DEFAULT"
    title_builtin_icon: EnumProperty(
        name="",
        description="Built-in MoCast branding icon",
        items=[
            ("BEACON",        "Beacon Icon",          ""),
            ("CURSOR",        "Cursor",               ""),
            ("KEYCAP",        "Keycap",               ""),
            ("ANIMATION",     "Animation",            ""),
            ("BRUSH_STROKE",  "Brush Stroke",         ""),
            ("CURVE",         "Curve",                ""),
            ("LOWPOLY_CUBE",  "Low-Poly Cube",        ""),
            ("CAMERA_1",      "Camera Icon 1",        ""),
            ("CAMERA_2",      "Camera Icon 2",        ""),
            ("RENDER_1",      "Render Icon 1",        ""),
            ("RENDER_2",      "Render Icon 2",        ""),
            ("PARTICLE_1",    "Particle Burst 1",     ""),
            ("PARTICLE_2",    "Particle Burst 2",     ""),
            ("PULSE",         "Pulse",                ""),
            ("NODE_COLOR",    "Colorful Node",        ""),
            ("RIGGING_COLOR", "Rigging (Colorful)",   ""),
            ("PRISM_1",       "Prism Icon 1",         ""),
            ("PRISM_2",       "Prism Icon 2",         ""),
        ],
        default="BEACON",
    )
    
    
    title_icon_path: StringProperty(name="", subtype="FILE_PATH", default="")
    # Kept for backward compatibility but forced off in draw()
    title_icon_auto: BoolProperty(name="", default=True)
    title_icon_size: IntProperty(name="", default=56, min=8, max=256)
    title_icon_pad: IntProperty(name="", default=6, min=0, max=32)
    title_font_size: IntProperty(name="", default=28, min=0, max=64)
    title_text_color: FloatVectorProperty(
        name="", subtype="COLOR_GAMMA", size=4,
        min=0.0, max=1.0,
        # #13ADFFFF
        default=(0.07303351, 0.6797883, 1.0, 1.0)
    )

    # Events appearance
    font_size: IntProperty(name="", default=16, min=0, max=64)
    bg_color: FloatVectorProperty(
        name="", subtype="COLOR", size=4,
        min=0.0, max=1.0,
        # #CDDEE6F
        default=(0.6138818, 0.7321329, 0.7908429, 1.0)
    )
    bg_opacity: FloatProperty(name="", default=0.35, min=0.0, max=1.0)
    text_color: FloatVectorProperty(
        name="", subtype="COLOR_GAMMA", size=4,
        min=0.0, max=1.0,
        # Value = 1, Alpha = 1 for predictable picking
        default=(1.0, 1.0, 1.0, 1.0)
    )
    corner_radius: IntProperty(name="", default=8, min=0, max=24)

    # Position (internal anchor; default = BOTTOM_LEFT, no UI control)
    position: EnumProperty(
        name="", update=_on_position_update, default="BOTTOM_LEFT",
        items=[
            ("TOP_LEFT",      "Top Left", ""),
            ("TOP_CENTER",    "Top Center", ""),
            ("TOP_RIGHT",     "Top Right", ""),
            ("MIDDLE_LEFT",   "Middle Left", ""),
            ("MIDDLE_CENTER", "Center", ""),
            ("MIDDLE_RIGHT",  "Middle Right", ""),
            ("BOTTOM_LEFT",   "Bottom Left", ""),
            ("BOTTOM_CENTER", "Bottom Center", ""),
            ("BOTTOM_RIGHT",  "Bottom Right", ""),
        ],
    )
    # hidden (used by presets / drag math)
    offset_x: IntProperty(name="Offset X", default=64, min=-4096, max=4096)
    offset_y: IntProperty(name="Offset Y", default=77, min=-4096, max=4096)

    # Behaviour (history/fade)
    history_count: IntProperty(name="", default=4, min=1, max=20)
    fade_seconds: FloatProperty(name="", default=3.0, min=0.25, max=30.0)

    # What to display (Events group)
    show_keys: BoolProperty(name="", default=True)
    show_mouse: BoolProperty(name="", default=True)
    show_modifiers: BoolProperty(name="", default=True)

    # Idle
    show_idle_hint: BoolProperty(name="", default=True)
    idle_hint_text: StringProperty(name="", default="Momentum Screencast Overlay")

    # Transform monitor (Events group)
    show_transform_axis: BoolProperty(name="", default=True)

    # Dragging
    drag_enable: BoolProperty(name="", default=True)
    # Forced true and hidden in UI; keep for preset compatibility
    drag_requires_shift: BoolProperty(name="Require Shift to Drag", default=True)

    # Mouse glyph (sidecar)
    show_mouse_glyph: BoolProperty(name="", default=True)
    mouse_glyph_size: IntProperty(name="", default=46, min=30, max=100)
    mouse_sidecar_gap: IntProperty(name="", default=14, min=6, max=64)

    # Simpler idle visibility rule for glyph: just "Hide when idle"
    mouse_hide_when_idle: BoolProperty(
        name="",
        description="Hide the mouse glyph when the overlay is idle",
        default=False,
    )

    mirror_mouse_lr: BoolProperty(name="", default=False)

    # Mouse color: always custom now (no toggle in UI)
    mouse_use_custom_body: BoolProperty(name="", default=True)
    mouse_body_color: FloatVectorProperty(
        name="", subtype="COLOR_GAMMA", size=4,
        min=0.0, max=1.0,
        # Alpha set to 1.0 for consistency
        default=(0.1333315, 0.6666651, 0.8862789, 1.0)
    )
    mouse_outline_shade: IntProperty(
        name="",
        description="Outline brightness in 10 steps (1=darkest, 10=lightest)",
        default=1, min=1, max=10
    )
    mouse_show_tail: BoolProperty(name="", default=True)

    # Limit to a single overlay per screen
    limit_one_per_screen: BoolProperty(
        name="",
        description="Show the overlay in only one 3D Viewport (it follows the last active viewport)",
        default=True
    )

    # Active preset name (always has a selection; 'Default' comes from items())
    active_preset: EnumProperty(
        name="",
        description="Active MoCast preset",
        items=msc_presets.preset_enum_items,
        update=msc_presets.on_active_preset_changed,
    )



class MSC_Preferences(AddonPreferences):
    # Use the real package id so Blender displays the prefs under the add-on
    bl_idname = (__package__ or __name__.split('.', 1)[0])

    # Per-addon language override (static enum; the field label is translated in draw)
    lang_override: EnumProperty(
        name="",  # label provided in draw()
        description="Override Blender’s language for MoCast labels only",
        items=[
            ("SYSTEM", "System Default", ""),
            ("en_US",  "English (US)", ""),
            ("fr_CA",  "Français (Canada)", ""),
            ("fr_FR",  "Français (France)", ""),
            ("pt_BR",  "Português (Brasil)", ""),
            ("es_ES",  "Español (España)", ""),
            ("de_DE",  "Deutsch", ""),
            ("ru_RU",  "Русский", ""),
            ("zh_CN",  "中文（简体）", ""),
        ],
        default="SYSTEM",
        update=on_lang_override_update,
    )

    def draw(self, context):
        col = self.layout.column()
        col.label(text=_("MoCast settings live in the 3D Viewport → Sidebar → MoCast."))
        col.separator()
        col.label(text=_("Language (MoCast only)"))
        col.prop(self, "lang_override", text="")


# ---------- Helpers ----------

def _find_mocast_prefs():
    """Try multiple strategies to get our add-on preferences object."""
    addons = bpy.context.preferences.addons
    candidates = []
    # 1) Package name of this module
    pkg = (__package__ or __name__.split('.', 1)[0])
    candidates.append(pkg)
    # 2) Common expected module name
    candidates.append("momentum_screencast_overlay")
    # 3) Heuristic scan
    for k in addons.keys():
        kl = k.lower()
        if "mocast" in kl or ("momentum" in kl and "cast" in kl) or ("screencast" in kl and "overlay" in kl):
            candidates.append(k)
    seen = set()
    for key in candidates:
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            return addons[key].preferences, key
        except Exception:
            pass
    return None, pkg


# ---------- Operators ----------

class MSC_OT_open_preferences(Operator):
    """Open the MoCast add-on preferences"""
    bl_idname = "momentum_screencast_overlay.open_preferences"
    bl_label = "Open MoCast Preferences"
    bl_description = "Open the MoCast add-on preferences"

    def execute(self, context):
        # Try to jump directly to this add-on in the Preferences
        pkg = (__package__ or __name__.split('.', 1)[0])
        try:
            bpy.ops.preferences.addon_show(module=pkg)
        except Exception:
            # Fallback: just switch to Add-ons tab
            try:
                context.preferences.active_section = 'ADDONS'
            except Exception:
                pass
        return {'FINISHED'}


class MSC_OT_set_icon_mode(Operator):
    """Set the branding icon mode (MoCast / Custom / None)"""
    bl_idname = "momentum_screencast_overlay.set_icon_mode"
    bl_label = "Set Icon Mode"
    bl_description = "Change which branding icon MoCast uses"

    mode: StringProperty(
        name="Mode",
        description="Icon mode to set",
        default="DEFAULT",
    )

    def execute(self, context):
        s = context.window_manager.msc_settings
        if self.mode not in {"DEFAULT", "CUSTOM", "NONE"}:
            return {'CANCELLED'}
        s.title_icon_mode = self.mode
        return {'FINISHED'}


# ---------- Panel ----------

class MSC_PT_panel(Panel):
    bl_label = _("MoCast")
    bl_idname = "MSC_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MoCast"

    def draw(self, context):
        from .msc_events import MSCState  # local import to avoid cycles
        s = context.window_manager.msc_settings
        layout = self.layout

        # Enforce always-on drag, always Shift for drag
        s.drag_enable = True
        s.drag_requires_shift = True
        s.mouse_use_custom_body = True  # always allow custom color
        # Force brand icon to use manual size (no Auto Scale)
        s.title_icon_auto = False

        # --- Header: Overlay control (Preferences moved to bottom) ---
        head = layout.box()
        row = head.row(align=True)
        row.operator(
            "momentum_screencast_overlay.toggle_overlay",
            icon="HIDE_OFF" if MSCState.running else "HIDE_ON",
            text=_("Start Overlay") if not MSCState.running else _("Stop Overlay"),
        )
        head.label(text=_("Status: Running") if MSCState.running else _("Status: Stopped"))

        # --- Branding assets (icon controls) ---
        box = layout.box()
        box.label(text=_("Branding Icon"), icon='FILE_IMAGE')
        box.use_property_split = True
        box.use_property_decorate = False
        br = box.column(align=True)

        # Mode buttons: MoCast Icon / Custom Icon / No Icon
        row = br.row(align=True)
        op = row.operator(
            "momentum_screencast_overlay.set_icon_mode",
            text=_("MoCast Icon"),
            depress=(s.title_icon_mode == "DEFAULT"),
        )
        op.mode = "DEFAULT"

        op = row.operator(
            "momentum_screencast_overlay.set_icon_mode",
            text=_("Custom Icon"),
            depress=(s.title_icon_mode == "CUSTOM"),
        )
        op.mode = "CUSTOM"

        op = row.operator(
            "momentum_screencast_overlay.set_icon_mode",
            text=_("No Icon"),
            depress=(s.title_icon_mode == "NONE"),
        )
        op.mode = "NONE"

        # Icon source controls
        if s.title_icon_mode == "DEFAULT":
            # Built-in MoCast icon selector
            br.prop(s, "title_builtin_icon", text=_("MoCast Icon"))
        elif s.title_icon_mode == "CUSTOM":
            # File path for a user-provided icon
            br.prop(s, "title_icon_path", text=_("Custom Image"))
        # If NONE: no extra controls


        # --- Text content (all editable text) ---
        box = layout.box()
        box.label(text=_("Text Content"), icon='OUTLINER_DATA_FONT')
        col_txt = box.column(align=True)
        col_txt.prop(s, "title_text", text=_("Brand Name"))
        if s.show_idle_hint:
            col_txt.prop(s, "idle_hint_text", text=_("Idle Text"))

        # --- Sizing & Geometry (all sliders for sizes/shape) ---
        box = layout.box()
        box.label(text=_("Sizing & Geometry"), icon='FULLSCREEN_ENTER')
        col_sz = box.column(align=True)
        # Text sizes
        col_sz.prop(s, "font_size", text=_("Event Font Size"))
        col_sz.prop(s, "title_font_size", text=_("Brand Font Size"))
        # Icon sizing
        col_sz.prop(s, "title_icon_size", text=_("Brand Icon Size"))
        col_sz.prop(s, "title_icon_pad", text=_("Icon Padding"))
        # Mouse glyph
        col_sz.prop(s, "mouse_glyph_size", text=_("Mouse Glyph Size"))
        col_sz.prop(s, "mouse_sidecar_gap", text=_("Sidecar Gap"))
        # Corners
        col_sz.prop(s, "corner_radius", text=_("Corner Radius"))

        # --- Color & Shading (all color + opacity + shade) ---
        box = layout.box()
        box.label(text=_("Color & Shading"), icon='COLOR')
        col_col = box.column(align=True)
        # Background
        col_col.prop(s, "bg_color", text=_("Background Color"))
        col_col.prop(s, "bg_opacity", text=_("Background Opacity"))
        # Event text
        col_col.prop(s, "text_color", text=_("Event Color"))
        # Brand
        col_col.prop(s, "title_text_color", text=_("Brand Color"))
        # Mouse glyph
        col_col.prop(s, "mouse_body_color", text=_("Mouse Body Color"))
        col_col.prop(s, "mouse_outline_shade", text=_("Glyph Outline Shade"))

        # --- Visibility & Behaviour (collapsible; includes placement & timing) ---
        vis = layout.box()
        row = vis.row()
        icon = 'TRIA_DOWN' if s.ui_show_advanced else 'TRIA_RIGHT'
        row.prop(s, "ui_show_advanced", text="", icon=icon, emboss=False)
        row.label(text=_("Visibility & Behaviour"))

        if s.ui_show_advanced:
            col = vis.column(align=True)

            # Brand
            col.label(text=_("Brand"))
            col.prop(s, "show_title", text=_("Show Branding"))

            # Events – vertical column
            col.separator()
            col.label(text=_("Events"))
            col.prop(s, "show_keys", text=_("Keys"))
            col.prop(s, "show_mouse", text=_("Mouse"))
            col.prop(s, "show_modifiers", text=_("Modifiers"))
            col.prop(s, "show_transform_axis", text=_("Axis"))

            # Mouse – vertical column
            col.separator()
            col.label(text=_("Mouse"))
            col.prop(s, "show_mouse_glyph", text=_("Show Mouse Glyph (Sidecar)"))
            col.prop(s, "mirror_mouse_lr", text=_("Flip Buttons (L↔R)"))
            col.prop(s, "mouse_show_tail", text=_("Mouse Tail"))
            col.prop(s, "mouse_hide_when_idle", text=_("Hide When Idle"))

            # Idle overlay
            col.separator()
            col.label(text=_("Idle Overlay"))
            col.prop(s, "show_idle_hint", text=_("Show Overlay When Idle"))

            # Screen behaviour (position is internal; default BOTTOM_LEFT)
            #pos_box = col.box()
            #pos_box.label(text=_("Screen Placement"))
            
            ## Removed limit_one_per_screen based on questionable outcomes
            # pos_box.prop(s, "limit_one_per_screen", text=_("Limit One/Screen"))

            # History & fade timing
            hist_box = col.box()
            hist_box.label(text=_("History / Timing"))
            hist_box.prop(s, "history_count", text=_("History Lines"))
            hist_box.prop(s, "fade_seconds", text=_("Fade Time (s)"))

        # --- Presets ---
        box = layout.box()
        box.label(text=_("Presets"), icon='PRESET')

        # Active preset dropdown (auto-loads on change)
        row = box.row(align=True)
        row.label(text=_("Active Preset:"))
        row.prop(s, "active_preset", text="")

        # Save / Delete buttons
        row = box.row(align=True)
        row.operator(
            "momentum_screencast_overlay.save_preset",
            text=_("Save Preset"),
            icon='EXPORT',
        )
        row.operator(
            "momentum_screencast_overlay.delete_preset",
            text=_("Delete Preset"),
            icon='TRASH',
        )

        from .msc_presets import preset_folder_display
        box.label(
            text=f"{_('Preset Folder:')} {preset_folder_display()}",
            icon='FILE_FOLDER',
        )

        # --- Preferences at bottom ---
        prefs_box = layout.box()
        prefs_box.label(text=_("Preferences"))
        prefs_box.operator(
            "momentum_screencast_overlay.open_preferences",
            icon='PREFERENCES',
            text=_("Open MoCast Preferences"),
        )


# ---------- Registration ----------

classes = (
    MSC_Settings,
    MSC_Preferences,
    MSC_OT_open_preferences,
    MSC_OT_set_icon_mode,
    MSC_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.msc_settings = PointerProperty(type=MSC_Settings)


def unregister():
    try:
        del bpy.types.WindowManager.msc_settings
    except Exception:
        pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
