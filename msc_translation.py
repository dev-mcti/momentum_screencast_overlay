## msc_translation.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
# (c) Momentum Creative Technology Inc. <dev@momentumcreativetech.ca>
#
# This file is part of MoCast, a Blender add-on licensed under the
# GNU General Public License v3.0 or later (GPL-3.0-or-later).
# See the LICENSE file or https://momentumcreativetech.ca/licenses-legal for details.

import bpy

# ---------------------------------------------------------------------------
# Robust preferences lookup (works regardless of folder/package id)
# ---------------------------------------------------------------------------

def _find_mocast_prefs():
    """
    Try multiple strategies to find this add-on's preferences object.
    Returns (prefs_or_None, detected_key).
    """
    addons = bpy.context.preferences.addons
    candidates = []

    # 1) Package name for this module (e.g. "momentum_screencast_overlay")
    pkg = (__package__ or __name__.split('.', 1)[0])
    if pkg:
        candidates.append(pkg)

    # 2) Common/expected key
    candidates.append("momentum_screencast_overlay")

    # 3) Heuristic scan of all enabled add-ons
    for k in addons.keys():
        kl = k.lower()
        if ("mocast" in kl) or ("screencast" in kl and "overlay" in kl) or ("momentum" in kl and "cast" in kl):
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

    return None, pkg or "momentum_screencast_overlay"


def _get_addon_prefs():
    """
    Safely fetch MoCast add-on preferences to read the language override.
    Works whether the package name is used or the add-on idname.
    """
    prefs, _key = _find_mocast_prefs()
    return prefs


# ---------------------------------------------------------------------------
# Active locale resolver
# ---------------------------------------------------------------------------

def _active_locale():
    """
    Decide the active locale for MoCast:
      1) Use the add-on preference override if set.
      2) Else use Blender's current locale (None/'' => English fallback).
    """
    prefs = _get_addon_prefs()
    if prefs:
        override = getattr(prefs, "lang_override", "SYSTEM")
        if override and override != "SYSTEM":
            return override
    # Blender’s global UI locale ('' or None means English / untranslated)
    return getattr(bpy.app.translations, "locale", None)


# ---------------------------------------------------------------------------
# Translation function (MoCast-first, then Blender, then fallback)
# ---------------------------------------------------------------------------

def _(msgid: str) -> str:
    """
    Public translator for all MoCast UI strings.
    Resolution order:
      1) MoCast’s own table, honoring the per-addon language override.
      2) Blender’s translation tables (pgettext_iface) as a backup.
      3) Fallback: the original msgid.
    """
    loc = _active_locale()

    # 1) Our own table with explicit locale
    if loc and loc in TRANSLATIONS:
        s = TRANSLATIONS[loc].get(msgid)
        if s:
            return s

    # 2) Let Blender try (uses global language)
    try:
        return bpy.app.translations.pgettext_iface(msgid)
    except Exception:
        pass

    # 3) Fallback
    return msgid


# ---------------------------------------------------------------------------
# Live-update hook: called when the language override changes
# ---------------------------------------------------------------------------

def _tag_everything_for_redraw():
    # Tag all areas in all windows to refresh immediately
    for win in bpy.context.window_manager.windows:
        scr = win.screen
        if not scr:
            continue
        for area in scr.areas:
            try:
                area.tag_redraw()
            except Exception:
                pass

def on_lang_override_update(self, context):
    """
    Update callback for MSC_Preferences.lang_override.
    Forces a full UI redraw so translated labels update instantly.
    """
    _tag_everything_for_redraw()

    # In some cases (rare), a short deferred redraw helps propagate to all regions.
    def _deferred():
        _tag_everything_for_redraw()
        return None
    try:
        bpy.app.timers.register(_deferred, first_interval=0.05)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Translation tables
