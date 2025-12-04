from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QSplitter, QStatusBar, QPushButton
from PySide6.QtCore import Qt, QTimer
import os
import time

from src.gui.styles import DARK_THEME
from src.gui.widgets.drop_zone import DropZone
from src.gui.widgets.chapter_list import ChapterList
from src.gui.widgets.controls import Controls
from src.gui.widgets.text_editor import ChapterEditor
from src.gui.widgets.metadata_panel import MetadataPanel
from src.gui.widgets.pronunciation_dialog import PronunciationDialog
from src.gui.workers import ExtractionWorker, SynthesisWorker, MetadataWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenNarrator")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(DARK_THEME)
        
        self.current_file = None
        self.chapters = []
        self.worker = None
        self.metadata = {}
        self.metadata_worker = None
        self.pronunciation_corrections = {}  # word -> phonetic_spelling
        
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
        
        left_layout.addWidget(self.drop_zone)
        left_layout.addWidget(self.controls)
        
        # Metadata Panel
        self.metadata_panel = MetadataPanel()
        self.metadata_panel.search_requested.connect(self.search_metadata)
        left_layout.addWidget(self.metadata_panel)
        
        left_layout.addStretch()
        
        # Right Area: Splitter for Chapter List and Editor
        right_splitter = QSplitter(Qt.Horizontal)
        
        self.chapter_list = ChapterList()
        self.chapter_list.list_widget.itemClicked.connect(self.on_chapter_selected)
        
        self.editor = ChapterEditor()
        self.editor.text_changed.connect(self.on_chapter_text_updated)
        
        right_splitter.addWidget(self.chapter_list)
        right_splitter.addWidget(self.editor)
        
        # Assemble Top Layout
        top_layout.addLayout(left_layout, 1) # 1/3 width
        
        # Right column with chapters and convert button
        right_column = QVBoxLayout()
        right_column.addWidget(right_splitter)
        
        # Button layout for pronunciation and convert
        button_layout = QHBoxLayout()
        
        # Check Pronunciations Button
        self.btn_pronunciations = QPushButton("Check Pronunciations")
        self.btn_pronunciations.setMinimumHeight(45)
        self.btn_pronunciations.setStyleSheet("background-color: #7b1fa2; color: white; font-weight: bold; font-size: 14px;")
        self.btn_pronunciations.clicked.connect(self.check_pronunciations)
        self.btn_pronunciations.setEnabled(False)  # Enable after chapters loaded
        button_layout.addWidget(self.btn_pronunciations)
        
        # Convert Button
        self.btn_convert = QPushButton("Convert to Audiobook")
        self.btn_convert.setMinimumHeight(45)
        self.btn_convert.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; font-size: 14px;")
        self.btn_convert.clicked.connect(self.toggle_conversion)
        button_layout.addWidget(self.btn_convert)
        
        right_column.addLayout(button_layout)
        
        top_layout.addLayout(right_column, 2) # 2/3 width
        
        main_layout.addLayout(top_layout)
        
        self.log_area = QTextEdit()
        self.log_area.setObjectName("LogArea")
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        
        main_layout.addWidget(self.log_area)
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.status_bar.addPermanentWidget(self.progress_bar, 1)
        
        # ETA Label
        self.lbl_eta = QLabel("ETA: --:--")
        self.lbl_eta.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.lbl_eta)
        
        # Total Time Label
        self.lbl_total_time = QLabel("Total Time: 00:00")
        self.lbl_total_time.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.lbl_total_time)

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
        
        # Enable pronunciation check button
        self.btn_pronunciations.setEnabled(True)
        
        # Populate metadata panel with extracted info
        self.metadata_panel.txt_title.setText(metadata.get('title', ''))
        self.metadata_panel.txt_author.setText(metadata.get('author', ''))

    def search_metadata(self, title, author):
        """Start metadata search in background thread."""
        self.log(f"Searching metadata for: {title}")
        
        self.metadata_worker = MetadataWorker(title, author if author else None)
        self.metadata_worker.finished.connect(self.on_metadata_found)
        self.metadata_worker.error.connect(self.on_metadata_error)
        self.metadata_worker.start()
    
    def on_metadata_found(self, result):
        """Handle successful metadata search."""
        self.metadata_panel.reset_search_button()
        self.metadata_panel.set_metadata(result)
        self.log(f"Found metadata from {result.source}")
        if result.cover_path:
            self.log(f"Cover art downloaded: {result.cover_path}")
        self.metadata_worker = None
    
    def on_metadata_error(self, error_msg):
        """Handle metadata search error."""
        self.metadata_panel.reset_search_button()
        self.log(f"Metadata search error: {error_msg}")
        QMessageBox.warning(self, "Metadata Search", error_msg)
        self.metadata_worker = None

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
        self.progress_bar.setValue(0)
        
        # Start synthesis
        self.worker = SynthesisWorker(
            selected_chapters, 
            output_path, 
            settings['voice'], 
            settings['speed'],
            metadata=getattr(self, 'metadata', {}),
            sentence_pause=settings.get('sentence_pause', 0.4),
            comma_pause=settings.get('comma_pause'),
            pronunciation_corrections=self.pronunciation_corrections
        )
        self.worker.progress_update.connect(self.update_progress)
        self.worker.eta_update.connect(self.lbl_eta.setText)
        self.worker.log_message.connect(self.log)
        self.worker.finished.connect(self.on_conversion_finished)
        self.worker.cancelled.connect(self.on_conversion_cancelled)
        self.worker.error.connect(self.on_worker_error)
        
        # Start Total Time Timer
        self.start_time = time.time()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000) # Update every second
        
        self.worker.start()

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.lbl_total_time.setText(f"Total Time: {mins:02d}:{secs:02d}")

    def update_progress(self, chapter_index, percent):
        # Update total progress directly from worker (now global percent)
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"Processing... ({percent}%)")

    def on_conversion_finished(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
            
        self.log("Conversion completed successfully!")
        self.reset_ui_state()
        self.progress_bar.setFormat("Done!")
        self.worker = None
        QMessageBox.information(self, "Success", "Audiobook created successfully!")

    def on_conversion_cancelled(self, partial_file_path):
        """Handle cancellation with user prompt to keep or discard partial file."""
        if hasattr(self, 'timer'):
            self.timer.stop()
            
        self.reset_ui_state()
        self.worker = None
        
        # Prompt user
        reply = QMessageBox.question(
            self,
            "Conversion Cancelled",
            f"A partial audiobook was created:\n{partial_file_path}\n\nWould you like to keep this partial file?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            # User chose to discard
            try:
                if os.path.exists(partial_file_path):
                    os.remove(partial_file_path)
                    self.log(f"Deleted partial file: {partial_file_path}")
            except Exception as e:
                self.log(f"Error deleting file: {e}")
        else:
            self.log(f"Partial audiobook saved: {partial_file_path}")

    def on_worker_error(self, error_msg):
        if hasattr(self, 'timer'):
            self.timer.stop()
            
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
    
    def check_pronunciations(self):
        """Open pronunciation dialog to check and correct difficult words."""
        if not self.chapters:
            QMessageBox.warning(self, "No Chapters", "Please load a book first.")
            return
        
        # Collect all text from chapters
        all_text = "\n\n".join([chapter.content for chapter in self.chapters])
        
        # Find difficult words
        from src.utils.pronunciation import find_difficult_words
        difficult_words = find_difficult_words(all_text)
        
        if not difficult_words:
            QMessageBox.information(
                self, 
                "No Difficult Words", 
                "No potentially difficult-to-pronounce words were found in the text."
            )
            return
        
        self.log(f"Found {len(difficult_words)} potentially difficult words.")
        
        # Open pronunciation dialog
        dialog = PronunciationDialog(difficult_words, self)
        if dialog.exec() == PronunciationDialog.DialogCode.Accepted:
            corrections = dialog.get_corrections()
            self.pronunciation_corrections = corrections
            
            if corrections:
                self.log(f"Applied {len(corrections)} pronunciation corrections:")
                for original, phonetic in corrections.items():
                    self.log(f"  {original} → {phonetic}")
            else:
                self.log("No pronunciation corrections applied.")
        else:
            self.log("Pronunciation check cancelled.")
