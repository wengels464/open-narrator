from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QPushButton, QLabel, QProgressBar, QLineEdit
from PySide6.QtCore import Qt, Signal

class ChapterList(QWidget):
    selection_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with controls
        header_layout = QHBoxLayout()
        self.title = QLabel("Chapters")
        self.title.setObjectName("Subheading")
        header_layout.addWidget(self.title)
        
        header_layout.addStretch()
        
        # Select All button with checkmark icon
        self.btn_all = QPushButton("☑ All")
        self.btn_all.setObjectName("SecondaryButton")
        self.btn_all.setFixedSize(60, 26)
        self.btn_all.setToolTip("Select all chapters")
        self.btn_all.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 2px 6px;
            }
        """)
        self.btn_all.clicked.connect(self.select_all)
        
        # Deselect All button with X icon
        self.btn_none = QPushButton("☐ None")
        self.btn_none.setObjectName("SecondaryButton")
        self.btn_none.setFixedSize(65, 26)
        self.btn_none.setToolTip("Deselect all chapters")
        self.btn_none.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: bold;
                padding: 2px 6px;
            }
        """)
        self.btn_none.clicked.connect(self.select_none)

        header_layout.addWidget(self.btn_all)
        header_layout.addWidget(self.btn_none)
        
        layout.addLayout(header_layout)

        # List Widget
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def set_chapters(self, chapters):
        self.list_widget.clear()
        for chapter in chapters:
            item = QListWidgetItem()
            
            # Create widget for item
            widget = QWidget()
            widget.setAttribute(Qt.WA_TranslucentBackground)
            widget.setStyleSheet("background-color: transparent;")
            
            w_layout = QHBoxLayout(widget)
            w_layout.setContentsMargins(5, 5, 5, 5)
            
            checkbox = QCheckBox()
            checkbox.setChecked(not chapter.is_toc) # Default: check everything except TOC
            checkbox.stateChanged.connect(lambda: self.selection_changed.emit())
            # Style the checkbox indicator
            checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 1px solid #3e3e42;
                    border-radius: 3px;
                    background: #252526;
                }
                QCheckBox::indicator:checked {
                    background: #007acc;
                    border-color: #007acc;
                }
            """)
            
            # Store chapter data on checkbox for easy retrieval
            checkbox.chapter_data = chapter
            
            # Editable Title
            title_edit = QLineEdit(chapter.title)
            title_edit.setStyleSheet("""
                QLineEdit {
                    color: #ffffff;
                    background-color: transparent;
                    border: 1px solid transparent;
                    font-size: 13px;
                    padding: 2px;
                }
                QLineEdit:focus {
                    background-color: #252526;
                    border: 1px solid #007acc;
                }
            """)
            if chapter.is_toc:
                title_edit.setStyleSheet(title_edit.styleSheet() + "color: #888888; font-style: italic;")
                
            # Connect text changed to update chapter title
            title_edit.textChanged.connect(lambda text, c=chapter: setattr(c, 'title', text))
            
            w_layout.addWidget(checkbox)
            w_layout.addWidget(title_edit, stretch=1)
            
            # Add character count
            count_label = QLabel(f"{len(chapter.content)} chars")
            count_label.setStyleSheet("color: #aaaaaa; font-size: 11px; background-color: transparent;")
            w_layout.addWidget(count_label)
            
            # Fix for squished text: Ensure widget has enough height
            widget.setMinimumHeight(40)
            
            # Add some padding to the size hint to prevent cutoff
            size = widget.sizeHint()
            size.setHeight(max(40, size.height() + 10))
            item.setSizeHint(size)
            
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    # Progress methods removed as per user request

    def get_selected_chapters(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            checkbox = widget.findChild(QCheckBox)
            if checkbox.isChecked():
                selected.append(checkbox.chapter_data)
        return selected

    def select_all(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            checkbox = widget.findChild(QCheckBox)
            checkbox.setChecked(True)

    def select_none(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            checkbox = widget.findChild(QCheckBox)
            checkbox.setChecked(False)