# Keep keys (msgids) IDENTICAL to the English strings used in code.
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "zh_CN": {
        # Add-on name & common UI
        "Momentum Screencast Overlay": "MoCast 叠加层",
        "Start / Stop Overlay": "启动 / 停止叠加层",
        "Start Overlay": "启动叠加层",
        "Stop Overlay": "停止叠加层",
        "Toggle the keyboard & mouse overlay in the viewport": "在视图中切换键鼠叠加层",
        "Status: Running": "状态：运行中",
        "Status: Stopped": "状态：已停止",
        "Events": "事件",
        "Other": "其他",
        "Overlay Appearance": "叠加层外观",
        "Branding": "品牌",
        "Mouse Glyph": "鼠标图标",
        "Idle / History": "空闲 / 历史",
        "Presets": "预设",
        "Advanced": "高级",
        "Show Branding": "显示品牌",
        "Brand Name": "品牌名称",
        "Brand Image": "品牌图像",
        "Default (Beacon)": "默认（灯泡）",
        "Custom": "自定义",
        "None": "无",
        "Custom Image": "自定义图像",
        "Auto Scale": "自动缩放",
        "Brand Icon Size": "图标大小",
        "Icon Padding": "图标内边距",
        "Brand Font Size": "字体大小（品牌）",
        "Brand Color": "品牌颜色",
        "Event Font Size": "事件字体大小",
        "Background Color": "背景颜色",
        "Background Opacity": "背景不透明度",
        "Event Color": "事件颜色",
        "Corner Radius": "圆角半径",
        "Position (Preset)": "位置（预设）",
        "Top Left": "左上",
        "Top Center": "上中",
        "Top Right": "右上",
        "Middle Left": "左中",
        "Center": "中心",
        "Middle Right": "右中",
        "Bottom Left": "左下",
        "Bottom Center": "下中",
        "Bottom Right": "右下",
        "History Lines": "历史行数",
        "Fade Time (s)": "淡出时间（秒）",
        "Keys": "按键",
        "Mouse": "鼠标",
        "Modifiers": "修饰键",
        "Show Overlay When Idle": "空闲时显示叠加层",
        "Idle Text": "空闲文本",
        "Axis": "轴",
        "Allow Drag (Shift)": "允许拖动（Shift）",
        "Flip Buttons (L↔R)": "翻转按键（左↔右）",
        "Position": "位置",
        "Show Mouse Glyph (Sidecar)": "显示鼠标图标（侧边）",
        "Mouse Glyph Size": "图标大小（鼠标）",
        "Sidecar Gap": "侧边间距",
        "When Idle": "空闲时",
        "Show": "显示",
        "Hide": "隐藏",
        "Hide When Idle": "空闲时隐藏",
        "Custom Body Color": "自定义机身颜色",
        "Body Color": "机身颜色",
        "Outline Shade": "轮廓亮度",
        "Show Tail": "显示尾线",
        "Mouse Tail": "鼠标尾线",
        "Save Preset": "保存预设",
        "Load Preset": "加载预设",
        "Folder:": "文件夹：",

        # NEW preset-related strings
        "Active Preset:": "当前预设：",
        "Delete Preset": "删除预设",
        "Preset Folder:": "预设文件夹：",

        # New section/label strings
        "Visibility & Behaviour": "可见性与行为",
        "Brand": "品牌",
        "Idle Overlay": "空闲叠加层",
        "Text Content": "文本内容",
        "Sizing & Geometry": "尺寸与几何",
        "Color & Shading": "颜色与阴影",
        "Branding Icon": "品牌图标",
        "Screen Placement": "屏幕位置",
        "History / Timing": "历史 / 时间",
        "Mouse Body Color": "鼠标主体颜色",
        "Glyph Outline Shade": "轮廓亮度（图标）",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "MoCast 设置位于 3D 视图 → 侧栏 → MoCast。",
        "Preferences": "首选项",
        "Open MoCast Preferences": "打开 MoCast 首选项",

        # Branding icon mode buttons
        "MoCast Icon": "MoCast 图标",
        "Custom Icon": "自定义图标",
        "No Icon": "无图标",

        # Event strings / labels
        "Left Click": "左键单击",
        "Right Click": "右键单击",
        "Middle Click": "中键单击",
        "Scroll ↑": "滚动 ↑",
        "Scroll ↓": "滚动 ↓",
        "Scroll (↑)": "滚动（↑）",
        "Scroll (↓)": "滚动（↓）",
        "Press": "按下",
        "Release": "松开",
        "Hold": "按住",
        "Drag": "拖动",
        "Shift": "Shift",
        "Ctrl": "Ctrl",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "小键盘",
        "Up Arrow": "上箭头",
        "Down Arrow": "下箭头",
        "Transform: ": "变换：",
        "Axis ": "轴 ",
        "Free": "自由",

        # Newly added common key-name strings
        "Space": "空格",
        "Tab": "Tab",
        "Esc": "Esc",
        "Enter": "回车",
        "Home": "行首",
        "End": "行尾",
        "Page Up": "向上翻页",
        "Page Down": "向下翻页",
        "Insert": "插入",
        "Delete": "删除",
        "Backspace": "退格",
        "Left Arrow": "左箭头",
        "Right Arrow": "右箭头",

        # Preferences strings
        "Open 3D Viewport → Sidebar → MoCast for settings.": "打开 3D 视图 → 侧栏 → MoCast 以进行设置。",
        "Language": "语言",
        "System Default": "系统默认",
        "Language (MoCast only)": "语言（仅 MoCast）",
        "Preferences not detected for package: ": "未检测到此包的首选项：",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "提示：以文件夹形式安装/启用插件并重新加载脚本。",
    },

    "ru_RU": {
        "Momentum Screencast Overlay": "MoCast оверлей",
        "Start / Stop Overlay": "Запуск / Остановка оверлея",
        "Start Overlay": "Запустить оверлей",
        "Stop Overlay": "Остановить оверлей",
        "Toggle the keyboard & mouse overlay in the viewport": "Переключить оверлей клавиатуры и мыши в окне просмотра",
        "Status: Running": "Статус: работает",
        "Status: Stopped": "Статус: остановлен",
        "Events": "События",
        "Other": "Другое",
        "Overlay Appearance": "Вид оверлея",
        "Branding": "Брендинг",
        "Mouse Glyph": "Значок мыши",
        "Idle / History": "Ожидание / История",
        "Presets": "Пресеты",
        "Advanced": "Расширенные",
        "Show Branding": "Показывать брендинг",
        "Brand Name": "Имя бренда",
        "Brand Image": "Изображение бренда",
        "Default (Beacon)": "По умолчанию (лампа)",
        "Custom": "Пользовательское",
        "None": "Нет",
        "Custom Image": "Собственное изображение",
        "Auto Scale": "Автомасштаб",
        "Brand Icon Size": "Размер значка",
        "Icon Padding": "Отступ значка",
        "Brand Font Size": "Размер шрифта (бренд)",
        "Brand Color": "Цвет бренда",
        "Event Font Size": "Размер шрифта (события)",
        "Background Color": "Цвет фона",
        "Background Opacity": "Непрозрачность фона",
        "Event Color": "Цвет событий",
        "Corner Radius": "Радиус скругления",
        "Position (Preset)": "Положение (пресет)",
        "Top Left": "Сверху слева",
        "Top Center": "Сверху по центру",
        "Top Right": "Сверху справа",
        "Middle Left": "По центру слева",
        "Center": "По центру",
        "Middle Right": "По центру справа",
        "Bottom Left": "Снизу слева",
        "Bottom Center": "Снизу по центру",
        "Bottom Right": "Снизу справа",
        "History Lines": "Строки истории",
        "Fade Time (s)": "Время затухания (с)",
        "Keys": "Клавиши",
        "Mouse": "Мышь",
        "Modifiers": "Модификаторы",
        "Show Overlay When Idle": "Показывать в простое",
        "Idle Text": "Текст простоя",
        "Axis": "Оси",
        "Allow Drag (Shift)": "Разрешить перетаскивание (Shift)",
        "Flip Buttons (L↔R)": "Поменять кнопки (Л↔П)",
        "Position": "Положение",
        "Show Mouse Glyph (Sidecar)": "Показывать значок мыши (сбоку)",
        "Mouse Glyph Size": "Размер значка мыши",
        "Sidecar Gap": "Отступ сбоку",
        "When Idle": "В простое",
        "Show": "Показывать",
        "Hide": "Скрывать",
        "Hide When Idle": "Скрывать в простое",
        "Custom Body Color": "Свой цвет корпуса",
        "Body Color": "Цвет корпуса",
        "Outline Shade": "Яркость контура",
        "Show Tail": "Показывать хвост",
        "Mouse Tail": "Хвост мыши",
        "Save Preset": "Сохранить пресет",
        "Load Preset": "Загрузить пресет",
        "Folder:": "Папка:",

        # NEW preset-related strings
        "Active Preset:": "Активный пресет:",
        "Delete Preset": "Удалить пресет",
        "Preset Folder:": "Папка пресетов:",

        # New section/label strings
        "Visibility & Behaviour": "Видимость и поведение",
        "Brand": "Бренд",
        "Idle Overlay": "Оверлей в простое",
        "Text Content": "Текстовое содержимое",
        "Sizing & Geometry": "Размеры и геометрия",
        "Color & Shading": "Цвет и затенение",
        "Branding Icon": "Иконка бренда",
        "Screen Placement": "Расположение на экране",
        "History / Timing": "История / время",
        "Mouse Body Color": "Цвет корпуса мыши",
        "Glyph Outline Shade": "Яркость контура значка",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "Настройки MoCast находятся в 3D-виде → Боковая панель → MoCast.",
        "Preferences": "Настройки",
        "Open MoCast Preferences": "Открыть настройки MoCast",

        # Branding icon mode buttons
        "MoCast Icon": "Значок MoCast",
        "Custom Icon": "Пользовательский значок",
        "No Icon": "Без значка",

        "Left Click": "ЛКМ",
        "Right Click": "ПКМ",
        "Middle Click": "СКМ",
        "Scroll ↑": "Прокрутка ↑",
        "Scroll ↓": "Прокрутка ↓",
        "Scroll (↑)": "Прокрутка (↑)",
        "Scroll (↓)": "Прокрутка (↓)",
        "Press": "Нажать",
        "Release": "Отпустить",
        "Hold": "Удерживать",
        "Drag": "Перетащить",
        "Shift": "Shift",
        "Ctrl": "Ctrl",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "Numpad",
        "Up Arrow": "Стрелка вверх",
        "Down Arrow": "Стрелка вниз",
        "Transform: ": "Трансформ: ",
        "Axis ": "Ось ",
        "Free": "Свободно",

        # Newly added common key-name strings
        "Space": "Пробел",
        "Tab": "Tab",
        "Esc": "Esc",
        "Enter": "Enter",
        "Home": "Home",
        "End": "End",
        "Page Up": "Страница вверх",
        "Page Down": "Страница вниз",
        "Insert": "Insert",
        "Delete": "Удалить",
        "Backspace": "Backspace",
        "Left Arrow": "Стрелка влево",
        "Right Arrow": "Стрелка вправо",

        "Open 3D Viewport → Sidebar → MoCast for settings.": "Откройте 3D-вид → Боковая панель → MoCast для настроек.",
        "Language": "Язык",
        "System Default": "Системный",
        "Language (MoCast only)": "Язык (только MoCast)",
        "Preferences not detected for package: ": "Не найдены настройки для пакета: ",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "Подсказка: установите/включите аддон папкой и перезагрузите скрипты.",
    },

    "de_DE": {
        "Momentum Screencast Overlay": "MoCast-Overlay",
        "Start / Stop Overlay": "Overlay starten / stoppen",
        "Start Overlay": "Overlay starten",
        "Stop Overlay": "Overlay stoppen",
        "Toggle the keyboard & mouse overlay in the viewport": "Tastatur-/Maus-Overlay im Viewport umschalten",
        "Status: Running": "Status: aktiv",
        "Status: Stopped": "Status: gestoppt",
        "Events": "Ereignnisse",
        "Other": "Sonstiges",
        "Overlay Appearance": "Overlay-Design",
        "Branding": "Branding",
        "Mouse Glyph": "Maus-Symbol",
        "Idle / History": "Leerlauf / Verlauf",
        "Presets": "Voreinstellungen",
        "Advanced": "Erweitert",
        "Show Branding": "Branding anzeigen",
        "Brand Name": "Markenname",
        "Brand Image": "Markenbild",
        "Default (Beacon)": "Standard (Lampe)",
        "Custom": "Benutzerdefiniert",
        "None": "Keins",
        "Custom Image": "Eigenes Bild",
        "Auto Scale": "Auto-Skalierung",
        "Brand Icon Size": "Symbolgröße",
        "Icon Padding": "Symbol-Abstand",
        "Brand Font Size": "Schriftgröße (Branding)",
        "Brand Color": "Markenfarbe",
        "Event Font Size": "Schriftgröße (Ereignisse)",
        "Background Color": "Hintergrundfarbe",
        "Background Opacity": "Hintergrund-Deckkraft",
        "Event Color": "Ereignisfarbe",
        "Corner Radius": "Eckenradius",
        "Position (Preset)": "Position (Voreinstellung)",
        "Top Left": "Oben links",
        "Top Center": "Oben zentriert",
        "Top Right": "Oben rechts",
        "Middle Left": "Mitte links",
        "Center": "Mitte",
        "Middle Right": "Mitte rechts",
        "Bottom Left": "Unten links",
        "Bottom Center": "Unten zentriert",
        "Bottom Right": "Unten rechts",
        "History Lines": "Verlaufszeilen",
        "Fade Time (s)": "Ausblendzeit (s)",
        "Keys": "Tasten",
        "Mouse": "Maus",
        "Modifiers": "Modifier",
        "Show Overlay When Idle": "Im Leerlauf anzeigen",
        "Idle Text": "Leerlauftext",
        "Axis": "Achsen",
        "Allow Drag (Shift)": "Ziehen erlauben (Shift)",
        "Flip Buttons (L↔R)": "Tasten tauschen (L↔R)",
        "Position": "Position",
        "Show Mouse Glyph (Sidecar)": "Maus-Symbol anzeigen (Seitlich)",
        "Mouse Glyph Size": "Symbolgröße (Maus)",
        "Sidecar Gap": "Seitlicher Abstand",
        "When Idle": "Im Leerlauf",
        "Show": "Anzeigen",
        "Hide": "Ausblenden",
        "Hide When Idle": "Im Leerlauf ausblenden",
        "Custom Body Color": "Eigene Gehäusefarbe",
        "Body Color": "Gehäusefarbe",
        "Outline Shade": "Konturhelligkeit",
        "Show Tail": "Schweif anzeigen",
        "Mouse Tail": "Maus-Schweif",
        "Save Preset": "Voreinstellung speichern",
        "Load Preset": "Voreinstellung laden",
        "Folder:": "Ordner:",

        # NEW preset-related strings
        "Active Preset:": "Aktive Voreinstellung:",
        "Delete Preset": "Voreinstellung löschen",
        "Preset Folder:": "Voreinstellungsordner:",

        # New section/label strings
        "Visibility & Behaviour": "Sichtbarkeit & Verhalten",
        "Brand": "Marke",
        "Idle Overlay": "Overlay im Leerlauf",
        "Text Content": "Textinhalt",
        "Sizing & Geometry": "Größe & Geometrie",
        "Color & Shading": "Farbe & Schattierung",
        "Branding Icon": "Branding-Symbol",
        "Screen Placement": "Bildschirmposition",
        "History / Timing": "Verlauf / Timing",
        "Mouse Body Color": "Farbe des Mausgehäuses",
        "Glyph Outline Shade": "Konturhelligkeit des Symbols",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "MoCast-Einstellungen findest du in der 3D-Ansicht → Seitenleiste → MoCast.",
        "Preferences": "Einstellungen",
        "Open MoCast Preferences": "MoCast-Einstellungen öffnen",

        # Branding icon mode buttons
        "MoCast Icon": "MoCast-Symbol",
        "Custom Icon": "Benutzerdefiniertes Symbol",
        "No Icon": "Kein Symbol",

        "Left Click": "Linksklick",
        "Right Click": "Rechtsklick",
        "Middle Click": "Mittelklick",
        "Scroll ↑": "Scrollen ↑",
        "Scroll ↓": "Scrollen ↓",
        "Scroll (↑)": "Scrollen (↑)",
        "Scroll (↓)": "Scrollen (↓)",
        "Press": "Drücken",
        "Release": "Loslassen",
        "Hold": "Halten",
        "Drag": "Ziehen",
        "Shift": "Shift",
        "Ctrl": "Strg",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "Numblock",
        "Up Arrow": "Pfeил nach oben",
        "Down Arrow": "Pfeил nach unten",
        "Transform: ": "Transformieren: ",
        "Axis ": "Achse ",
        "Free": "Frei",

        # Newly added common key-name strings
        "Space": "Leertaste",
        "Tab": "Tab",
        "Esc": "Esc",
        "Enter": "Eingabe",
        "Home": "Pos1",
        "End": "Ende",
        "Page Up": "Bild auf",
        "Page Down": "Bild ab",
        "Insert": "Einfügen",
        "Delete": "Entfernen",
        "Backspace": "Rücktaste",
        "Left Arrow": "Pfeil nach links",
        "Right Arrow": "Pfeil nach rechts",

        "Open 3D Viewport → Sidebar → MoCast for settings.": "3D-Viewport öffnen → Seitenleiste → MoCast für Einstellungen.",
        "Language": "Sprache",
        "System Default": "Systemstandard",
        "Language (MoCast only)": "Sprache (nur MoCast)",
        "Preferences not detected for package: ": "Einstellungen für Paket nicht gefunden: ",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "Tipp: Add-on als Ordner installieren/aktivieren und Skripte neu laden.",
    },

    "es_ES": {
        "Momentum Screencast Overlay": "Overlay MoCast",
        "Start / Stop Overlay": "Iniciar / Detener Overlay",
        "Start Overlay": "Iniciar overlay",
        "Stop Overlay": "Detener overlay",
        "Toggle the keyboard & mouse overlay in the viewport": "Alternar el overlay de teclado y ratón en el visor",
        "Status: Running": "Estado: en ejecución",
        "Status: Stopped": "Estado: detenido",
        "Events": "Eventos",
        "Other": "Otros",
        "Overlay Appearance": "Apariencia del overlay",
        "Branding": "Identidad",
        "Mouse Glyph": "Ícono de ratón",
        "Idle / History": "Inactividad / Historial",
        "Presets": "Preajustes",
        "Advanced": "Avanzado",
        "Show Branding": "Mostrar identidad",
        "Brand Name": "Nombre de marca",
        "Brand Image": "Imagen de marca",
        "Default (Beacon)": "Predeterminado (bombilla)",
        "Custom": "Personalizado",
        "None": "Ninguno",
        "Custom Image": "Imagen personalizada",
        "Auto Scale": "Escala automática",
        "Brand Icon Size": "Tamaño del ícono",
        "Icon Padding": "Relleno del ícono",
        "Brand Font Size": "Tamaño de fuente (marca)",
        "Brand Color": "Color de marca",
        "Event Font Size": "Tamaño de fuente (eventos)",
        "Background Color": "Color de fondo",
        "Background Opacity": "Opacidad del fondo",
        "Event Color": "Color de eventos",
        "Corner Radius": "Radio de esquina",
        "Position (Preset)": "Posición (preajuste)",
        "Top Left": "Arriba izquierda",
        "Top Center": "Arriba centro",
        "Top Right": "Arriba derecha",
        "Middle Left": "Centro izquierda",
        "Center": "Centro",
        "Middle Right": "Centro derecha",
        "Bottom Left": "Abajo izquierda",
        "Bottom Center": "Abajo centro",
        "Bottom Right": "Abajo derecha",
        "History Lines": "Líneas de historial",
        "Fade Time (s)": "Tiempo de desvanecimiento (s)",
        "Keys": "Teclas",
        "Mouse": "Ratón",
        "Modifiers": "Modificadores",
        "Show Overlay When Idle": "Mostrar en inactividad",
        "Idle Text": "Texto en inactividad",
        "Axis": "Ejes",
        "Allow Drag (Shift)": "Permitir arrastrar (Shift)",
        "Flip Buttons (L↔R)": "Invertir botones (I↔D)",
        "Position": "Posición",
        "Show Mouse Glyph (Sidecar)": "Mostrar ícono de ratón (lateral)",
        "Mouse Glyph Size": "Tamaño del ícono (ratón)",
        "Sidecar Gap": "Separación lateral",
        "When Idle": "En inactividad",
        "Show": "Mostrar",
        "Hide": "Ocultar",
        "Hide When Idle": "Ocultar en inactividad",
        "Custom Body Color": "Color del cuerpo personalizado",
        "Body Color": "Color del cuerpo",
        "Outline Shade": "Brillo del contorno",
        "Show Tail": "Mostrar cola",
        "Mouse Tail": "Cola del ratón",
        "Save Preset": "Guardar preajuste",
        "Load Preset": "Cargar preajuste",
        "Folder:": "Carpeta:",

        # NEW preset-related strings
        "Active Preset:": "Preajuste activo:",
        "Delete Preset": "Eliminar preajuste",
        "Preset Folder:": "Carpeta de preajustes:",

        # New section/label strings
        "Visibility & Behaviour": "Visibilidad y comportamiento",
        "Brand": "Marca",
        "Idle Overlay": "Overlay en inactividad",
        "Text Content": "Contenido de texto",
        "Sizing & Geometry": "Tamaño y geometría",
        "Color & Shading": "Color y sombreado",
        "Branding Icon": "Ícono de marca",
        "Screen Placement": "Ubicación en pantalla",
        "History / Timing": "Historial / tiempo",
        "Mouse Body Color": "Color del cuerpo del ratón",
        "Glyph Outline Shade": "Brillo del contorno del ícono",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "Los ajustes de MoCast están en el visor 3D → Barra lateral → MoCast.",
        "Preferences": "Preferencias",
        "Open MoCast Preferences": "Abrir preferencias de MoCast",

        # Branding icon mode buttons
        "MoCast Icon": "Ícono MoCast",
        "Custom Icon": "Ícono personalizado",
        "No Icon": "Sin ícono",

        "Left Click": "Clic izquierdo",
        "Right Click": "Clic derecho",
        "Middle Click": "Clic central",
        "Scroll ↑": "Desplazar ↑",
        "Scroll ↓": "Desplazar ↓",
        "Scroll (↑)": "Desplazar (↑)",
        "Scroll (↓)": "Desplazar (↓)",
        "Press": "Pulsar",
        "Release": "Soltar",
        "Hold": "Mantener",
        "Drag": "Arrastrar",
        "Shift": "Shift",
        "Ctrl": "Ctrl",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "Teclado num.",
        "Up Arrow": "Flecha arriba",
        "Down Arrow": "Flecha abajo",
        "Transform: ": "Transformar: ",
        "Axis ": "Eje ",
        "Free": "Libre",

        # Newly added common key-name strings
        "Space": "Espacio",
        "Tab": "Tab",
        "Esc": "Esc",
        "Enter": "Intro",
        "Home": "Inicio",
        "End": "Fin",
        "Page Up": "Re Pág",
        "Page Down": "Av Pág",
        "Insert": "Insertar",
        "Delete": "Supr",
        "Backspace": "Retroceso",
        "Left Arrow": "Flecha izquierda",
        "Right Arrow": "Flecha derecha",

        "Open 3D Viewport → Sidebar → MoCast for settings.": "Abrir visor 3D → Barra lateral → MoCast para configuración.",
        "Language": "Idioma",
        "System Default": "Predeterminado del sistema",
        "Language (MoCast only)": "Idioma (solo MoCast)",
        "Preferences not detected for package: ": "No se detectaron preferencias para el paquete: ",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "Consejo: instala/habilita el complemento como carpeta y recarga los scripts.",
    },

    "pt_BR": {
        "Momentum Screencast Overlay": "Overlay MoCast",
        "Start / Stop Overlay": "Iniciar / Parar Overlay",
        "Start Overlay": "Iniciar overlay",
        "Stop Overlay": "Parar overlay",
        "Toggle the keyboard & mouse overlay in the viewport": "Alternar o overlay de teclado e mouse no visor",
        "Status: Running": "Status: em execução",
        "Status: Stopped": "Status: parado",
        "Events": "Eventos",
        "Other": "Outros",
        "Overlay Appearance": "Aparência do overlay",
        "Branding": "Identidade",
        "Mouse Glyph": "Ícone do mouse",
        "Idle / History": "Ocioso / Histórico",
        "Presets": "Predefinições",
        "Advanced": "Avançado",
        "Show Branding": "Mostrar identidade",
        "Brand Name": "Nome da marca",
        "Brand Image": "Imagem da marca",
        "Default (Beacon)": "Padrão (lâmpada)",
        "Custom": "Personalizado",
        "None": "Nenhum",
        "Custom Image": "Imagem personalizada",
        "Auto Scale": "Escala automática",
        "Brand Icon Size": "Tamanho do ícone",
        "Icon Padding": "Espaçamento do ícone",
        "Brand Font Size": "Tamanho da fonte (marca)",
        "Brand Color": "Cor da marca",
        "Event Font Size": "Tamanho da fonte (eventos)",
        "Background Color": "Cor de fundo",
        "Background Opacity": "Opacidade do fundo",
        "Event Color": "Cor de eventos",
        "Corner Radius": "Raio do canto",
        "Position (Preset)": "Posição (predefinida)",
        "Top Left": "Superior esquerdo",
        "Top Center": "Superior central",
        "Top Right": "Superior direito",
        "Middle Left": "Meio esquerdo",
        "Center": "Centro",
        "Middle Right": "Meio direito",
        "Bottom Left": "Inferior esquerdo",
        "Bottom Center": "Inferior central",
        "Bottom Right": "Inferior direito",
        "History Lines": "Linhas de histórico",
        "Fade Time (s)": "Tempo de desvanecimento (s)",
        "Keys": "Teclas",
        "Mouse": "Mouse",
        "Modifiers": "Modificadores",
        "Show Overlay When Idle": "Mostrar em repouso",
        "Idle Text": "Texto em repouso",
        "Axis": "Eixos",
        "Allow Drag (Shift)": "Permitir arrastar (Shift)",
        "Flip Buttons (L↔R)": "Inverter botões (E↔D)",
        "Position": "Posição",
        "Show Mouse Glyph (Sidecar)": "Mostrar ícone do mouse (lateral)",
        "Mouse Glyph Size": "Tamanho do ícone (mouse)",
        "Sidecar Gap": "Espaço lateral",
        "When Idle": "Em repouso",
        "Show": "Mostrar",
        "Hide": "Ocultar",
        "Hide When Idle": "Ocultar em repouso",
        "Custom Body Color": "Cor do corpo personalizada",
        "Body Color": "Cor do corpo",
        "Outline Shade": "Brilho do contorno",
        "Show Tail": "Mostrar cauda",
        "Mouse Tail": "Cauda do mouse",
        "Save Preset": "Salvar predefinição",
        "Load Preset": "Carregar predefinição",
        "Folder:": "Pasta:",

        # NEW preset-related strings
        "Active Preset:": "Predefinição ativa:",
        "Delete Preset": "Excluir predefinição",
        "Preset Folder:": "Pasta de predefinições:",

        # New section/label strings
        "Visibility & Behaviour": "Visibilidade e comportamento",
        "Brand": "Marca",
        "Idle Overlay": "Overlay em repouso",
        "Text Content": "Conteúdo de texto",
        "Sizing & Geometry": "Tamanho e geometria",
        "Color & Shading": "Cor e sombreamento",
        "Branding Icon": "Ícone de marca",
        "Screen Placement": "Posição na tela",
        "History / Timing": "Histórico / tempo",
        "Mouse Body Color": "Cor do corpo do mouse",
        "Glyph Outline Shade": "Brilho do contorno do ícone",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "As configurações do MoCast ficam em Visor 3D → Barra lateral → MoCast.",
        "Preferences": "Preferências",
        "Open MoCast Preferences": "Abrir preferências do MoCast",

        # Branding icon mode buttons
        "MoCast Icon": "Ícone MoCast",
        "Custom Icon": "Ícone personalizado",
        "No Icon": "Sem ícone",

        "Left Click": "Clique esquerdo",
        "Right Click": "Clique direito",
        "Middle Click": "Clique do meio",
        "Scroll ↑": "Rolar ↑",
        "Scroll ↓": "Rolar ↓",
        "Scroll (↑)": "Rolar (↑)",
        "Scroll (↓)": "Rolar (↓)",
        "Press": "Pressionar",
        "Release": "Soltar",
        "Hold": "Manter",
        "Drag": "Arrastar",
        "Shift": "Shift",
        "Ctrl": "Ctrl",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "Teclado numérico",
        "Up Arrow": "Seta para cima",
        "Down Arrow": "Seta para baixo",
        "Transform: ": "Transformar: ",
        "Axis ": "Eixo ",
        "Free": "Livre",

        # Newly added common key-name strings
        "Space": "Barra de espaço",
        "Tab": "Tab",
        "Esc": "Esc",
        "Enter": "Enter",
        "Home": "Início",
        "End": "Fim",
        "Page Up": "Page Up",
        "Page Down": "Page Down",
        "Insert": "Insert",
        "Delete": "Excluir",
        "Backspace": "Backspace",
        "Left Arrow": "Seta para a esquerda",
        "Right Arrow": "Seta para a direita",

        "Open 3D Viewport → Sidebar → MoCast for settings.": "Abrir visor 3D → Barra lateral → MoCast para configurações.",
        "Language": "Idioma",
        "System Default": "Padrão do sistema",
        "Language (MoCast only)": "Idioma (apenas MoCast)",
        "Preferences not detected for package: ": "Preferências não detectadas para o pacote: ",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "Dica: instale/habilite o add-on como pasta e recarregue os scripts.",
    },

    "fr_CA": {
        "Momentum Screencast Overlay": "Overlay MoCast",
        "Start / Stop Overlay": "Démarrer / Arrêter l’overlay",
        "Start Overlay": "Démarrer l’overlay",
        "Stop Overlay": "Arrêter l’overlay",
        "Toggle the keyboard & mouse overlay in the viewport": "Basculer l’overlay clavier-souris dans la vue 3D",
        "Status: Running": "Statut : en marche",
        "Status: Stopped": "Statut : arrêté",
        "Events": "Événements",
        "Other": "Autre",
        "Overlay Appearance": "Apparence de l’overlay",
        "Branding": "Image de marque",
        "Mouse Glyph": "Icône de souris",
        "Idle / History": "Inactivité / Historique",
        "Presets": "Préréglages",
        "Advanced": "Avancé",
        "Show Branding": "Afficher la marque",
        "Brand Name": "Nom de marque",
        "Brand Image": "Image de marque",
        "Default (Beacon)": "Par défaut (ampoule)",
        "Custom": "Personnalisé",
        "None": "Aucun",
        "Custom Image": "Image personnalisée",
        "Auto Scale": "Échelle automatique",
        "Brand Icon Size": "Taille de l’icône",
        "Icon Padding": "Marge de l’icône",
        "Brand Font Size": "Taille de police (marque)",
        "Brand Color": "Couleur de marque",
        "Event Font Size": "Taille de police (événements)",
        "Background Color": "Couleur d’arrière-plan",
        "Background Opacity": "Opacité d’arrière-plan",
        "Event Color": "Couleur des événements",
        "Corner Radius": "Rayon d’angle",
        "Position (Preset)": "Position (préréglée)",
        "Top Left": "Haut gauche",
        "Top Center": "Haut centre",
        "Top Right": "Haut droite",
        "Middle Left": "Milieu gauche",
        "Center": "Centre",
        "Middle Right": "Milieu droite",
        "Bottom Left": "Bas gauche",
        "Bottom Center": "Bas centre",
        "Bottom Right": "Bas droite",
        "History Lines": "Lignes d’historique",
        "Fade Time (s)": "Temps de fondu (s)",
        "Keys": "Touches",
        "Mouse": "Souris",
        "Modifiers": "Modificateurs",
        "Show Overlay When Idle": "Afficher à l’inactivité",
        "Idle Text": "Texte d’inactivité",
        "Axis": "Axes",
        "Allow Drag (Shift)": "Autoriser le glisser (Shift)",
        "Flip Buttons (L↔R)": "Inverser les boutons (G↔D)",
        "Position": "Position",
        "Show Mouse Glyph (Sidecar)": "Afficher l’icône de souris (latéral)",
        "Mouse Glyph Size": "Taille de l’icône (souris)",
        "Sidecar Gap": "Écart latéral",
        "When Idle": "À l’inactivité",
        "Show": "Afficher",
        "Hide": "Masquer",
        "Hide When Idle": "Masquer à l’inactivité",
        "Custom Body Color": "Couleur du corps personnalisée",
        "Body Color": "Couleur du corps",
        "Outline Shade": "Luminosité du contour",
        "Show Tail": "Afficher la traîne",
        "Mouse Tail": "Traîne de souris",
        "Save Preset": "Enregistrer le préréglage",
        "Load Preset": "Charger le préréglage",
        "Folder:": "Dossier :",

        # NEW preset-related strings
        "Active Preset:": "Préréglage actif :",
        "Delete Preset": "Supprimer le préréglage",
        "Preset Folder:": "Dossier des préréglages :",

        # New section/label strings
        "Visibility & Behaviour": "Visibilité et comportement",
        "Brand": "Marque",
        "Idle Overlay": "Overlay d’inactivité",
        "Text Content": "Contenu textuel",
        "Sizing & Geometry": "Taille et géométrie",
        "Color & Shading": "Couleur et ombrage",
        "Branding Icon": "Icône de marque",
        "Screen Placement": "Position à l’écran",
        "History / Timing": "Historique / durée",
        "Mouse Body Color": "Couleur du corps de la souris",
        "Glyph Outline Shade": "Luminosité du contour du glyphe",
        "MoCast settings live in the 3D Viewport → Sidebar → MoCast.": "Les réglages de MoCast se trouvent dans la Vue 3D → Barre latérale → MoCast.",
        "Preferences": "Préférences",
        "Open MoCast Preferences": "Ouvrir les préférences MoCast",

        # Branding icon mode buttons
        "MoCast Icon": "Icône MoCast",
        "Custom Icon": "Icône personnalisée",
        "No Icon": "Aucune icône",

        "Left Click": "Clic gauche",
        "Right Click": "Clic droit",
        "Middle Click": "Clic central",
        "Scroll ↑": "Défiler ↑",
        "Scroll ↓": "Défiler ↓",
        "Scroll (↑)": "Défiler (↑)",
        "Scroll (↓)": "Défiler (↓)",
        "Press": "Appuyer",
        "Release": "Relâcher",
        "Hold": "Maintenir",
        "Drag": "Glisser",
        "Shift": "Maj",
        "Ctrl": "Ctrl",
        "Alt": "Alt",
        "Cmd": "Cmd",
        "Win": "Win",
        "Numpad": "Pavé num.",
        "Up Arrow": "Flèche haut",
        "Down Arrow": "Flèche bas",
        "Transform: ": "Transformer : ",
        "Axis ": "Axe ",
        "Free": "Libre",

        # Newly added common key-name strings
        "Space": "Espace",
        "Tab": "Tab",
        "Esc": "Échap",
        "Enter": "Entrée",
        "Home": "Début",
        "End": "Fin",
        "Page Up": "Page préc.",
        "Page Down": "Page suiv.",
        "Insert": "Insérer",
        "Delete": "Suppr",
        "Backspace": "Retour arrière",
        "Left Arrow": "Flèche gauche",
        "Right Arrow": "Flèche droite",

        "Open 3D Viewport → Sidebar → MoCast for settings.": "Ouvrir la Vue 3D → Barre latérale → MoCast pour les réglages.",
        "Language": "Langue",
        "System Default": "Valeur système",
        "Language (MoCast only)": "Langue (MoCast seulement)",
        "Preferences not detected for package: ": "Préférences non détectées pour le paquet : ",
        "Tip: Install/enable the add-on as a folder and reload scripts.": "Astuce : installe/active l’add-on en dossier et recharge les scripts.",
    },
}

# Alias generic French to Canadian French for now
TRANSLATIONS["fr_FR"] = TRANSLATIONS["fr_CA"]

# ---------------------------------------------------------------------------
# Blender registration (registering our catalog is optional for _(), but harmless)
# ---------------------------------------------------------------------------

def register():
    try:
        bpy.app.translations.register(__name__, TRANSLATIONS)
    except Exception:
        pass

def unregister():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
