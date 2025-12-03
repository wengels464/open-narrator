import sys
import os
import traceback

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.synthesizer import AudioSynthesizer

print("Testing AudioSynthesizer initialization...")

try:
    synth = AudioSynthesizer()
    print("✓ AudioSynthesizer initialized successfully!")
    
    # Test a simple synthesis
    print("\nTesting synthesis with a short sentence...")
    audio, sample_rate = synth.synthesize_segment("Hello, this is a test.", voice_name="af_sarah")
    print(f"✓ Synthesis successful! Audio shape: {audio.shape}, Sample rate: {sample_rate}")
except Exception:
    print("✗ Error occurred:")
    traceback.print_exc()

