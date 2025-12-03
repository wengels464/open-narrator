# **OpenNarrator: Software Design Specification**

## **1\. Executive Summary**

**OpenNarrator** is a Free and Open Source Software (FOSS) application designed to convert PDF and EPUB eBooks into chapterized, metadata-rich M4B audiobooks.

The core philosophy of OpenNarrator is **Local Sovereignty**:

1. **Zero API Calls:** No data ever leaves the user's machine.  
2. **Batteries Included:** All models, voices, and dependencies are bundled.  
3. **Cross-Platform Parity:** Identical functionality on Windows, macOS, and Linux.

## **2\. Technical Architecture**

### **2.1 High-Level Stack**

* **Language:** Python 3.11+  
* **GUI Framework:** **PySide6 (Qt for Python)**. Chosen for its native look-and-feel, robust heavy-lifting capabilities on desktop, and excellent support for accessibility (screen readers).  
* **TTS Engine:** **Kokoro-82M (ONNX version)**. A cutting-edge 82-million parameter model that runs faster than real-time on modest hardware while providing "ElevenLabs-quality" prosody.  
* **Audio Processing:** **FFmpeg** (static build bundled) for encoding AAC/M4B and concatenating audio streams.  
* **Metadata Engine:** **Mutagen** for ID3/M4B tagging and cover art embedding.

### **2.2 Application Flow**

1. **Ingestion:**  
   * User drags PDF/EPUB into GUI.  
   * **PDF Parsing:** pymupdf (MuPDF) extracts text, respecting layout to avoid reading headers/footers.  
   * **EPUB Parsing:** ebooklib extracts compliant HTML/text.  
2. **Preprocessing:**  
   * Text is cleaned (smart quote normalization, removal of "Page X of Y").  
   * Text is segmented into sentences using pysbd (pragmatic sentence boundary disambiguation) to ensure smooth TTS flow.  
3. **Synthesis (The Pipeline):**  
   * Segments are sent to the **Kokoro ONNX** inference engine.  
   * **GPU Acceleration:** The engine initializes ONNX Runtime. It automatically attempts to load the CUDAExecutionProvider (NVIDIA) or CoreMLExecutionProvider (Apple Silicon). If unavailable, it falls back to CPU (which remains highly performant for this specific model).  
4. **Assembly:**  
   * Raw PCM audio is streamed into an FFmpeg pipe.  
   * FFmpeg encodes to AAC (LC-AAC) inside an M4B container.  
   * Chapter markers are calculated based on the input text structure and inserted into the metadata.  
5. **Finalization:**  
   * User-uploaded cover image is resized and embedded.  
   * Final .m4b file is written to disk.

## **3\. Voice Model Selection & Strategy**

The requirement for "six distinct, natural English voices" is satisfied by bundling the **Kokoro-82M** voice packs. These are not merely different pitches of the same voice, but distinct speaker embeddings trained on different datasets.

**Selected Voice Roster:**

1. **Bella (US-Female):** *The Standard.* Professional, articulate, improved American accent. Ideal for non-fiction and business books.  
2. **Sarah (US-Female):** *The Storyteller.* Softer, slightly breathy, high emotional range. Perfect for fiction and romance.  
3. **Adam (US-Male):** *The Anchor.* Deep, resonant, authoritative. Excellent for biographies and history.  
4. **Michael (US-Male):** *The Conversationalist.* Higher pitch, faster paced, casual tone. Good for modern thrillers or blogs-to-audio.  
5. **Emma (UK-Female):** *The Classic.* Received Pronunciation (RP), elegant and precise. Ideal for classic literature (Austen, Brontë).  
6. **George (UK-Male):** *The Professor.* Warm, older British male voice. Perfect for academic texts or fantasy narration (e.g., Tolkien-esque).

*Why Kokoro?* Unlike Piper (which is faster but robotic) or StyleTTS2 (which is heavy and complex to bundle), Kokoro is an 80MB model that sounds nearly indistinguishable from human speech and is permissive (Apache 2.0).

## **4\. Packaging & Distribution Strategy**

To meet the "no installer" and "cross-platform" requirements, we will use a "Fat Binary" approach.

### **4.1 Dependency Bundling**

* **Model Weights:** The .onnx model (\~300MB quantized or \~600MB fp32) and voice .bin files will be downloaded during the GitHub Actions build process and baked into the executable's \_MEIPASS (temp) directory.  
* **FFmpeg:** A static, stripped-down build of FFmpeg (audio-only) will be bundled to ensure the user does not need to install it manually.

### **4.2 Platform Specifics**

#### **Windows (exe)**

* **Tool:** PyInstaller.  
* **Format:** Single-file Executable (--onefile).  
* **Note:** The first launch will be slightly slower as it unpacks the model to a temporary directory, but this satisfies the "no installer" rule.

#### **macOS (dmg)**

* **Tool:** PyInstaller \+ create-dmg.  
* **Format:** .app bundle inside a verified DMG.  
* **Acceleration:** Explicit support for CoreML provider in ONNX Runtime to leverage the Neural Engine on M1/M2/M3 chips.

#### **Linux (AppImage)**

* **Tool:** AppImageBuilder.  
* **Format:** A single .AppImage file containing the python runtime, glibc fallbacks, and the model.  
* **Justification:** AppImages run on almost any distro without installation, fitting the portable ethos.

#### **Docker**

* **Base Image:** python:3.11-slim.  
* **Behavior:** The container will expose a volume for /input and /output. When run, it watches the input folder, converts any new PDF/EPUB, and places the M4B in output.  
* **GPU:** The Docker image will come in two flavors: opennarrator:cpu and opennarrator:cuda (based on nvidia/cuda base image).

## **5\. Privacy & Offline Verification**

To guarantee the "Private" aspect:

1. **Source Code Audit:** The repo will contain a network\_lock.py module. In the production build, socket libraries will be monkey-patched to raise errors if any outgoing connection is attempted after the initial model verification (which happens at build time, not runtime).  
2. **Air-Gap Ready:** The software will be tested in fully air-gapped environments (VMs with disabled NICs) to ensure no silent crashes occur due to missing update checks.

## **6\. Implementation Roadmap**

### **Phase 1: Core Logic (CLI)**

* Implement TextExtractor for PDF/EPUB.  
* Implement AudioSynthesizer using kokoro-onnx.  
* Implement M4BBuilder using FFmpeg.

### **Phase 2: GUI Development**

* Build Main Window in PySide6.  
* Create "Voice Preview" buttons (playing pre-rendered samples to avoid lag).  
* Add "Chapter Editor" (allow users to manually adjust where chapter breaks occur before rendering).

### **Phase 3: Packaging**

* Set up GitHub Actions for automated building of EXE, DMG, and AppImage.  
* Optimize model size (investigate fp16 ONNX quantization to reduce bundle size).

## **7\. System Requirements (Estimated)**

* **RAM:** 4GB Minimum (8GB recommended for long books).  
* **Disk Space:** \~800MB (Application \+ Models).  
* **GPU:** Optional.  
  * NVIDIA RTX 2000+ (for CUDA acceleration).  
  * Apple M1+ (for CoreML acceleration).  
  * Modern CPU (Ryzen 5000+ / Intel 11th Gen+) is sufficient for 3x-5x real-time generation.