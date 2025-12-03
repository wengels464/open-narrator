import pysbd
import re

def clean_text(text):
    """
    Normalizes quotes, whitespace, and removes common artifacts.
    """
    # Normalize quotes
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def segment_text(text, language='en'):
    """
    Segments text into sentences using pysbd.
    """
    seg = pysbd.Segmenter(language=language, clean=False)
    return seg.segment(text)
