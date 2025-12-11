# DEVELOPER_README.md
### *Internal Development Notes for the MoCast Add-On*  
(c) Momentum Creative Technology Inc.

This document is distributed as part of the MoCast Blender add-on and is
covered under the same license terms (GPL-3.0-or-later).  
It is intended for developers contributing to or maintaining the add-on.

---

# **MoCast – Developer Architecture Overview**

This document provides a high-level technical overview of how MoCast works internally.
It is intended for developers who need to maintain, extend, or debug the add-on.

For user documentation, tutorials, and walkthrough videos, see:
**https://momentumcreativetech.ca**  
**YouTube channel**

---

# **1. High-Level Concept**

MoCast is a real-time event overlay for Blender. It displays:

- Keyboard and mouse events  
- Branding block (text + icon)  
- Mouse glyph (sidecar icon)  
- Idle message  
- Transform axis hints  

It draws in screen space using Blender’s GPU API.

---

# **2. Module Responsibilities**

## `msc_ui.py`
User interface, settings properties, sidebar panel, preset buttons, branding UI.

## `msc_events.py`
Core state machine, event capture, idle detection, event formatting.

## `msc_branding.py`
Built‑in icon registry, icon loading, GPU texture caching.

## `msc_mouse.py`
Mouse glyph drawing, shading, size, mirroring logic.

## `msc_presets.py`
Preset save/load/delete logic, JSON serialization, defaults.

## `__init__.py`
Add-on registration and module integration.

---

# **3. Overlay Drawing Pipeline**

MoCast uses Blender’s GPU draw handler:

```
bpy.types.SpaceView3D.draw_handler_add(...)
```

Pipeline:

1. Collect events  
2. Update overlay state  
3. Compute screen positions  
4. Draw background, text, mouse glyph, branding, idle message  

---

# **4. Branding Icon Logic**

Modes:

- **DEFAULT** → built-in icons from `assets/icons/`
- **CUSTOM** → user file path
- **NONE** → hide icon

Textures are cached to avoid reloading.

---

# **5. Preset System**

- Default preset resets to RNA defaults  
- Save → overwrite or new  
- Delete → confirmation required  
- All settings serialized to JSON  
- Live‑load when switching presets  

---

# **6. Developer Guidelines**

- Add settings only in `MSC_Settings`  
- Keep drawing code outside UI  
- Add built-in icons to both branding and UI enums  
- Cache textures, never load in draw loop  
- Maintain “Beacon” as the first built‑in icon  
- When adding preset fields, only update serialization helpers  

---

# **7. Stability Notes**

- Blender fileselect hover crashes → avoided by design  
- FILE_PATH fields are safe  
- Always redraw safely and avoid mutating state during draw  
- Overlay must never interrupt Blender workflows  

---

# **8. Optional Future Features**

- Icon grid preview  
- Theme presets  
- Export overlay frames  
- Remote‑control API  

---

# **End of Document**
