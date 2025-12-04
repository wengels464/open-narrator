import pysbd
import re

def clean_text(text):
    """
    Normalizes punctuation, removes artifacts, and prepares text for TTS.
    
    Allowed punctuation: . , : ; -
    Pause groupings:
      - Sentence pause (. ; -): treated as sentence breaks
      - Comma pause (, :): treated as phrase pauses
    """
    # Normalize smart quotes to standard quotes
    text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
    
    # Remove footnote patterns
    # Pattern 1: Bracketed numbers like [1], [12], [123]
    text = re.sub(r'\[\d+\]', '', text)
    # Pattern 2: Numbers in parentheses like (1), (12)
    text = re.sub(r'\(\d+\)', '', text)
    # Pattern 3: Inline footnotes after punctuation (e.g., ". 8 It" or ", 9 A")
    # Match space + 1-3 digit number + space before next capital letter
    text = re.sub(r'\s+\d{1,3}(?=\s+[A-Z])', '', text)
    # Pattern 4: Standalone footnote numbers at end of text
    text = re.sub(r'\s+\d{1,3}\s*$', '', text)
    # Pattern 5: Superscript-style numbers immediately after words (e.g., "word1")
    text = re.sub(r'(?<=[a-zA-Z"\'])\d{1,3}(?=[\s.,;:!?]|$)', '', text)
    
    # Normalize em dashes, en dashes to comma (phrase pause)
    text = text.replace('—', ',')  # Em dash → comma pause
    text = text.replace('–', ',')  # En dash → comma pause
    
    # Normalize colons to commas (same pause group)
    text = text.replace(':', ',')
    
    # Normalize semicolons to periods (sentence pause)
    text = text.replace(';', '.')
    
    # Remove decorative/non-standard punctuation
    # Remove repeated punctuation (e.g., "...", "---", "***")
    text = re.sub(r'\.{2,}', '.', text)  # Multiple periods → single period
    text = re.sub(r'-{2,}', '', text)    # Multiple hyphens → remove
    text = re.sub(r'_{2,}', '', text)    # Multiple underscores → remove
    text = re.sub(r'\*{2,}', '', text)   # Multiple asterisks → remove
    text = re.sub(r'#{2,}', '', text)    # Multiple hashes → remove
    text = re.sub(r'~{2,}', '', text)    # Multiple tildes → remove
    text = re.sub(r'={2,}', '', text)    # Multiple equals → remove
    
    # Remove remaining non-allowed punctuation (keep only . , - and alphanumerics/spaces)
    # Allowed: letters, digits, spaces, . , - ' "
    text = re.sub(r"[^\w\s.,'\"()-]", '', text)
    
    # Clean up hyphen usage: hyphen with space on either side becomes period
    text = re.sub(r'\s+-\s+', '. ', text)
    
    # Remove orphaned quotes
    text = re.sub(r'(?<!\w)"(?!\w)', '', text)
    text = re.sub(r"(?<!\w)'(?!\w)", '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Clean up multiple consecutive punctuation after processing
    text = re.sub(r'[.,]{2,}', '.', text)  # Multiple comma/period → period
    text = re.sub(r'\s+([.,])', r'\1', text)  # Remove space before punctuation
    
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
