import fitz  # pymupdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import warnings

# Suppress ebooklib warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib")
warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib")

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        # Get text blocks to potentially filter headers/footers later
        # For now, just get all text
        text.append(page.get_text())
    
    return "\n".join(text)

def extract_text_from_epub(epub_path):
    """
    Extracts text from an EPUB file.
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        raise ValueError(f"Failed to read EPUB: {e}")

    text = []
    
    # Iterate through items
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            chapter_text = soup.get_text(separator='\n')
            text.append(chapter_text)
            
    return "\n".join(text)
