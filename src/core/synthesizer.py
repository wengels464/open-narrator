from kokoro import KPipeline
import soundfile as sf
import os
import numpy as np
import torch
from src.utils.config import KOKORO_MODEL_PATH, VOICES_BIN_PATH

class AudioSynthesizer:
    def __init__(self):
        # Determine device
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Initializing Kokoro TTS on {self.device}...")
        
        try:
            # Initialize pipeline for American English
            # lang_code='a' is for American English in Kokoro
            self.pipeline = KPipeline(lang_code='a', device=self.device)
            print(f"Kokoro initialized successfully on {self.device}")
        except Exception as e:
            print(f"Failed to initialize Kokoro: {e}")
            if self.device == 'cuda':
                print("Falling back to CPU...")
                self.device = 'cpu'
                self.pipeline = KPipeline(lang_code='a', device='cpu')
            else:
                raise e

    def synthesize_segment(self, text, voice_name='af_sarah', speed=1.0):
        """
        Synthesizes text to audio using Kokoro PyTorch pipeline.
        Returns audio data (numpy array) and sample rate.
        """
        try:
            # Generate audio
            # pipeline returns a generator of results
            generator = self.pipeline(
                text, 
                voice=voice_name, 
                speed=speed, 
                split_pattern=r'\n+'
            )
            
            # Collect all audio segments
            audio_segments = []
            sample_rate = 24000 # Kokoro default
            
            for result in generator:
                if hasattr(result, 'audio'):
                    audio_segments.append(result.audio)
                elif isinstance(result, tuple):
                    # Some versions might return tuple
                    audio_segments.append(result[0])
            
            if not audio_segments:
                return np.array([], dtype=np.float32), sample_rate
                
            # Concatenate all segments
            full_audio = np.concatenate(audio_segments)
            return full_audio, sample_rate
            
        except Exception as e:
            print(f"Error synthesizing text: {text[:50]}... Error: {e}")
            raise e

    def save_audio(self, audio, sample_rate, output_path):
        sf.write(output_path, audio, sample_rate)
