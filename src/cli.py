import argparse
import sys
import os

# Add project root to sys.path to allow running script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.extractor import extract_text_from_pdf, extract_text_from_epub
from src.core.cleaner import clean_text, segment_text
from src.core.synthesizer import AudioSynthesizer
from src.core.audio_builder import M4BBuilder
import tempfile
import shutil

def main():
    parser = argparse.ArgumentParser(description="OpenNarrator CLI")
    parser.add_argument("input_file", help="Path to PDF or EPUB file")
    parser.add_argument("--output", "-o", help="Output M4B file path", default="output.m4b")
    parser.add_argument("--voice", "-v", help="Voice name", default="af_sarah")
    parser.add_argument("--speed", "-s", type=float, help="Speed", default=1.0)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return

    print(f"Processing {args.input_file}...")
    
    # 1. Extraction
    try:
        if args.input_file.lower().endswith(".pdf"):
            text = extract_text_from_pdf(args.input_file)
        elif args.input_file.lower().endswith(".epub"):
            text = extract_text_from_epub(args.input_file)
        else:
            print("Unsupported file format.")
            return
    except Exception as e:
        print(f"Extraction failed: {e}")
        return
        
    print(f"Extracted {len(text)} characters.")
    
    # 2. Cleaning & Segmentation
    text = clean_text(text)
    sentences = segment_text(text)
    print(f"Segmented into {len(sentences)} sentences.")
    
    # 3. Synthesis
    try:
        synthesizer = AudioSynthesizer()
    except Exception as e:
        print(f"Failed to initialize synthesizer: {e}")
        return

    temp_dir = tempfile.mkdtemp()
    audio_files = []
    
    try:
        # Limit for testing
        max_sentences = 5
        print(f"Synthesizing first {max_sentences} sentences for demo...")
        
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            
            if i >= max_sentences:
                break
                
            print(f"Synthesizing sentence {i+1}...")
            try:
                audio, sample_rate = synthesizer.synthesize_segment(sentence, voice_name=args.voice, speed=args.speed)
                
                output_wav = os.path.join(temp_dir, f"segment_{i:04d}.wav")
                synthesizer.save_audio(audio, sample_rate, output_wav)
                audio_files.append(output_wav)
            except Exception as e:
                print(f"Failed to synthesize sentence {i+1}: {e}")
        
        if not audio_files:
            print("No audio generated.")
            return

        # 4. Assembly
        print("Assembling M4B...")
        try:
            builder = M4BBuilder()
            builder.combine_audio_chunks(audio_files, args.output)
            builder.add_metadata(args.output, title="Test Audiobook", author="OpenNarrator")
            print(f"Done! Saved to {args.output}")
        except Exception as e:
            print(f"Assembly failed: {e}")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
