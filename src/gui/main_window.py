
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
        # self.chapter_list.reset_progress() - Removed
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
        self.log(f"Error: {error_msg}")
        self.reset_ui_state()
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
        # self.chapter_list.reset_progress() - Removed
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
