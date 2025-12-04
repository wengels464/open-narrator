import pysbd
import re

def clean_text(text):
    """
    Normalizes quotes, whitespace, and removes common artifacts.
    """
    # Normalize quotes
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # Convert em dashes and en dashes to periods (treat as sentence breaks)
    text = text.replace('—', '.') # Em dash
    text = text.replace('–', '.') # En dash
    text = text.replace('- ', '. ') # Hyphen with space (often used as informal em dash)
    
    # Remove footnote references like [1], [12]
    text = re.sub(r'\[\d+\]', '', text)
    
    # Remove standalone numbers that look like footnotes (e.g., at end of sentence or word)
    # This is a heuristic: remove numbers that appear after a word character, possibly with a space
    # Be careful not to remove years or quantities. 
    # Strategy: Remove numbers that are NOT preceded by a currency symbol or 'No.' and are at the end of a sentence.
    # For now, let's stick to the user's request "numbers that stand for footnotes" which are often just [n] or superscript.
    # If the user means just plain numbers at the end of sentences:
    # text = re.sub(r'(?<=[a-zA-Z.,])\d+', '', text) # Too aggressive?
    
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
