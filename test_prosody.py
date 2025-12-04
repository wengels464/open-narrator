from src.core.synthesizer import AudioSynthesizer
import numpy as np
import soundfile as sf
import os

def test_prosody():
    synth = AudioSynthesizer()
    voice = 'af_sarah'
    text = "They were careless people, Tom and Daisy- they smashed up things and creatures."
    
    print("Synthesizing standard version...")
    audio_std, sr = synth.synthesize_segment(text, voice_name=voice)
    sf.write("test_std.wav", audio_std, sr)
    
    print("Synthesizing split version...")
    # Split by comma/dash manually
    part1 = "They were careless people"
    part2 = "Tom and Daisy"
    part3 = "they smashed up things and creatures."
    
    a1, _ = synth.synthesize_segment(part1, voice_name=voice)
    a2, _ = synth.synthesize_segment(part2, voice_name=voice)
    a3, _ = synth.synthesize_segment(part3, voice_name=voice)
    
    # Add short silence (e.g. 100ms)
    silence = np.zeros(int(sr * 0.1), dtype=np.float32)
    
    audio_split = np.concatenate([a1, silence, a2, silence, a3])
    sf.write("test_split.wav", audio_split, sr)
    
    print("Done. Check test_std.wav and test_split.wav")
    
    # Inspect g2p output
    print("\nInspecting g2p output for 'Hello, world.'")
    text = "Hello, world."
    # g2p likely returns (graphemes, phonemes, tokens) or similar
    # Let's print whatever it returns
    try:
        result = synth.pipeline.g2p(text)
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
    except Exception as e:
        print(f"g2p failed: {e}")

if __name__ == "__main__":
    test_prosody()
