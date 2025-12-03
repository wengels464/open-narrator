from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QSplitter
from PySide6.QtCore import Qt
import os

from src.gui.styles import DARK_THEME
from src.gui.widgets.drop_zone import DropZone
from src.gui.widgets.chapter_list import ChapterList
from src.gui.widgets.controls import Controls
from src.gui.widgets.text_editor import ChapterEditor
from src.gui.workers import ExtractionWorker, SynthesisWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenNarrator")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(DARK_THEME)
        
        self.current_file = None
        self.chapters = []
        self.worker = None
        
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top Section: Split View
        top_layout = QHBoxLayout()
        
        # Left Column: Drop Zone & Controls
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(150)
        self.drop_zone.file_dropped.connect(self.handle_file_drop)
        self.drop_zone.browse_requested.connect(self.browse_file)
        
        self.controls = Controls()
        self.controls.convert_clicked.connect(self.toggle_conversion)
        
        left_layout.addWidget(self.drop_zone)
        left_layout.addWidget(self.controls)
        left_layout.addStretch()
        
        # Right Area: Splitter for Chapter List and Editor
        right_splitter = QSplitter(Qt.Horizontal)
        
        self.chapter_list = ChapterList()
        self.chapter_list.list_widget.itemClicked.connect(self.on_chapter_selected)
        
        self.editor = ChapterEditor()
        self.editor.text_changed.connect(self.on_chapter_text_updated)
        
        right_splitter.addWidget(self.chapter_list)
        right_splitter.addWidget(self.editor)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 2)
        
        top_layout.addLayout(left_layout, stretch=1)
        top_layout.addWidget(right_splitter, stretch=3)
        
        main_layout.addLayout(top_layout, stretch=1)
        
        # Bottom Section: Progress & Logs
        bottom_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        self.lbl_eta = QLabel("ETA: --:--")
        self.lbl_eta.setStyleSheet("color: #858585; font-weight: bold; margin-left: 10px;")
        self.lbl_eta.setFixedWidth(100)
        
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.lbl_eta)
        
        main_layout.addLayout(bottom_layout)
        
        self.log_area = QTextEdit()
        self.log_area.setObjectName("LogArea")
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        
        main_layout.addWidget(self.log_area)

    def log(self, message):
        self.log_area.append(message)
        # Scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select eBook", "", "eBook Files (*.epub *.pdf);;All Files (*)"
        )
        if file_path:
            self.handle_file_drop(file_path)

    def handle_file_drop(self, file_path):
        self.current_file = file_path
        self.log(f"Loading file: {file_path}")
        self.drop_zone.label.setText("Loading chapters...")
        
        # Start extraction
        self.worker = ExtractionWorker(file_path)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_extraction_finished(self, chapters, metadata):
        self.chapters = chapters
        self.metadata = metadata
        self.chapter_list.set_chapters(chapters)
        self.log(f"Extracted {len(chapters)} chapters.")
        self.log(f"Title: {metadata.get('title', 'Unknown')}")
        self.drop_zone.label.setText(f"Loaded:\n{os.path.basename(self.current_file)}")
        self.worker = None

    def on_chapter_selected(self, item):
        index = self.chapter_list.list_widget.row(item)
        if 0 <= index < len(self.chapters):
            self.editor.load_chapter(index, self.chapters[index])

    def on_chapter_text_updated(self, index, new_text):
        if 0 <= index < len(self.chapters):
            self.chapters[index].content = new_text
            # Update char count in list
            self.chapter_list.set_chapters(self.chapters) # Refresh list to show new counts
            # Re-select the item
            self.chapter_list.list_widget.setCurrentRow(index)
            self.log(f"Updated text for chapter {index + 1}")

    def toggle_conversion(self):
        if self.worker and isinstance(self.worker, SynthesisWorker):
            # Cancel requested
            self.log("Cancelling conversion...")
            self.worker.cancel()
            self.controls.btn_convert.setEnabled(False) # Disable until fully stopped
            self.controls.btn_convert.setText("Cancelling...")
            return

        # Start requested
        self.start_conversion()

    def start_conversion(self):
        if not self.chapters:
            QMessageBox.warning(self, "No Content", "Please load a file first.")
            return
            
        selected_chapters = self.chapter_list.get_selected_chapters()
        if not selected_chapters:
            QMessageBox.warning(self, "No Selection", "Please select at least one chapter.")
            return

        settings = self.controls.get_settings()
        
        # Ask for output location
        default_name = os.path.splitext(os.path.basename(self.current_file))[0] + ".m4b"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Audiobook", default_name, "Audiobook (*.m4b)"
        )
        
        if not output_path:
            return

        self.log(f"Starting conversion with voice: {settings['voice']}, speed: {settings['speed']}")
        self.log(f"Processing {len(selected_chapters)} chapters...")
        
        # Update UI state
        self.controls.btn_convert.setText("Cancel Conversion")
        self.controls.btn_convert.setStyleSheet("background-color: #f44747;") # Red for cancel
        self.chapter_list.reset_progress()
        self.progress_bar.setValue(0)
        
        # Start synthesis
        self.worker = SynthesisWorker(
            selected_chapters, 
            output_path, 
            settings['voice'], 
            settings['speed'],
            metadata=getattr(self, 'metadata', {})
        )
        self.worker.progress_update.connect(self.update_progress)
        self.worker.eta_update.connect(self.lbl_eta.setText)
        self.worker.log_message.connect(self.log)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def update_progress(self, chapter_index, percent):
        # Update individual chapter progress
        self.chapter_list.update_progress(chapter_index, percent)
        
        # Update total progress (approximate)
        total_chapters = len(self.chapters)
        if total_chapters > 0:
            # Calculate overall progress based on completed chapters + current chapter percent
            # This is an approximation assuming equal chapter length, but good enough for UI
            overall_percent = int(((chapter_index + (percent / 100)) / total_chapters) * 100)
            self.progress_bar.setValue(overall_percent)
            self.progress_bar.setFormat(f"Processing Chapter {chapter_index + 1}/{total_chapters} ({percent}%)")

    def on_conversion_finished(self):
        self.log("Conversion completed successfully!")
        self.reset_ui_state()
        self.progress_bar.setFormat("Done!")
        self.worker = None
        QMessageBox.information(self, "Success", "Audiobook created successfully!")

    def on_worker_error(self, error_msg):
        self.log(f"Error: {error_msg}")
        self.reset_ui_state()
        self.worker = None
        # Don't show popup if just cancelled (handled via log)
        if "cancelled" not in error_msg.lower():
            QMessageBox.critical(self, "Error", error_msg)

    def reset_ui_state(self):
        self.controls.btn_convert.setText("Convert to Audiobook")
        self.controls.btn_convert.setStyleSheet("") # Reset style
        self.controls.btn_convert.setEnabled(True)
