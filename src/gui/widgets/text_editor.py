from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PySide6.QtCore import Signal, Qt

class ChapterEditor(QWidget):
    text_changed = Signal(int, str) # chapter_index, new_text

    def __init__(self):
        super().__init__()
        self.current_chapter_index = -1
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("Chapter Editor")
        self.lbl_title.setObjectName("Subheading")
        header_layout.addWidget(self.lbl_title)
        
        header_layout.addStretch()
        
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setObjectName("SecondaryButton")
        self.btn_save.setFixedSize(100, 30) # Increased height from 24 to 30
        self.btn_save.clicked.connect(self.save_changes)
        self.btn_save.setEnabled(False)
        
        header_layout.addWidget(self.btn_save)
        layout.addLayout(header_layout)
        
        # Text Area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Select a chapter to edit text...")
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        # Info Label
        self.lbl_info = QLabel("Modifications will be used for audio generation.")
        self.lbl_info.setStyleSheet("color: #858585; font-size: 11px;")
        layout.addWidget(self.lbl_info)

    def load_chapter(self, index, chapter):
        self.current_chapter_index = index
        self.lbl_title.setText(f"Editing: {chapter.title}")
        self.text_edit.blockSignals(True)
        self.text_edit.setText(chapter.content)
        self.text_edit.blockSignals(False)
        self.btn_save.setEnabled(False)

    def on_text_changed(self):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Save Changes*")
        self.btn_save.setStyleSheet("background-color: #007acc; color: white;")

    def save_changes(self):
        if self.current_chapter_index >= 0:
            new_text = self.text_edit.toPlainText()
            self.text_changed.emit(self.current_chapter_index, new_text)
            
            self.btn_save.setEnabled(False)
            self.btn_save.setText("Saved")
            self.btn_save.setStyleSheet("")
