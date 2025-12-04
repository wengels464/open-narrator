from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QPushButton, QMessageBox, QGroupBox, QSpinBox
from PySide6.QtCore import Signal, QThread, Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import numpy as np
import os
import tempfile
import soundfile as sf
from src.utils.config import VOICES_BIN_PATH, PREVIEW_TEXT
from src.core.synthesizer import AudioSynthesizer
from src.utils.gpu import get_gpu_info

class PreviewWorker(QThread):
    finished = Signal()
    error = Signal(str)
    audio_ready = Signal(str) # Emits path to generated audio

    def __init__(self, voice, speed, sentence_pause=0.4, comma_pause=None):
        super().__init__()
        self.voice = voice
        self.speed = speed
        self.sentence_pause = sentence_pause
        self.comma_pause = comma_pause

    def run(self):
        try:
            from src.utils.audio_utils import trim_silence, create_silence
            import numpy as np
            import re
            
            synth = AudioSynthesizer()
            # Friendly name mapping for preview text
            name = self.voice.split('_')[1].title()
            text = PREVIEW_TEXT
            
            # Apply advanced prosody if comma_pause is set
            if self.comma_pause is not None:
                parts = re.split(r'(,)', text)
                phrase_audios = []
                current_phrase = ""
                sample_rate = 24000
                
                for part in parts:
                    current_phrase += part
                    if ',' in part or part == parts[-1]:
                        if not current_phrase.strip():
                            continue
                        audio, sample_rate = synth.synthesize_segment(
                            current_phrase, voice_name=self.voice, speed=self.speed
                        )
                        audio = trim_silence(audio, sample_rate=sample_rate)
                        phrase_audios.append(audio)
                        
                        if ',' in part and part != parts[-1]:
                            silence = create_silence(self.comma_pause, sample_rate)
                            phrase_audios.append(silence)
                        current_phrase = ""
                
                if phrase_audios:
                    audio = np.concatenate(phrase_audios)
                else:
                    audio, sample_rate = synth.synthesize_segment(text, voice_name=self.voice, speed=self.speed)
            else:
                audio, sample_rate = synth.synthesize_segment(text, voice_name=self.voice, speed=self.speed)
            
            # Add sentence pause if specified
            if self.sentence_pause > 0:
                silence = create_silence(self.sentence_pause, sample_rate)
                audio = np.concatenate([audio, silence])
            
            temp_dir = tempfile.gettempdir()
            preview_path = os.path.join(temp_dir, "preview.wav")
            synth.save_audio(audio, sample_rate, preview_path)
            
            self.audio_ready.emit(preview_path)
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
        
        # Audio Player Setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        
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
        
        layout.addLayout(voice_layout)
        
        # Voice Preview Button (large green)
        self.btn_preview = QPushButton("Voice Preview")
        self.btn_preview.setMinimumHeight(35)
        self.btn_preview.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_preview.clicked.connect(self.play_preview)
        layout.addWidget(self.btn_preview)
        

        
        # Speed Selection
        layout.addWidget(QLabel("Speed"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        layout.addWidget(self.speed_spin)
        
        # Advanced Settings
        self.group_advanced = QGroupBox("Advanced Settings")
        self.group_advanced.setCheckable(True)
        self.group_advanced.setChecked(False)
        
        adv_layout = QVBoxLayout()
        
        # Sentence Pause
        adv_layout.addWidget(QLabel("Sentence Pause (ms)"))
        self.spin_sentence_pause = QSpinBox()
        self.spin_sentence_pause.setRange(0, 2000)
        self.spin_sentence_pause.setValue(400) # Default
        self.spin_sentence_pause.setSingleStep(50)
        adv_layout.addWidget(self.spin_sentence_pause)
        
        # Comma Pause
        adv_layout.addWidget(QLabel("Comma Pause (ms)"))
        self.spin_comma_pause = QSpinBox()
        self.spin_comma_pause.setRange(0, 1000)
        self.spin_comma_pause.setValue(150) # Default short pause
        self.spin_comma_pause.setSingleStep(10)
        adv_layout.addWidget(self.spin_comma_pause)
        
        self.group_advanced.setLayout(adv_layout)
        layout.addWidget(self.group_advanced)
        
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
        # If currently playing, stop
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.stop()
            return

        friendly = self.voice_combo.currentText()
        code = self.voice_data.get(friendly)
        speed = self.speed_spin.value()
        
        if not code:
            return
            
        self.btn_preview.setEnabled(False)
        self.btn_preview.setText("Generating...")
        
        # Get pause settings
        sentence_pause = 0.4
        comma_pause = None
        if self.group_advanced.isChecked():
            sentence_pause = self.spin_sentence_pause.value() / 1000.0
            comma_pause = self.spin_comma_pause.value() / 1000.0
        
        self.worker = PreviewWorker(code, speed, sentence_pause, comma_pause)
        self.worker.audio_ready.connect(self.on_preview_ready)
        self.worker.error.connect(self.on_preview_error)
        self.worker.start()

    def on_preview_ready(self, file_path):
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(1.0)
        self.player.play()
        # Button state will be handled by on_playback_state_changed

    def on_preview_error(self, error_msg):
        QMessageBox.warning(self, "Preview Error", error_msg)
        self.btn_preview.setEnabled(True)
        self.btn_preview.setText("▶")

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_preview.setEnabled(True)
            self.btn_preview.setText("Stop Preview")
            self.btn_preview.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
        elif state == QMediaPlayer.StoppedState:
            self.btn_preview.setEnabled(True)
            self.btn_preview.setText("Voice Preview")
            self.btn_preview.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")

    def get_settings(self):
        friendly = self.voice_combo.currentText()
        
        # Get advanced settings if enabled
        sentence_pause = 0.4 # Default 400ms
        comma_pause = None # Default None (let model decide)
        
        if self.group_advanced.isChecked():
            sentence_pause = self.spin_sentence_pause.value() / 1000.0
            comma_pause = self.spin_comma_pause.value() / 1000.0
            
        return {
            "voice": self.voice_data.get(friendly, "af_sarah"),
            "speed": self.speed_spin.value(),
            "sentence_pause": sentence_pause,
            "comma_pause": comma_pause
        }
