"""
Metadata Panel widget for Open Narrator.
Displays and allows editing of book metadata, plus cover art preview.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QFileDialog, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap


class MetadataPanel(QWidget):
    """Panel for displaying and editing book metadata."""
    
    search_requested = Signal(str, str)  # title, author
    
    def __init__(self):
        super().__init__()
        self.cover_path = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Metadata Group
        metadata_group = QGroupBox("Book Metadata")
        metadata_layout = QVBoxLayout()
        metadata_layout.setSpacing(5)
        
        # Title
        metadata_layout.addWidget(QLabel("Title"))
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Book title")
        metadata_layout.addWidget(self.txt_title)
        
        # Author
        metadata_layout.addWidget(QLabel("Author"))
        self.txt_author = QLineEdit()
        self.txt_author.setPlaceholderText("Author name")
        metadata_layout.addWidget(self.txt_author)
        
        # ISBN
        metadata_layout.addWidget(QLabel("ISBN"))
        self.txt_isbn = QLineEdit()
        self.txt_isbn.setPlaceholderText("ISBN-10 or ISBN-13")
        metadata_layout.addWidget(self.txt_isbn)
        
        # Description
        metadata_layout.addWidget(QLabel("Description"))
        self.txt_description = QTextEdit()
        self.txt_description.setPlaceholderText("Book description")
        self.txt_description.setMaximumHeight(80)
        metadata_layout.addWidget(self.txt_description)
        
        # Search Button
        self.btn_search = QPushButton("🔍 Search Metadata Online")
        self.btn_search.setMinimumHeight(30)
        self.btn_search.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")
        self.btn_search.clicked.connect(self.on_search_clicked)
        metadata_layout.addWidget(self.btn_search)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        # Cover Art Group
        cover_group = QGroupBox("Cover Art")
        cover_layout = QVBoxLayout()
        
        # Cover Preview
        self.lbl_cover = QLabel()
        self.lbl_cover.setFixedSize(150, 150)
        self.lbl_cover.setAlignment(Qt.AlignCenter)
        self.lbl_cover.setStyleSheet("background-color: #333; border: 1px solid #555;")
        self.lbl_cover.setText("No Cover")
        cover_layout.addWidget(self.lbl_cover, alignment=Qt.AlignCenter)
        
        # Browse Cover Button
        self.btn_browse_cover = QPushButton("Browse Cover Image")
        self.btn_browse_cover.clicked.connect(self.browse_cover)
        cover_layout.addWidget(self.btn_browse_cover)
        
        cover_group.setLayout(cover_layout)
        layout.addWidget(cover_group)
        
        layout.addStretch()
    
    def on_search_clicked(self):
        """Emit search request with current title and author."""
        title = self.txt_title.text().strip()
        author = self.txt_author.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Search Error", "Please enter a book title to search.")
            return
        
        self.btn_search.setEnabled(False)
        self.btn_search.setText("Searching...")
        self.search_requested.emit(title, author)
    
    def set_metadata(self, metadata):
        """
        Set metadata fields from a MetadataResult or dict.
        """
        if isinstance(metadata, dict):
            self.txt_title.setText(metadata.get("title", ""))
            self.txt_author.setText(metadata.get("author", ""))
            self.txt_isbn.setText(metadata.get("isbn", ""))
            self.txt_description.setPlainText(metadata.get("description", ""))
            
            cover_path = metadata.get("cover_path")
            if cover_path:
                self.set_cover(cover_path)
        else:
            # MetadataResult object
            self.txt_title.setText(metadata.title or "")
            self.txt_author.setText(metadata.author or "")
            self.txt_isbn.setText(metadata.isbn or "")
            self.txt_description.setPlainText(metadata.description or "")
            
            if metadata.cover_path:
                self.set_cover(metadata.cover_path)
    
    def get_metadata(self):
        """Get current metadata as dict."""
        return {
            "title": self.txt_title.text().strip(),
            "author": self.txt_author.text().strip(),
            "isbn": self.txt_isbn.text().strip(),
            "description": self.txt_description.toPlainText().strip(),
            "cover_path": self.cover_path
        }
    
    def set_cover(self, image_path):
        """Set cover art preview from file path."""
        self.cover_path = image_path
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_cover.setPixmap(scaled)
        else:
            self.lbl_cover.setText("No Cover")
            self.lbl_cover.setPixmap(QPixmap())
    
    def browse_cover(self):
        """Open file dialog to select cover image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Cover Image", "", 
            "Image Files (*.jpg *.jpeg *.png *.bmp);;All Files (*)"
        )
        if file_path:
            # Process the cover to 2400x2400
            from src.core.metadata import process_local_cover
            processed_path = process_local_cover(file_path)
            if processed_path:
                self.set_cover(processed_path)
            else:
                self.set_cover(file_path)
    
    def reset_search_button(self):
        """Reset search button state."""
        self.btn_search.setEnabled(True)
        self.btn_search.setText("🔍 Search Metadata Online")
    
    def clear(self):
        """Clear all fields."""
        self.txt_title.clear()
        self.txt_author.clear()
        self.txt_isbn.clear()
        self.txt_description.clear()
        self.cover_path = None
        self.lbl_cover.setText("No Cover")
        self.lbl_cover.setPixmap(QPixmap())


# Need os import for path checking
import os
