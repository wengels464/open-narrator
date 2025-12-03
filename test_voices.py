"""
Enhanced CLI for testing different voices and speeds to find the best naturalness.
Generates multiple versions of a sample with different settings.
"""
import argparse
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.synthesizer import AudioSynthesizer

def main():
    parser = argparse.ArgumentParser(description="Test Kokoro TTS voices and speeds")
    parser.add_argument("--text", "-t", default="Hello, this is a test of the Kokoro text to speech system. The quick brown fox jumps over the lazy dog.", 
                       help="Text to synthesize")
    parser.add_argument("--voices", "-v", nargs="+", 
                       default=["af_sarah", "af_bella", "af_nicole", "am_adam", "am_michael"],
                       help="Voices to test (space-separated)")
    parser.add_argument("--speeds", "-s", nargs="+", type=float,
                       default=[0.8, 0.9, 1.0, 1.1],
                       help="Speeds to test (space-separated)")
    parser.add_argument("--output-dir", "-o", default="voice_tests",
                       help="Output directory for test files")
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("Initializing synthesizer...")
    synth = AudioSynthesizer()
    
    print(f"\nGenerating {len(args.voices)} voices × {len(args.speeds)} speeds = {len(args.voices) * len(args.speeds)} samples")
    print("=" * 60)
    
    for voice in args.voices:
        for speed in args.speeds:
            filename = f"{voice}_speed{speed:.1f}.wav"
            output_path = os.path.join(args.output_dir, filename)
            
            try:
                print(f"Generating: {filename}...", end=" ")
                audio, sr = synth.synthesize_segment(args.text, voice_name=voice, speed=speed)
                synth.save_audio(audio, sr, output_path)
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"✓ Samples saved to: {args.output_dir}/")
    print("\nRecommendations for audiobook narration:")
    print("  - Female voices: af_bella, af_nicole, af_sarah")
    print("  - Male voices: am_adam, am_michael, am_liam")
    print("  - Speed: 0.9-1.0 for natural pacing")
    print("  - For more expressive: try af_nova, am_echo")

if __name__ == "__main__":
    main()
