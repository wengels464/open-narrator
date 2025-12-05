"""
Metadata fetching module for Open Narrator.
Uses Open Library API (primary) and Google Books API (fallback).
"""

import requests
import os
import tempfile
from PIL import Image
from io import BytesIO
from urllib.parse import quote

# Constants
COVER_SIZE = 2400
USER_AGENT = "OpenNarrator/1.0 (Audiobook Generator)"

class MetadataResult:
    """Container for book metadata."""
    def __init__(self):
        self.title = ""
        self.subtitle = ""
        self.author = ""
        self.translator = ""
        self.year = ""
        self.isbn = ""
        self.description = ""
        self.tags = []
        self.cover_url = ""
        self.cover_path = ""
        self.source = ""
    
    def to_dict(self):
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "author": self.author,
            "translator": self.translator,
            "year": self.year,
            "isbn": self.isbn,
            "description": self.description,
            "tags": self.tags,
            "cover_url": self.cover_url,
            "cover_path": self.cover_path,
            "source": self.source
        }


def search_open_library(title, author=None):
    """
    Search Open Library for book metadata.
    Returns MetadataResult or None if not found.
    """
    try:
        # Build search query
        query = quote(title)
        if author:
            query += f"+author:{quote(author)}"
        
        url = f"https://openlibrary.org/search.json?q={query}&limit=5"
        headers = {"User-Agent": USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("docs"):
            return None
        
        # Get best match (first result)
        book = data["docs"][0]
        
        result = MetadataResult()
        result.title = book.get("title", "")
        result.subtitle = book.get("subtitle", "")
        result.author = ", ".join(book.get("author_name", []))
        result.year = str(book.get("first_publish_year", ""))
        result.isbn = book.get("isbn", [""])[0] if book.get("isbn") else ""
        result.tags = book.get("subject", [])[:10]  # Limit to 10 tags
        result.source = "Open Library"
        
        # Get cover URL
        cover_id = book.get("cover_i")
        if cover_id:
            result.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        
        # Try to get description from work details
        work_key = book.get("key")
        if work_key:
            try:
                work_url = f"https://openlibrary.org{work_key}.json"
                work_resp = requests.get(work_url, headers=headers, timeout=5)
                if work_resp.ok:
                    work_data = work_resp.json()
                    desc = work_data.get("description")
                    if isinstance(desc, dict):
                        result.description = desc.get("value", "")
                    elif isinstance(desc, str):
                        result.description = desc
            except:
                pass
        
        return result
        
    except Exception as e:
        print(f"Open Library search error: {e}")
        return None


def search_google_books(title, author=None):
    """
    Search Google Books for book metadata.
    Returns MetadataResult or None if not found.
    """
    try:
        # Build search query
        query = title
        if author:
            query += f"+inauthor:{author}"
        
        url = f"https://www.googleapis.com/books/v1/volumes?q={quote(query)}&maxResults=5"
        headers = {"User-Agent": USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("items"):
            return None
        
        # Get best match
        book = data["items"][0]["volumeInfo"]
        
        result = MetadataResult()
        result.title = book.get("title", "")
        result.subtitle = book.get("subtitle", "")  # Google Books has explicit subtitle field
        result.author = ", ".join(book.get("authors", []))
        result.year = book.get("publishedDate", "")[:4]  # Extract year
        result.description = book.get("description", "")
        result.tags = book.get("categories", [])
        result.source = "Google Books"
        
        # Get ISBN
        identifiers = book.get("industryIdentifiers", [])
        for ident in identifiers:
            if ident.get("type") in ["ISBN_13", "ISBN_10"]:
                result.isbn = ident.get("identifier", "")
                break
        
        # Get cover URL (prefer larger images)
        image_links = book.get("imageLinks", {})
        result.cover_url = (
            image_links.get("extraLarge") or
            image_links.get("large") or
            image_links.get("medium") or
            image_links.get("thumbnail", "")
        )
        
        return result
        
    except Exception as e:
        print(f"Google Books search error: {e}")
        return None


def search_metadata(title, author=None):
    """
    Search for book metadata using Open Library, with Google Books fallback.
    Merges data from both sources to fill missing fields.
    Prefers author names with diacritics (e.g., "Martín" over "Martin").
    Returns MetadataResult or None if not found.
    """
    # Try Open Library first
    result = search_open_library(title, author)
    
    # Always try Google Books to fill missing fields
    google_result = search_google_books(title, author)
    
    if google_result:
        if not result:
            # Open Library failed, use Google Books
            result = google_result
        else:
            # Merge missing fields from Google Books
            if not result.subtitle and google_result.subtitle:
                result.subtitle = google_result.subtitle
                result.source += " + Google Books (subtitle)"
            if not result.isbn and google_result.isbn:
                result.isbn = google_result.isbn
            if not result.description and google_result.description:
                result.description = google_result.description
            if not result.cover_url and google_result.cover_url:
                result.cover_url = google_result.cover_url
                result.source += " + Google Books (cover)"
            if not result.year and google_result.year:
                result.year = google_result.year
            
            # Prefer author with diacritics (more Unicode characters = more complete)
            if google_result.author and _has_more_diacritics(google_result.author, result.author):
                result.author = google_result.author
                result.source += " + Google Books (author)"
    
    return result


def _has_more_diacritics(text1: str, text2: str) -> bool:
    """Check if text1 has more diacritic/Unicode characters than text2."""
    import unicodedata
    
    def count_accented(s):
        return sum(1 for c in s if unicodedata.category(c) in ('Mn', 'Mc', 'Me') or ord(c) > 127)
    
    return count_accented(text1) > count_accented(text2)


def download_and_process_cover(url, output_path=None):
    """
    Download cover image and resize to 2400x2400 square.
    Centers non-square images on black background.
    
    Returns path to processed image or None on failure.
    """
    if not url:
        return None
        
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Open image
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGB if necessary (for PNG with alpha)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Create square canvas
        canvas = Image.new('RGB', (COVER_SIZE, COVER_SIZE), (0, 0, 0))
        
        # Calculate scaling to fit within canvas
        img_ratio = img.width / img.height
        
        if img_ratio > 1:
            # Wider than tall
            new_width = COVER_SIZE
            new_height = int(COVER_SIZE / img_ratio)
        else:
            # Taller than wide or square
            new_height = COVER_SIZE
            new_width = int(COVER_SIZE * img_ratio)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center on canvas
        x_offset = (COVER_SIZE - new_width) // 2
        y_offset = (COVER_SIZE - new_height) // 2
        canvas.paste(img, (x_offset, y_offset))
        
        # Save to output path
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "cover_2400x2400.jpg")
        
        canvas.save(output_path, "JPEG", quality=95)
        return output_path
        
    except Exception as e:
        print(f"Cover download/processing error: {e}")
        return None


def process_local_cover(image_path, output_path=None):
    """
    Process a local cover image to 2400x2400 square.
    Centers non-square images on black background.
    
    Returns path to processed image or None on failure.
    """
    try:
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Create square canvas
        canvas = Image.new('RGB', (COVER_SIZE, COVER_SIZE), (0, 0, 0))
        
        # Calculate scaling to fit within canvas
        img_ratio = img.width / img.height
        
        if img_ratio > 1:
            new_width = COVER_SIZE
            new_height = int(COVER_SIZE / img_ratio)
        else:
            new_height = COVER_SIZE
            new_width = int(COVER_SIZE * img_ratio)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Center on canvas
        x_offset = (COVER_SIZE - new_width) // 2
        y_offset = (COVER_SIZE - new_height) // 2
        canvas.paste(img, (x_offset, y_offset))
        
        # Save to output path
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "cover_2400x2400.jpg")
        
        canvas.save(output_path, "JPEG", quality=95)
        return output_path
        
    except Exception as e:
        print(f"Local cover processing error: {e}")
        return None
