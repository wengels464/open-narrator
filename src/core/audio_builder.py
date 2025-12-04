import subprocess
import os
from mutagen.mp4 import MP4, MP4Cover

class M4BBuilder:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def combine_audio_chunks(self, audio_files, output_path, chapters=None, progress_callback=None):
        """
        Combines multiple audio files into one M4B file using FFmpeg.
        chapters: List of (title, start_time, end_time) tuples in seconds.
        progress_callback: Optional callback function(percent) to report progress.
        """
        # Create a file list for ffmpeg in the same directory as the audio files
        # This avoids issues with absolute paths and drive letters on Windows
        if not audio_files:
            raise ValueError("No audio files to combine")
            
        audio_dir = os.path.dirname(audio_files[0])
        list_file = os.path.join(audio_dir, "concat_list.txt")
        
        with open(list_file, 'w', encoding='utf-8') as f:
            for audio_file in audio_files:
                # Use absolute paths with forward slashes for FFmpeg on Windows
                # This is the most robust method
                abs_path = os.path.abspath(audio_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        metadata_file = None
        if chapters:
            metadata_file = output_path + ".metadata.txt"
            self._create_metadata_file(chapters, metadata_file)

        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", list_file
        ]

        if metadata_file:
            cmd.extend(["-i", metadata_file, "-map_metadata", "1"])

        cmd.extend([
            "-c:a", "aac",
            "-b:a", "64k", # Bitrate for audiobook
            "-f", "mp4",  # M4B files are MP4 containers
            "-y",
            output_path
        ])
        
        try:
            if progress_callback:
                # Emit progress during FFmpeg processing
                # Since we can't easily track FFmpeg progress, emit incremental updates
                progress_callback(10)  # Starting
                
            subprocess.run(cmd, check=True, capture_output=True)
            
            if progress_callback:
                progress_callback(90)  # FFmpeg complete
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg failed: {e.stderr.decode()}")
            raise e
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)
            if metadata_file and os.path.exists(metadata_file):
                os.remove(metadata_file)

    def _create_metadata_file(self, chapters, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(";FFMETADATA1\n")
            for title, start, end in chapters:
                f.write("[CHAPTER]\n")
                f.write("TIMEBASE=1/1000\n")
                f.write(f"START={int(start * 1000)}\n")
                f.write(f"END={int(end * 1000)}\n")
                f.write(f"title={title}\n")

    def add_metadata(self, file_path, title, author, cover_image_path=None):
        try:
            audio = MP4(file_path)
            audio["\xa9nam"] = title
            audio["\xa9ART"] = author
            audio["\xa9alb"] = title 
            
            if cover_image_path and os.path.exists(cover_image_path):
                with open(cover_image_path, "rb") as f:
                    audio["covr"] = [MP4Cover(f.read(), imageformat=MP4Cover.FORMAT_JPEG)]
            
            audio.save()
        except Exception as e:
            print(f"Failed to add metadata: {e}")
            # Don't raise, metadata is optional-ish
