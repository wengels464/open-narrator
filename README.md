# OpenNarrator

A modern desktop application for converting EPUB and PDF books into high-quality M4B audiobooks using AI voice synthesis.

## Features

- 🎙️ **AI Voice Synthesis**: Uses Kokoro-82M ONNX model for natural-sounding narration
- 📚 **Multiple Formats**: Supports EPUB and PDF input files
- 🎨 **Modern GUI**: Dark-themed PySide6 interface with drag-and-drop
- ✏️ **Text Editor**: Edit chapter content before conversion
- 📊 **Progress Tracking**: Per-chapter progress bars and ETA display
- 🎯 **GPU Acceleration**: Automatic detection and use of NVIDIA CUDA
- 🔊 **Voice Preview**: Test voices before conversion
- 📖 **Chapter Detection**: Automatic chapter extraction and filtering
- 🎵 **M4B Output**: Properly formatted audiobooks with chapter markers

## Installation

### Prerequisites

- Python 3.10 or higher
- FFmpeg (for audio processing)
- Windows 10/11 (other platforms may work but are untested)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/wengels464/open-narrator.git
cd open-narrator
```

2. Create a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Download AI models and voices:

```bash
python setup_resources.py
```

This will download:

- `kokoro-v1.0.onnx` (310 MB) - AI voice model
- `voices-v1.0.bin` (2 MB) - Voice embeddings

## Usage

### GUI Mode

```bash
python main.py
```

1. Drag and drop an EPUB or PDF file
2. Select chapters to include
3. Choose voice and speed settings
4. Click "Convert to Audiobook"

### CLI Mode

```bash
python src/cli.py "path/to/book.epub" --output "audiobook.m4b" --voice af_sarah --speed 1.0
```

## Available Voices

See [VOICE_GUIDE.md](VOICE_GUIDE.md) for a complete list of available voices in multiple languages.

## Project Structure

```
open-narrator/
├── src/
│   ├── core/           # Core logic (extraction, synthesis, building)
│   ├── gui/            # PySide6 GUI components
│   └── utils/          # Utilities and configuration
├── assets/
│   ├── models/         # AI models (downloaded by setup_resources.py)
│   └── voices/         # Voice embeddings (downloaded by setup_resources.py)
├── main.py             # GUI entry point
└── setup_resources.py  # Downloads required models
```

## License

MIT License - See LICENSE file for details

## Credits

- [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) - AI voice synthesis model
- Built with PySide6, ebooklib, PyPDF2, and FFmpeg
