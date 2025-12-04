from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QPushButton, QMessageBox
from PySide6.QtCore import Signal, QThread, Qt
import numpy as np
import os
import tempfile
import soundfile as sf
from src.utils.config import VOICES_BIN_PATH
from src.core.synthesizer import AudioSynthesizer
from src.utils.gpu import get_gpu_info

class PreviewWorker(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, voice, speed):
        super().__init__()
        self.voice = voice
        self.speed = speed

    def run(self):
        try:
            synth = AudioSynthesizer()
            # Friendly name mapping for preview text
            name = self.voice.split('_')[1].title()
            # text = f"Hello, I am {name}. This is a preview of my voice."
            text = "They were careless people, Tom and Daisy- they smashed up things and creatures and then retreated back into their money or their vast carelessness or whatever it was that kept them together, and let other people clean up the mess they had made."
            
            audio, sr = synth.synthesize_segment(text, voice_name=self.voice, speed=self.speed)
            
            # Play audio using simple method (os.startfile on Windows is easiest for quick preview)
            temp_dir = tempfile.gettempdir()
            preview_path = os.path.join(temp_dir, "preview.wav")
            synth.save_audio(audio, sr, preview_path)
            
            if os.name == 'nt':
                os.startfile(preview_path)
            else:
                pass
                
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class Controls(QWidget):
    convert_clicked = Signal()
    
    VOICE_MAPPING = {
        'af': 'American Female',
        'am': 'American Male',
        'bf': 'British Female',
        'bm': 'British Male',
        'ef': 'Spanish Female',
        'em': 'Spanish Male',
        'ff': 'French Female',
        'hf': 'Hindi Female',
        'hm': 'Hindi Male',
        'if': 'Italian Female',
        'im': 'Italian Male',
        'jf': 'Japanese Female',
        'jm': 'Japanese Male',
        'pf': 'Portuguese Female',
        'pm': 'Portuguese Male',
        'zf': 'Chinese Female',
        'zm': 'Chinese Male'
    }

    def __init__(self):
        super().__init__()
        self.voice_data = {} # Map friendly name -> code
        self.setup_ui()
        self.load_voices()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Voice Selection
        layout.addWidget(QLabel("Voice"))
        
        voice_layout = QHBoxLayout()
        self.voice_combo = QComboBox()
        voice_layout.addWidget(self.voice_combo, stretch=1)
        
        self.btn_preview = QPushButton("▶")
        self.btn_preview.setToolTip("Preview Voice")
        self.btn_preview.setFixedSize(30, 30)
        self.btn_preview.clicked.connect(self.play_preview)
        voice_layout.addWidget(self.btn_preview)
        
        layout.addLayout(voice_layout)
        
        # Speed Selection
        layout.addWidget(QLabel("Speed"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        layout.addWidget(self.speed_spin)
        
        layout.addStretch()
        
        # Convert Button
        self.btn_convert = QPushButton("Convert to Audiobook")
        self.btn_convert.setMinimumHeight(40)
        self.btn_convert.clicked.connect(self.convert_clicked.emit)
        layout.addWidget(self.btn_convert)
        
        # GPU Status
        gpu_available, gpu_name = get_gpu_info()
        status_color = "#4ec9b0" if gpu_available else "#ce9178"
        
        self.lbl_gpu = QLabel(f"Hardware: {gpu_name}")
        self.lbl_gpu.setStyleSheet(f"color: {status_color}; font-size: 11px; margin-top: 5px;")
        self.lbl_gpu.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_gpu)

    def get_friendly_name(self, voice_code):
        parts = voice_code.split('_')
        if len(parts) < 2:
            return voice_code
            
        prefix = parts[0]
        name = parts[1].title()
        
        region_gender = self.VOICE_MAPPING.get(prefix, "Unknown")
        return f"{name} ({region_gender})"

    def load_voices(self):
        try:
            if os.path.exists(VOICES_BIN_PATH):
                voices = np.load(VOICES_BIN_PATH, allow_pickle=True)
                voice_list = sorted(voices.keys())
                
                for code in voice_list:
                    friendly = self.get_friendly_name(code)
                    self.voice_data[friendly] = code
                    self.voice_combo.addItem(friendly)
                
                # Set default to Sarah
                default_name = self.get_friendly_name("af_sarah")
                index = self.voice_combo.findText(default_name)
                if index >= 0:
                    self.voice_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Failed to load voices: {e}")
            self.voice_combo.addItem("Error loading voices")

    def play_preview(self):
        friendly = self.voice_combo.currentText()
        code = self.voice_data.get(friendly)
        speed = self.speed_spin.value()
        
        if not code:
            return
            
        self.btn_preview.setEnabled(False)
        self.worker = PreviewWorker(code, speed)
        self.worker.finished.connect(lambda: self.btn_preview.setEnabled(True))
        self.worker.error.connect(lambda e: QMessageBox.warning(self, "Preview Error", e))
        self.worker.start()

    def get_settings(self):
        friendly = self.voice_combo.currentText()
        return {
            "voice": self.voice_data.get(friendly, "af_sarah"),
            "speed": self.speed_spin.value()
        }
