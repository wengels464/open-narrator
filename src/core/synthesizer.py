from kokoro_onnx import Kokoro
import soundfile as sf
import os
import numpy as np
import onnxruntime as ort
from src.utils.config import KOKORO_MODEL_PATH, VOICES_BIN_PATH

class AudioSynthesizer:
    def __init__(self):
        if not os.path.exists(KOKORO_MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {KOKORO_MODEL_PATH}")
        if not os.path.exists(VOICES_BIN_PATH):
            raise FileNotFoundError(f"Voices not found at {VOICES_BIN_PATH}")
        
        # Enable GPU acceleration if available
        # kokoro_onnx checks ONNX_PROVIDER environment variable
        available_providers = ort.get_available_providers()
        
        # Try to use GPU, but fall back to CPU if it fails
        gpu_enabled = False
        if 'CUDAExecutionProvider' in available_providers:
            try:
                os.environ['ONNX_PROVIDER'] = 'CUDAExecutionProvider'
                print("Attempting GPU acceleration: NVIDIA CUDA")
                gpu_enabled = True
            except Exception as e:
                print(f"CUDA initialization failed: {e}")
                print("Falling back to CPU")
                if 'ONNX_PROVIDER' in os.environ:
                    del os.environ['ONNX_PROVIDER']
        elif 'DmlExecutionProvider' in available_providers:
            try:
                os.environ['ONNX_PROVIDER'] = 'DmlExecutionProvider'
                print("GPU acceleration enabled: DirectML")
                gpu_enabled = True
            except Exception as e:
                print(f"DirectML initialization failed: {e}")
                print("Falling back to CPU")
                if 'ONNX_PROVIDER' in os.environ:
                    del os.environ['ONNX_PROVIDER']
        
        if not gpu_enabled:
            print("Using CPU for synthesis")
        
        # Load Kokoro with the correct .bin file (no pickle workaround needed)
        self.kokoro = Kokoro(KOKORO_MODEL_PATH, VOICES_BIN_PATH)

    def synthesize_segment(self, text, voice_name='af_sarah', speed=1.0):
        """
        Synthesizes text to audio.
        Returns audio data (numpy array) and sample rate.
        """
        try:
            # Kokoro.create returns (audio, sample_rate)
            # audio is a numpy array
            audio, sample_rate = self.kokoro.create(
                text, 
                voice=voice_name, 
                speed=speed, 
                lang="en-us"
            )
            return audio, sample_rate
        except Exception as e:
            print(f"Error synthesizing text: {text[:50]}... Error: {e}")
            raise e

    def save_audio(self, audio, sample_rate, output_path):
        sf.write(output_path, audio, sample_rate)
