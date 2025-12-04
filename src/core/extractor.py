import fitz  # pymupdf
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import warnings

# Suppress ebooklib warnings
warnings.filterwarnings("ignore", category=UserWarning, module="ebooklib")
warnings.filterwarnings("ignore", category=FutureWarning, module="ebooklib")

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Chapter:
    title: str
    content: str
    order: int
    is_toc: bool = False

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

def extract_chapters_from_pdf(pdf_path) -> List[Chapter]:
    """
    Extracts chapters from a PDF file.
    For now, treats the entire PDF as a single chapter.
    """
    text = extract_text_from_pdf(pdf_path)
    return [Chapter(title="Full Text", content=text, order=1)], {}

def extract_text_from_epub(epub_path):
    """
    Extracts text from an EPUB file.
    """
    chapters = extract_chapters_from_epub(epub_path)
    return "\n".join([c.content for c in chapters])

def extract_chapters_from_epub(epub_path, skip_toc=False) -> List[Chapter]:
    """
    Extracts chapters from an EPUB file.
    """
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        raise ValueError(f"Failed to read EPUB: {e}")

    chapters = []
    
    # Helper to check if chapter should be skipped (TOC, Index, etc.)
    def is_skippable(title):
        if not title:
            return False
        t = title.lower().strip()
        
        # Explicit inclusions (keep these even if they match exclusion keywords)
        includes = ['introduction', 'preface', 'foreword', 'prologue', 'chapter']
        if any(x in t for x in includes):
            return False
            
        # Exact matches for exclusion
        excludes_exact = {
            'contents', 'table of contents', 'toc',
            'table of figures', 'list of figures', 'list of tables',
            'acknowledgments', 'acknowledgements',
            'title page', 'copyright', 'copyright page',
            'index',
            'notes', 'endnotes', 'bibliography', 'references', 'works cited',
            'about the author', 'colophon'
        }
        
        if t in excludes_exact:
            return True
            
        # Partial matches (be careful here)
        if 'copyright' in t: return True
        if 'acknowledgment' in t: return True
        
        return False

    # Map file names to TOC titles
    toc_map = {}
    
    def process_toc_item(item):
        if isinstance(item, (list, tuple)):
            # It's a section with children: (Link, [children])
            if len(item) >= 1:
                process_toc_item(item[0]) # Process the section link itself
            if len(item) >= 2 and isinstance(item[1], (list, tuple)):
                for child in item[1]:
                    process_toc_item(child)
        elif hasattr(item, 'href') and hasattr(item, 'title'):
            # It's a Link object
            href = item.href.split('#')[0]
            if href not in toc_map:
                toc_map[href] = item.title

    for item in book.toc:
        process_toc_item(item)

    # Get items from spine to ensure correct order
    for i, item_id in enumerate(book.spine):
        item = book.get_item_with_id(item_id[0])
        
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Remove image-related elements (captions, figures, etc.)
            # These won't be present in the audiobook
            for element in soup.find_all(['figure', 'figcaption', 'caption', 'img']):
                element.decompose()
            
            # Remove elements with image-related classes
            for element in soup.find_all(class_=re.compile(r'(image|figure|caption|illustration|photo|picture)', re.I)):
                element.decompose()
            
            # Remove elements with image-related ids
            for element in soup.find_all(id=re.compile(r'(image|figure|caption|illustration|photo|picture)', re.I)):
                element.decompose()
            
            # Try to find a title
            title = ""
            title_element = None
            
            # 1. Check TOC map first (most reliable)
            item_name = item.get_name()
            if item_name in toc_map:
                title = toc_map[item_name]
                # Find the element matching this title to remove it
                # We look for h1, h2, h3 with matching text
                for tag in ['h1', 'h2', 'h3']:
                    for header in soup.find_all(tag):
                        if title.lower() in header.get_text().strip().lower():
                            title_element = header
                            break
                    if title_element:
                        break
            
            # 2. Fallback to HTML headings
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text().strip()
                    title_element = h1
                elif soup.find('h2'):
                    h2 = soup.find('h2')
                    title = h2.get_text().strip()
                    title_element = h2
            
            # Remove the title element from the body if found
            if title_element:
                title_element.decompose()
            
            # 3. Fallback to item name
            if not title:
                title = item_name

            # Get text with proper spacing
            # Use space separator to avoid breaking words
            chapter_text = soup.get_text(separator=' ', strip=True)
            
            # Normalize excessive whitespace while preserving paragraph breaks
            # Replace multiple spaces with single space
            chapter_text = re.sub(r' +', ' ', chapter_text)
            # Clean up any remaining artifacts
            chapter_text = chapter_text.strip()
            
            if not chapter_text:
                continue

            chapter_is_toc = is_skippable(title)
            
            if skip_toc and chapter_is_toc:
                print(f"Skipping TOC chapter: {title}")
                continue

            chapters.append(Chapter(
                title=title,
                content=chapter_text,
                order=i + 1,
                is_toc=chapter_is_toc
            ))
            
    # Extract Metadata
    metadata = {
        "title": "Unknown Title",
        "author": "Unknown Author"
    }
    
    try:
        # Get Title
        titles = book.get_metadata('DC', 'title')
        if titles:
            metadata['title'] = titles[0][0]
            
        # Get Author
        authors = book.get_metadata('DC', 'creator')
        if authors:
            metadata['author'] = authors[0][0]
    except Exception as e:
        print(f"Error extracting metadata: {e}")

    return chapters, metadata
