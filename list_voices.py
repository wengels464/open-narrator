"""
List all available voices in the Kokoro TTS model and generate samples.
"""
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.synthesizer import AudioSynthesizer

def main():
    # Load voices
    voices_path = "assets/voices/voices-v1.0.bin"
    voices = np.load(voices_path, allow_pickle=True)
    
    print("Available Kokoro TTS Voices:")
    print("=" * 50)
    
    voice_list = sorted(voices.keys())
    for i, voice in enumerate(voice_list, 1):
        print(f"{i:2d}. {voice}")
    
    print("\n" + "=" * 50)
    print(f"Total: {len(voice_list)} voices")
    print("\nVoice naming convention:")
    print("  - Prefix: af (adult female), am (adult male)")
    print("  - Name: character/style identifier")
    
    # Optional: Generate samples
    generate = input("\nGenerate sample audio for all voices? (y/n): ").lower()
    if generate == 'y':
        sample_text = "Hello, this is a test of the Kokoro text to speech system."
        synth = AudioSynthesizer()
        
        os.makedirs("voice_samples", exist_ok=True)
        
        for voice in voice_list:
            try:
                print(f"Generating sample for {voice}...")
                audio, sr = synth.synthesize_segment(sample_text, voice_name=voice)
                output_path = f"voice_samples/{voice}_sample.wav"
                synth.save_audio(audio, sr, output_path)
                print(f"  ✓ Saved to {output_path}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    main()
