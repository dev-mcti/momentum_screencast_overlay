## __init__.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.

bl_info = {
    "name": "MoCast – Momentum Screencast Overlay",
    "author": "Momentum Creative Technology Inc.",
    "version": (1, 0, 0),  # MoCast 1.0 Release
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > MoCast",
    "description": "Keyboard & mouse overlay for educators: keys, clicks/scroll, transform axis; customizable branding title/icon.",
    "category": "3D View",
}

# Register translations first so _() works everywhere
from . import msc_translation
from . import msc_ui, msc_presets, msc_branding, msc_mouse, msc_events

def register():
    # 1) translations
    msc_translation.register()
    # 2) everything else
    msc_ui.register()
    msc_presets.register()
    msc_branding.register()
    msc_mouse.register()
    msc_events.register()

def unregister():
    # reverse order
    msc_events.unregister()
    msc_mouse.unregister()
    msc_branding.unregister()
    msc_presets.unregister()
    msc_ui.unregister()
    # translations last
    msc_translation.unregister()

if __name__ == "__main__":
    register()
