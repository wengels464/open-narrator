from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QCheckBox, QHBoxLayout, QPushButton, QLabel, QProgressBar
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
        
        self.btn_all = QPushButton("All")
        self.btn_all.setObjectName("SecondaryButton")
        self.btn_all.setFixedSize(40, 24)
        self.btn_all.clicked.connect(self.select_all)
        
        self.btn_none = QPushButton("None")
        self.btn_none.setObjectName("SecondaryButton")
        self.btn_none.setFixedSize(40, 24)
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
            checkbox.stateChanged.connect(self.selection_changed.emit)
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
            
            label_text = f"{chapter.order}. {chapter.title}"
            if chapter.is_toc:
                label_text += " [TOC]"
                
            label = QLabel(label_text)
            # Ensure label text is visible with high contrast
            label.setStyleSheet("QLabel { color: #ffffff; background-color: transparent; font-size: 13px; }")
            if chapter.is_toc:
                label.setStyleSheet("QLabel { color: #888888; font-style: italic; background-color: transparent; font-size: 13px; }")
            
            w_layout.addWidget(checkbox)
            w_layout.addWidget(label, stretch=1)
            
            # Progress Bar (Hidden by default, shown during processing)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(0)
            progress.setTextVisible(False)
            progress.setFixedWidth(100)
            progress.setFixedHeight(6) # Thinner
            progress.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #3e3e42;
                    border-radius: 3px;
                }
                QProgressBar::chunk {
                    background-color: #4ec9b0;
                    border-radius: 3px;
                }
            """)
            progress.hide()
            w_layout.addWidget(progress)
            
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

    def update_progress(self, chapter_index, percent):
        # chapter_index is 0-based index in the list
        if chapter_index < self.list_widget.count():
            item = self.list_widget.item(chapter_index)
            widget = self.list_widget.itemWidget(item)
            progress = widget.findChild(QProgressBar)
            if progress:
                progress.show()
                progress.setValue(percent)

    def reset_progress(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            progress = widget.findChild(QProgressBar)
            if progress:
                progress.hide()
                progress.setValue(0)

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
