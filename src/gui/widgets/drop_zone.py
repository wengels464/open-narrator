from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os

class DropZone(QWidget):
    file_dropped = Signal(str)  # Emits file path
    browse_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.label = QLabel("Drag & Drop PDF or EPUB here\nor click to browse")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #858585; font-size: 16px; font-weight: bold;")
        
        layout.addWidget(self.label)
        
        self.btn_browse = QPushButton("Browse Files")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.clicked.connect(self.browse_clicked)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #2a2d2e;
                border: 1px solid #3e3e42;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-color: #007acc;
            }
        """)
        layout.addWidget(self.btn_browse)

    def browse_clicked(self):
        # Emit signal or handle directly? 
        # Since we need QFileDialog, better to emit signal to parent
        # But for simplicity, we can emit a custom signal that MainWindow connects to
        self.browse_requested.emit()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.pdf', '.epub')):
                    event.acceptProposedAction()
                    self.setStyleSheet("QWidget#DropZone { border-color: #007acc; background-color: #2a2d2e; }")
                    return
        
        event.ignore()

    def dragLeaveEvent(self, event):
        # Reset style
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.file_dropped.emit(file_path)
            self.label.setText(f"Selected:\n{os.path.basename(file_path)}")
            self.setStyleSheet("QWidget#DropZone { border-color: #4ec9b0; }")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Signal parent to open file dialog
            # We can't open dialog here easily without blocking, better to let parent handle
            pass
