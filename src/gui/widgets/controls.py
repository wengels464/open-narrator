from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, QPushButton, QMessageBox, QSpinBox, QCheckBox
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

    def __init__(self, voice, speed, sentence_pause=0.3, comma_pause=0.15):
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
        self.loop_enabled = False
        self.current_preview_path = None
        
        # Audio Player Setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.playbackStateChanged.connect(self.on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        self.setup_ui()
        self.load_voices()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Voice Selection
        layout.addWidget(QLabel("Voice"))
        self.voice_combo = QComboBox()
        layout.addWidget(self.voice_combo)
        
        # Speed Selection
        layout.addWidget(QLabel("Speed"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 2.0)
        self.speed_spin.setSingleStep(0.05)
        self.speed_spin.setValue(1.10)  # Default: 1.10x
        layout.addWidget(self.speed_spin)
        
        # Pause Settings (no longer in a checkbox group)
        layout.addWidget(QLabel("Sentence Pause (ms)"))
        self.spin_sentence_pause = QSpinBox()
        self.spin_sentence_pause.setRange(0, 2000)
        self.spin_sentence_pause.setValue(300)  # Default: 300ms
        self.spin_sentence_pause.setSingleStep(50)
        layout.addWidget(self.spin_sentence_pause)
        
        layout.addWidget(QLabel("Comma Pause (ms)"))
        self.spin_comma_pause = QSpinBox()
        self.spin_comma_pause.setRange(0, 1000)
        self.spin_comma_pause.setValue(150)  # Default: 150ms
        self.spin_comma_pause.setSingleStep(10)
        layout.addWidget(self.spin_comma_pause)
        
        # Voice Preview Button (large green)
        self.btn_preview = QPushButton("Voice Preview")
        self.btn_preview.setMinimumHeight(35)
        self.btn_preview.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        self.btn_preview.clicked.connect(self.play_preview)
        layout.addWidget(self.btn_preview)
        
        # Loop Audio Checkbox
        self.chk_loop = QCheckBox("Loop Audio for Pause Testing")
        self.chk_loop.setChecked(False)
        self.chk_loop.toggled.connect(self.on_loop_toggled)
        layout.addWidget(self.chk_loop)
        
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
                
                # Set default to Sky (American Female)
                default_name = self.get_friendly_name("af_sky")
                index = self.voice_combo.findText(default_name)
                if index >= 0:
                    self.voice_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Failed to load voices: {e}")
            self.voice_combo.addItem("Error loading voices")

    def on_loop_toggled(self, checked):
        self.loop_enabled = checked
        if checked and self.current_preview_path:
            # If we have a preview and just enabled loop, set it up
            self.player.setLoops(QMediaPlayer.Infinite)
        else:
            self.player.setLoops(1)

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
        
        # Get pause settings (always enabled now)
        sentence_pause = self.spin_sentence_pause.value() / 1000.0
        comma_pause = self.spin_comma_pause.value() / 1000.0
        
        self.worker = PreviewWorker(code, speed, sentence_pause, comma_pause)
        self.worker.audio_ready.connect(self.on_preview_ready)
        self.worker.error.connect(self.on_preview_error)
        self.worker.start()

    def on_preview_ready(self, file_path):
        self.current_preview_path = file_path
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(1.0)
        
        # Set loop mode if enabled
        if self.loop_enabled:
            self.player.setLoops(QMediaPlayer.Infinite)
        else:
            self.player.setLoops(1)
            
        self.player.play()

    def on_preview_error(self, error_msg):
        QMessageBox.warning(self, "Preview Error", error_msg)
        self.btn_preview.setEnabled(True)
        self.btn_preview.setText("Voice Preview")
        self.btn_preview.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")

    def on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.btn_preview.setEnabled(True)
            self.btn_preview.setText("Stop Preview")
            self.btn_preview.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")
        elif state == QMediaPlayer.StoppedState:
            self.btn_preview.setEnabled(True)
            self.btn_preview.setText("Voice Preview")
            self.btn_preview.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")

    def on_media_status_changed(self, status):
        # Handle end of media for looping with regeneration
        if status == QMediaPlayer.EndOfMedia and self.loop_enabled:
            # Regenerate with current settings and play again
            self.play_preview()

    def get_settings(self):
        friendly = self.voice_combo.currentText()
        
        # Pause settings always enabled
        sentence_pause = self.spin_sentence_pause.value() / 1000.0
        comma_pause = self.spin_comma_pause.value() / 1000.0
            
        return {
            "voice": self.voice_data.get(friendly, "af_sky"),
            "speed": self.speed_spin.value(),
            "sentence_pause": sentence_pause,
            "comma_pause": comma_pause
        }
