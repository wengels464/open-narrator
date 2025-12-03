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

def segment_text(text, language='en', max_chars=400):
    """
    Segments text into sentences using pysbd, then ensures no segment exceeds max_chars.
    """
    seg = pysbd.Segmenter(language=language, clean=False)
    initial_segments = seg.segment(text)
    
    final_segments = []
    for segment in initial_segments:
        if len(segment) <= max_chars:
            final_segments.append(segment)
        else:
            # Split long segments
            current_chunk = ""
            words = segment.split(' ')
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= max_chars:
                    current_chunk += (word + " ")
                else:
                    if current_chunk:
                        final_segments.append(current_chunk.strip())
                    current_chunk = word + " "
            
            if current_chunk:
                final_segments.append(current_chunk.strip())
                
    return final_segments
