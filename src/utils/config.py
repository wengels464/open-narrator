import os
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_PATH = get_base_path()
ASSETS_DIR = os.path.join(BASE_PATH, 'assets')
MODELS_DIR = os.path.join(ASSETS_DIR, 'models')
VOICES_DIR = os.path.join(ASSETS_DIR, 'voices')

KOKORO_MODEL_PATH = os.path.join(MODELS_DIR, 'kokoro-v1.0.onnx')
VOICES_BIN_PATH = os.path.join(VOICES_DIR, 'voices-v1.0.bin')
