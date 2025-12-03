# Modern Dark Theme Colors
COLORS = {
    "background": "#1e1e1e",
    "surface": "#252526",
    "surface_hover": "#2a2d2e",
    "primary": "#007acc",
    "primary_hover": "#0098ff",
    "text": "#cccccc",
    "text_dim": "#858585",
    "border": "#3e3e42",
    "success": "#4ec9b0",
    "error": "#f44747",
    "warning": "#cca700"
}

# Main Stylesheet
DARK_THEME = f"""
QMainWindow {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
}}

QWidget {{
    background-color: {COLORS['background']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}}

/* Headings */
QLabel#Heading {{
    font-size: 24px;
    font-weight: bold;
    color: {COLORS['text']};
    margin-bottom: 10px;
}}

QLabel#Subheading {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS['text']};
    margin-top: 10px;
    margin-bottom: 5px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary']};
}}

QPushButton:disabled {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_dim']};
}}

/* Secondary Button */
QPushButton#SecondaryButton {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text']};
}}

QPushButton#SecondaryButton:hover {{
    background-color: {COLORS['surface_hover']};
    border-color: {COLORS['text_dim']};
}}

/* Inputs */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text']};
    padding: 6px;
    border-radius: 4px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {COLORS['primary']};
}}

/* List Widget */
QListWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['background']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['surface_hover']};
    color: {COLORS['text']};
}}

QListWidget::item:hover {{
    background-color: {COLORS['surface_hover']};
}}

/* Progress Bar */
QProgressBar {{
    border: none;
    background-color: {COLORS['surface']};
    border-radius: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 4px;
}}

/* Scrollbar */
QScrollBar:vertical {{
    border: none;
    background: {COLORS['background']};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

/* Custom Widgets */
QWidget#DropZone {{
    background-color: {COLORS['surface']};
    border: 2px dashed {COLORS['border']};
    border-radius: 8px;
}}

QWidget#DropZone:hover {{
    border-color: {COLORS['primary']};
    background-color: {COLORS['surface_hover']};
}}

QTextEdit#LogArea {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}
"""
