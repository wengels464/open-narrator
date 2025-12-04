"""
Pronunciation review dialog for Open Narrator.
Allows users to review and approve pronunciation corrections.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QHeaderView, QLineEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread
from typing import Dict, List
import sys


class PronunciationLookupWorker(QThread):
    """Worker thread for looking up pronunciations without blocking GUI."""
    progress = Signal(int, int)  # current, total
    word_found = Signal(str, dict)  # word, pronunciation_info
    finished = Signal(dict)  # final pronunciation_dict
    
    def __init__(self, words: List[str]):
        super().__init__()
        self.words = words
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def run(self):
        from src.utils.pronunciation import search_wikipedia_pronunciation, ipa_to_phonetic_spelling
        
        pronunciation_dict = {}
        total = len(self.words)
        
        for i, word in enumerate(self.words):
            if self._is_cancelled:
                break
            
            self.progress.emit(i + 1, total)
            result = search_wikipedia_pronunciation(word)
            
            if result:
                # Create phonetic spelling
                if 'ipa' in result:
                    phonetic = ipa_to_phonetic_spelling(result['ipa'], word)
                    result['phonetic_spelling'] = phonetic
                elif 'respelling' in result:
                    result['phonetic_spelling'] = result['respelling']
                
                pronunciation_dict[word] = result
                self.word_found.emit(word, result)
        
        self.finished.emit(pronunciation_dict)


class PronunciationDialog(QDialog):
    """
    Dialog for reviewing and approving pronunciation corrections.
    """
    
    def __init__(self, difficult_words: List[str], parent=None):
        super().__init__(parent)
        self.difficult_words = difficult_words
        self.pronunciation_dict = {}
        self.approved_corrections = {}  # word -> phonetic_spelling
        self.worker = None
        
        self.setWindowTitle("Pronunciation Corrections")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(
            f"Found {len(self.difficult_words)} potentially difficult words. "
            "Looking up pronunciations from Wikipedia..."
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.difficult_words))
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Apply", "Original Word", "Pronunciation (IPA)", "Phonetic Spelling", "Source"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(len(self.difficult_words))
        
        # Populate table with words (pronunciations will be filled in by worker)
        for i, word in enumerate(self.difficult_words):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(False)  # Start unchecked, user approves
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 0, checkbox_widget)
            
            # Original word
            self.table.setItem(i, 1, QTableWidgetItem(word))
            
            # Placeholders for pronunciation info
            self.table.setItem(i, 2, QTableWidgetItem("Searching..."))
            self.table.setItem(i, 3, QTableWidgetItem(""))
            self.table.setItem(i, 4, QTableWidgetItem(""))
        
        layout.addWidget(self.table)
        
        # Instructions
        instructions = QLabel(
            "Review the pronunciations and check the boxes for words you want to correct. "
            "You can edit the phonetic spelling if needed."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self.select_all)
        button_layout.addWidget(self.btn_select_all)
        
        self.btn_select_none = QPushButton("Select None")
        self.btn_select_none.clicked.connect(self.select_none)
        button_layout.addWidget(self.btn_select_none)
        
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_apply = QPushButton("Apply Corrections")
        self.btn_apply.clicked.connect(self.apply_corrections)
        self.btn_apply.setEnabled(False)  # Enable after lookup completes
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
        # Start pronunciation lookup
        self.start_lookup()
    
    def start_lookup(self):
        """Start background thread to look up pronunciations."""
        self.worker = PronunciationLookupWorker(self.difficult_words)
        self.worker.progress.connect(self.update_progress)
        self.worker.word_found.connect(self.add_pronunciation)
        self.worker.finished.connect(self.lookup_finished)
        self.worker.start()
    
    def update_progress(self, current, total):
        """Update progress bar."""
        self.progress_bar.setValue(current)
    
    def add_pronunciation(self, word, info):
        """Add pronunciation info to table when found."""
        # Find row for this word
        for row in range(self.table.rowCount()):
            if self.table.item(row, 1).text() == word:
                # Update IPA
                ipa = info.get('ipa', info.get('respelling', 'N/A'))
                self.table.setItem(row, 2, QTableWidgetItem(ipa))
                
                # Update phonetic spelling (editable)
                phonetic_item = QTableWidgetItem(info.get('phonetic_spelling', ''))
                phonetic_item.setFlags(phonetic_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, phonetic_item)
                
                # Update source
                self.table.setItem(row, 4, QTableWidgetItem(info.get('source', '')))
                
                # Auto-check if pronunciation found
                checkbox_widget = self.table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and info.get('phonetic_spelling'):
                    checkbox.setChecked(True)
                
                break
    
    def lookup_finished(self, pronunciation_dict):
        """Called when all lookups are complete."""
        self.pronunciation_dict = pronunciation_dict
        self.progress_bar.setFormat("Lookup complete!")
        self.btn_apply.setEnabled(True)
        
        # Update rows where no pronunciation was found
        for row in range(self.table.rowCount()):
            if self.table.item(row, 2).text() == "Searching...":
                self.table.setItem(row, 2, QTableWidgetItem("Not found"))
                self.table.setItem(row, 3, QTableWidgetItem(""))
                self.table.setItem(row, 4, QTableWidgetItem(""))
    
    def select_all(self):
        """Select all checkboxes."""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox and self.table.item(row, 3).text():  # Only if has phonetic spelling
                checkbox.setChecked(True)
    
    def select_none(self):
        """Deselect all checkboxes."""
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(False)
    
    def apply_corrections(self):
        """Collect approved corrections and close dialog."""
        self.approved_corrections = {}
        
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            
            if checkbox and checkbox.isChecked():
                original = self.table.item(row, 1).text()
                phonetic = self.table.item(row, 3).text()
                
                if phonetic:  # Only add if has phonetic spelling
                    self.approved_corrections[original] = phonetic
        
        self.accept()
    
    def get_corrections(self) -> Dict[str, str]:
        """Get the approved corrections dict."""
        return self.approved_corrections


# For testing
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    test_words = ["Achille", "Mbembe", "Nietzsche", "Goethe", "Tchaikovsky"]
    dialog = PronunciationDialog(test_words)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        corrections = dialog.get_corrections()
        print("Approved corrections:")
        for original, phonetic in corrections.items():
            print(f"  {original} -> {phonetic}")
    
    sys.exit(0)
