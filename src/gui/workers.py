from PySide6.QtCore import QThread, Signal, QObject
import os
import time
import tempfile
import shutil
import torch
from src.core.extractor import extract_chapters_from_pdf, extract_chapters_from_epub
from src.core.cleaner import clean_text, segment_text
from src.core.synthesizer import AudioSynthesizer
from src.core.audio_builder import M4BBuilder

class ExtractionWorker(QThread):
    finished = Signal(list, dict) # Emits (chapters, metadata)
    error = Signal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            if self.file_path.lower().endswith(".pdf"):
                chapters, metadata = extract_chapters_from_pdf(self.file_path)
            elif self.file_path.lower().endswith(".epub"):
                # Don't skip TOC here, let user decide in GUI
                chapters, metadata = extract_chapters_from_epub(self.file_path, skip_toc=False)
            else:
                raise ValueError("Unsupported file format")
            
            self.finished.emit(chapters, metadata)
        except Exception as e:
            self.error.emit(str(e))

class SynthesisWorker(QThread):
    progress_update = Signal(int, int) # current, total
    eta_update = Signal(str) # "MM:SS remaining"
    log_message = Signal(str)
    finished = Signal()
    error = Signal(str)
    cancelled = Signal(str) # Emits partial file path when cancelled

    def __init__(self, chapters, output_path, voice, speed, metadata=None):
        super().__init__()
        self.chapters = chapters
        self.output_path = output_path
        self.voice = voice
        self.speed = speed
        self.metadata = metadata or {}
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        temp_dir = tempfile.mkdtemp()
        all_audio_files = []
        chapter_metadata = []
        current_timestamp = 0.0
        
        start_time = time.time()
        total_chapters = len(self.chapters)
        chapters_processed = 0
        
        try:
            # Initialize Synthesizer
            self.log_message.emit("Initializing synthesizer...")
            synthesizer = AudioSynthesizer()
            
            # 1. Synthesize Intro Announcement
            if self.metadata.get('title'):
                title = self.metadata.get('title', 'Unknown Title')
                author = self.metadata.get('author', 'Unknown Author')
                intro_text = f"The following is a machine-generated audiobook created using Open Narrator. {title}. by {author}."
                
                self.log_message.emit("Synthesizing intro announcement...")
                try:
                    audio, sr = synthesizer.synthesize_segment(intro_text, voice_name=self.voice, speed=self.speed)
                    duration = len(audio) / sr
                    # Use absolute path for intro.wav
                    output_wav = os.path.abspath(os.path.join(temp_dir, "intro.wav"))
                    synthesizer.save_audio(audio, sr, output_wav)
                    
                    all_audio_files.append(output_wav)
                    current_timestamp += duration
                except Exception as e:
                    self.log_message.emit(f"Error synthesizing intro: {e}")

            for i, chapter in enumerate(self.chapters):
                if self._is_cancelled:
                    break
                    
                self.log_message.emit(f"Processing Chapter {i+1}/{total_chapters}: {chapter.title}")
                
                # Clean & Segment
                text = clean_text(chapter.content)
                sentences = segment_text(text)
                
                if not sentences:
                    chapters_processed += 1
                    continue
                    
                chapter_start_time = current_timestamp
                
                # Synthesize sentences
                total_sentences = len(sentences)
                for j, sentence in enumerate(sentences):
                    if self._is_cancelled:
                        break
                        
                    if not sentence.strip():
                        continue
                        
                    try:
                        audio, sample_rate = synthesizer.synthesize_segment(
                            sentence, 
                            voice_name=self.voice, 
                            speed=self.speed
                        )
                        
                        duration = len(audio) / sample_rate
                        output_wav = os.path.join(temp_dir, f"ch{i}_seg{j:04d}.wav")
                        synthesizer.save_audio(audio, sample_rate, output_wav)
                        
                        all_audio_files.append(output_wav)
                        current_timestamp += duration
                        
                        # Update progress within chapter
                        percent = int(((j + 1) / total_sentences) * 100)
                        self.progress_update.emit(i, percent)
                        
                    except Exception as e:
                        self.log_message.emit(f"Error synthesizing sentence: {e}")
                
                chapter_end_time = current_timestamp
                chapter_metadata.append((chapter.title, chapter_start_time, chapter_end_time))
                
                # Ensure 100% at end of chapter
                self.progress_update.emit(i, 100)
                
                # Calculate ETA
                chapters_processed += 1
                elapsed = time.time() - start_time
                avg_time_per_chapter = elapsed / chapters_processed
                remaining_chapters = total_chapters - chapters_processed
                eta_seconds = int(avg_time_per_chapter * remaining_chapters)
                
                mins, secs = divmod(eta_seconds, 60)
                self.eta_update.emit(f"ETA: {mins}m {secs}s")
            
            
            if self._is_cancelled:
                # Build partial M4B file if we have any audio
                if all_audio_files:
                    try:
                        self.log_message.emit("Building partial audiobook...")
                        builder = M4BBuilder()
                        builder.combine_audio_chunks(all_audio_files, self.output_path, chapters=chapter_metadata)
                        title = os.path.splitext(os.path.basename(self.output_path))[0]
                        builder.add_metadata(self.output_path, title=title, author="OpenNarrator")
                        self.cancelled.emit(self.output_path)  # Emit path for user to decide
                    except Exception as e:
                        self.log_message.emit(f"Error building partial file: {e}")
                        self.error.emit("Conversion cancelled.")
                else:
                    self.log_message.emit("Conversion cancelled.")
                return

            if not all_audio_files:
                self.error.emit("No audio generated.")
                return

            # Assembly
            self.log_message.emit("Assembling M4B file...")
            builder = M4BBuilder()
            builder.combine_audio_chunks(all_audio_files, self.output_path, chapters=chapter_metadata)
            
            title = os.path.splitext(os.path.basename(self.output_path))[0]
            builder.add_metadata(self.output_path, title=title, author="OpenNarrator")
            
            self.log_message.emit(f"Successfully saved to {self.output_path}")
            
            # Explicitly clean up synthesizer to free GPU memory
            self.log_message.emit("Releasing GPU resources...")
            del synthesizer
            if 'torch' in globals():
                torch.cuda.empty_cache()
            
            # Clean up temp files
            self.log_message.emit("Cleaning up temporary files...")
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.log_message.emit("Cleanup complete.")
                except Exception as e:
                    self.log_message.emit(f"Warning: Failed to clean up temp dir: {e}")
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Final safety check
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
