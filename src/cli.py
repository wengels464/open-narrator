import argparse
import sys
import os
import shutil
import tempfile

# Add project root to sys.path to allow running script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.extractor import extract_chapters_from_pdf, extract_chapters_from_epub
from src.core.cleaner import clean_text, segment_text
from src.core.synthesizer import AudioSynthesizer
from src.core.audio_builder import M4BBuilder

def main():
    parser = argparse.ArgumentParser(description="OpenNarrator CLI")
    parser.add_argument("input_file", help="Path to PDF or EPUB file")
    parser.add_argument("--output", "-o", help="Output M4B file path", default="output.m4b")
    parser.add_argument("--voice", "-v", help="Voice name", default="af_sarah")
    parser.add_argument("--speed", "-s", type=float, help="Speed", default=1.0)
    parser.add_argument("--skip-toc", action="store_true", help="Skip Table of Contents chapters")
    parser.add_argument("--list-chapters", action="store_true", help="List chapters and exit")
    parser.add_argument("--start-chapter", type=int, help="Start from chapter number (1-based)")
    parser.add_argument("--end-chapter", type=int, help="End at chapter number (1-based)")
    parser.add_argument("--preview", action="store_true", help="Preview mode: synthesize only first 3 sentences per chapter")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return

    print(f"Processing {args.input_file}...")

    # 1. Extraction
    try:
        if args.input_file.lower().endswith(".pdf"):
            # PDF support is basic for now
            chapters = extract_chapters_from_pdf(args.input_file)
        elif args.input_file.lower().endswith(".epub"):
            chapters = extract_chapters_from_epub(args.input_file, skip_toc=args.skip_toc)
        else:
            print("Unsupported file format.")
            return
    except Exception as e:
        print(f"Extraction failed: {e}")
        return

    print(f"Found {len(chapters)} chapters.")

    if args.list_chapters:
        print("\nChapter List:")
        for ch in chapters:
            toc_mark = " [TOC]" if ch.is_toc else ""
            print(f"{ch.order}. {ch.title}{toc_mark} ({len(ch.content)} chars)")
        return

    # Filter chapters
    start_idx = 0
    end_idx = len(chapters)

    if args.start_chapter:
        start_idx = max(0, args.start_chapter - 1)
    if args.end_chapter:
        end_idx = min(len(chapters), args.end_chapter)
    
    selected_chapters = chapters[start_idx:end_idx]
    
    if not selected_chapters:
        print("No chapters selected.")
        return

    print(f"Processing {len(selected_chapters)} chapters (from {start_idx+1} to {end_idx})...")

    # Initialize Synthesizer
    try:
        synthesizer = AudioSynthesizer()
    except Exception as e:
        print(f"Failed to initialize synthesizer: {e}")
        return

    temp_dir = tempfile.mkdtemp()
    all_audio_files = []
    chapter_metadata = [] # List of (title, start, end)
    current_timestamp = 0.0

    try:
        for i, chapter in enumerate(selected_chapters):
            print(f"\nProcessing Chapter {chapter.order}: {chapter.title}")
            
            # Cleaning & Segmentation
            text = clean_text(chapter.content)
            sentences = segment_text(text)
            print(f"  - {len(sentences)} sentences")

            if not sentences:
                continue

            chapter_start_time = current_timestamp
            
            # Synthesis
            count = 0
            for j, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                
                if args.preview and count >= 3:
                    break

                try:
                    # print(f"    Synthesizing sentence {j+1}/{len(sentences)}...", end='\r')
                    audio, sample_rate = synthesizer.synthesize_segment(sentence, voice_name=args.voice, speed=args.speed)
                    
                    # Calculate duration
                    duration = len(audio) / sample_rate
                    
                    output_wav = os.path.join(temp_dir, f"ch{chapter.order}_seg{j:04d}.wav")
                    synthesizer.save_audio(audio, sample_rate, output_wav)
                    
                    all_audio_files.append(output_wav)
                    current_timestamp += duration
                    count += 1
                except Exception as e:
                    print(f"\n    Failed to synthesize sentence {j+1}: {e}")
            
            chapter_end_time = current_timestamp
            chapter_metadata.append((chapter.title, chapter_start_time, chapter_end_time))
            print(f"  - Chapter processed. Duration: {chapter_end_time - chapter_start_time:.2f}s")

        if not all_audio_files:
            print("No audio generated.")
            return

        # 4. Assembly
        print("\nAssembling M4B...")
        try:
            builder = M4BBuilder()
            # Pass chapter metadata
            builder.combine_audio_chunks(all_audio_files, args.output, chapters=chapter_metadata)
            
            # Add basic metadata
            title = os.path.splitext(os.path.basename(args.input_file))[0]
            builder.add_metadata(args.output, title=title, author="OpenNarrator")
            
            print(f"Done! Saved to {args.output}")
        except Exception as e:
            print(f"Assembly failed: {e}")
            
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
