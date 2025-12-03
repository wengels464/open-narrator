import subprocess
import os
from mutagen.mp4 import MP4, MP4Cover

class M4BBuilder:
    def __init__(self, ffmpeg_path="ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    def combine_audio_chunks(self, audio_files, output_path):
        """
        Combines multiple audio files into one M4B file using FFmpeg.
        """
        # Create a file list for ffmpeg
        list_file = output_path + ".list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for audio_file in audio_files:
                # Escape paths if needed
                # FFmpeg concat demuxer requires 'file path' format
                # Windows paths with backslashes need to be escaped or use forward slashes
                safe_path = audio_file.replace('\\', '/')
                f.write(f"file '{safe_path}'\n")
        
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:a", "aac",
            "-b:a", "64k", # Bitrate for audiobook
            "-f", "mp4",  # M4B files are MP4 containers
            "-y",
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg failed: {e.stderr.decode()}")
            raise e
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)

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
