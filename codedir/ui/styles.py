from __future__ import annotations


_BASE_STYLESHEET = """
QWidget#AppRoot {{
    background: {app_bg};
    color: {text};
    font-family: "Segoe UI", "Inter", Arial, sans-serif;
    font-size: 13px;
}}

QLabel#Title {{
    color: {title};
    font-size: 24px;
    font-weight: 700;
}}

QLabel#Subtitle {{
    color: {subtitle};
    font-size: 13px;
}}

QLabel#FieldLabel {{
    color: {field_label};
    font-weight: 600;
}}

QFrame#Panel {{
    background: {panel_bg};
    border: 1px solid {panel_border};
    border-radius: 8px;
}}

QFrame#DropZone {{
    background: {drop_bg};
    border: 2px dashed {drop_border};
    border-radius: 8px;
}}

QFrame#DropZone[dragging="true"] {{
    background: {drop_active_bg};
    border: 2px dashed {accent_soft};
}}

QTabWidget::pane {{
    border: 1px solid {panel_border};
    background: transparent;
    border-radius: 8px;
    margin-top: 8px;
}}

QTabWidget {{
    background: transparent;
}}

QTabBar {{
    background: {app_bg};
}}

QTabBar::tab-bar {{
    alignment: left;
    background: {app_bg};
}}

QTabBar::tab {{
    background: {button_bg};
    border: 1px solid {button_border};
    color: {subtitle};
    padding: 9px 16px;
    min-width: 110px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 6px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: {panel_bg};
    color: {title};
    border-color: {panel_border};
}}

QTabBar::tab:hover:!selected {{
    background: {button_hover_bg};
    color: {button_text};
    border-color: {button_hover_border};
}}

QLineEdit, QComboBox {{
    background: {input_bg};
    border: 1px solid {input_border};
    border-radius: 6px;
    color: {input_text};
    min-height: 32px;
    padding: 5px 9px;
    selection-background-color: {accent};
    selection-color: {selection_text};
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {accent_soft};
}}

QComboBox::drop-down {{
    border: 0;
    width: 28px;
}}

QComboBox QAbstractItemView {{
    background: {panel_bg};
    border: 1px solid {input_border};
    color: {text};
    selection-background-color: {selection_bg};
    selection-color: {selection_item_text};
}}

QPushButton {{
    background: {button_bg};
    border: 1px solid {button_border};
    border-radius: 6px;
    color: {button_text};
    font-weight: 600;
    min-height: 32px;
    padding: 6px 12px;
}}

QPushButton:hover {{
    background: {button_hover_bg};
    border-color: {button_hover_border};
}}

QPushButton:pressed {{
    background: {button_pressed_bg};
}}

QPushButton#PrimaryButton {{
    background: {accent};
    border-color: {accent_soft};
    color: {primary_text};
}}

QPushButton#PrimaryButton:hover {{
    background: {accent_soft};
}}

QPushButton#DangerButton {{
    background: {danger_bg};
    border-color: {danger_border};
    color: {danger_text};
}}

QCheckBox {{
    color: {checkbox_text};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {drop_border};
    background: {input_bg};
}}

QCheckBox::indicator:checked {{
    background: {accent};
    border-color: {accent_soft};
}}

QTableWidget {{
    background: {input_bg};
    alternate-background-color: {table_alt_bg};
    border: 1px solid {panel_border};
    border-radius: 8px;
    color: {text};
    gridline-color: {panel_border};
    selection-background-color: {selection_bg};
    selection-color: {selection_item_text};
}}

QHeaderView::section {{
    background: {header_bg};
    border: 0;
    border-right: 1px solid {panel_border};
    color: {field_label};
    font-weight: 700;
    min-height: 32px;
    padding: 6px;
}}

QTableCornerButton::section {{
    background: {header_bg};
    border: 0;
}}

QStatusBar {{
    background: {app_bg};
    color: {subtitle};
}}

QLabel#DropTitle {{
    color: {title};
    font-size: 18px;
    font-weight: 700;
}}

QLabel#DropSubtitle {{
    color: {subtitle};
    font-size: 11px;
}}
"""


_DARK = {
    "app_bg": "#0B0F16",
    "text": "#E8EEF8",
    "title": "#F8FAFC",
    "subtitle": "#91A0B8",
    "field_label": "#AAB6CA",
    "panel_bg": "#121821",
    "panel_border": "#263143",
    "drop_bg": "#10161F",
    "drop_border": "#3B4B63",
    "drop_active_bg": "#132D33",
    "input_bg": "#0E141D",
    "input_border": "#2C3748",
    "input_text": "#F8FAFC",
    "accent": "#14B8A6",
    "accent_soft": "#2DD4BF",
    "selection_text": "#0B0F16",
    "selection_bg": "#1F6F69",
    "selection_item_text": "#FFFFFF",
    "button_bg": "#1C2634",
    "button_border": "#344258",
    "button_text": "#F8FAFC",
    "button_hover_bg": "#273448",
    "button_hover_border": "#4B607D",
    "button_pressed_bg": "#151D28",
    "primary_text": "#04110F",
    "danger_bg": "#3A2026",
    "danger_border": "#70414C",
    "danger_text": "#FFD4DC",
    "checkbox_text": "#B8C4D8",
    "table_alt_bg": "#121A25",
    "header_bg": "#171F2B",
}


_LIGHT = {
    "app_bg": "#F3F6FB",
    "text": "#17212E",
    "title": "#0F1722",
    "subtitle": "#5F6F83",
    "field_label": "#516176",
    "panel_bg": "#FFFFFF",
    "panel_border": "#D4DEE9",
    "drop_bg": "#F8FBFF",
    "drop_border": "#A8BBCF",
    "drop_active_bg": "#E9FBF7",
    "input_bg": "#FFFFFF",
    "input_border": "#C9D4E1",
    "input_text": "#17212E",
    "accent": "#0F9D8A",
    "accent_soft": "#25B9A7",
    "selection_text": "#FFFFFF",
    "selection_bg": "#D7F5F0",
    "selection_item_text": "#103934",
    "button_bg": "#EEF3F9",
    "button_border": "#C8D4E1",
    "button_text": "#17212E",
    "button_hover_bg": "#E2EAF4",
    "button_hover_border": "#AEBFD2",
    "button_pressed_bg": "#D7E1EC",
    "primary_text": "#FFFFFF",
    "danger_bg": "#FDECEE",
    "danger_border": "#E3B8BF",
    "danger_text": "#7A2433",
    "checkbox_text": "#435468",
    "table_alt_bg": "#F8FBFF",
    "header_bg": "#EAF0F7",
}


def get_stylesheet(theme: str) -> str:
    palette = _LIGHT if theme == "light" else _DARK
    return _BASE_STYLESHEET.format(**palette)
