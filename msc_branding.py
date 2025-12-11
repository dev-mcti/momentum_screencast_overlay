## msc_branding.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.


import os, bpy, gpu
from gpu_extras.batch import batch_for_shader

# Root + icon directories
_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
_ICON_DIR = os.path.join(_ADDON_DIR, "assets", "icons")

# Map symbolic names to filenames inside assets/icons
_BUILTIN_ICON_FILES = {
    "BEACON":        "MCT_Beacon_512.png",
    "CURSOR":        "msc_Cursor.png",
    "KEYCAP":        "msc_Keycap.png",
    "ANIMATION":     "msc_Animation.png",
    "BRUSH_STROKE":  "msc_Brush Stroke.png",
    "CURVE":         "msc_Curve.png",
    "LOWPOLY_CUBE":  "msc_Low-Poly Cube.png",
    "CAMERA_1":      "msc_Camera Icon_1.png",
    "CAMERA_2":      "msc_Camera Icon_2.png",
    "RENDER_1":      "msc_Render _1.png",
    "RENDER_2":      "msc_Render _2.png",
    "PARTICLE_1":    "msc_Particle Burst_1.png",
    "PARTICLE_2":    "msc_Particle Burst_2.png",
    "PULSE":         "msc_pulse.png",
    "NODE_COLOR":    "msc_Colorful Node.png",
    "RIGGING_COLOR": "msc_Colorful_Rigging.png",
    "PRISM_1":       "msc_Prism Icon_1.png",
    "PRISM_2":       "msc_Prism Icon_2.png",
}

# Local cache (module-level, independent of MSCState)
_ICON_IMAGE = None
_ICON_TEX = None
_ICON_PATH = None

def addon_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def builtin_icon_path(name: str) -> str:
    """
    Resolve a built-in icon id (e.g. 'BEACON', 'CAMERA_1') to a full path
    inside assets/icons. Falls back to the Beacon if unknown.
    """
    key = (name or "BEACON").upper()
    filename = _BUILTIN_ICON_FILES.get(key) or _BUILTIN_ICON_FILES["BEACON"]
    return os.path.join(_ICON_DIR, filename)


def default_icon_path() -> str:
    """Existing API: return the default Beacon icon path."""
    return builtin_icon_path("BEACON")


def ensure_icon_loaded(path: str):
    global _ICON_IMAGE, _ICON_TEX, _ICON_PATH
    if not path:
        _ICON_IMAGE = None; _ICON_TEX = None; _ICON_PATH = None; return
    if _ICON_PATH == path and _ICON_TEX:
        return
    try:
        abspath = bpy.path.abspath(path)
        img = next((im for im in bpy.data.images if bpy.path.abspath(getattr(im, "filepath","")) == abspath), None)
        if not img:
            img = bpy.data.images.load(abspath, check_existing=True)
        if _ICON_TEX:
            try: _ICON_TEX.free()
            except: pass
        _ICON_TEX = gpu.texture.from_image(img)
        _ICON_IMAGE = img
        _ICON_PATH = path
    except Exception:
        _ICON_IMAGE = None; _ICON_TEX = None; _ICON_PATH = None

def draw_image_icon(x:int, y:int, size:int):
    tex = _ICON_TEX
    if not tex: return
    shader=gpu.shader.from_builtin("IMAGE")
    coords=[(x,y),(x+size,y),(x+size,y+size),(x,y),(x+size,y+size),(x,y+size)]
    uvs=[(0,0),(1,0),(1,1),(0,0),(1,1),(0,1)]
    batch=batch_for_shader(shader,"TRIS",{"pos":coords,"texCoord":uvs})
    gpu.state.blend_set("ALPHA"); shader.bind(); shader.uniform_sampler("image",tex); batch.draw(shader); gpu.state.blend_set("NONE")

def register(): pass
def unregister(): pass
