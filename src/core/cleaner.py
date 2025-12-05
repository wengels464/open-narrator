import pysbd
import re
from num2words import num2words

def clean_text(text):
    """
    Normalizes punctuation, removes artifacts, and prepares text for TTS.
    
    Allowed punctuation: . , ? ! : ; -
    Pause groupings:
      - Sentence pause (. ? ! ; -): treated as sentence breaks
      - Comma pause (, :): treated as phrase pauses
    """
    # Normalize smart quotes to standard quotes
    text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
    
    # Normalize dates for better TTS reading
    # Convert "June 21, 2015" to "June 21st, 2015" 
    # Day ordinals: 1st, 2nd, 3rd, 4th-20th, 21st, 22nd, 23rd, 24th-30th, 31st
    def add_ordinal(match):
        day = int(match.group(2))
        month = match.group(1)
        year = match.group(3) if match.group(3) else ""
        
        if 11 <= day <= 13:
            suffix = "th"
        elif day % 10 == 1:
            suffix = "st"
        elif day % 10 == 2:
            suffix = "nd"
        elif day % 10 == 3:
            suffix = "rd"
        else:
            suffix = "th"
        
        # Remove comma before year for more natural reading
        if year:
            return f"{month} {day}{suffix} {year}"
        return f"{month} {day}{suffix}"
    
    # Pattern: Month DD, YYYY or Month DD
    months = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    text = re.sub(rf'{months}\s+(\d{{1,2}}),?\s*(\d{{4}})?', add_ordinal, text)
    
    # Also handle numeric dates like 12/25/2024 → December 25th 2024
    month_names = ["January", "February", "March", "April", "May", "June", 
                   "July", "August", "September", "October", "November", "December"]
    def convert_numeric_date(match):
        month_num = int(match.group(1))
        day = int(match.group(2))
        year = match.group(3)
        
        if 1 <= month_num <= 12:
            month = month_names[month_num - 1]
            if 11 <= day <= 13:
                suffix = "th"
            elif day % 10 == 1:
                suffix = "st"
            elif day % 10 == 2:
                suffix = "nd"
            elif day % 10 == 3:
                suffix = "rd"
            else:
                suffix = "th"
            return f"{month} {day}{suffix} {year}"
        return match.group(0)
    
    text = re.sub(r'(\d{1,2})/(\d{1,2})/(\d{4})', convert_numeric_date, text)
    
    # Expand common abbreviations for natural reading
    abbreviations = {
        r'\bDr\.': 'Doctor',
        r'\bMr\.': 'Mister',
        r'\bMrs\.': 'Missus',
        r'\bMs\.': 'Miss',
        r'\bProf\.': 'Professor',
        r'\bGen\.': 'General',
        r'\bSgt\.': 'Sergeant',
        r'\bLt\.': 'Lieutenant',
        r'\bCol\.': 'Colonel',
        r'\bCpt\.': 'Captain',
        r'\bSt\.': 'Saint',
        r'\bvs\.': 'versus',
        r'\betc\.': 'etcetera',
        r'\be\.g\.': 'for example',
        r'\bi\.e\.': 'that is',
        r'\bno\.': 'number',
        r'\bNo\.': 'Number',
        r'\bvol\.': 'volume',
        r'\bVol\.': 'Volume',
        r'\bp\.': 'page',
        r'\bpp\.': 'pages',
    }
    for abbr, expansion in abbreviations.items():
        text = re.sub(abbr, expansion, text)
    
    # Expand currency amounts (e.g., $5.99 → five dollars and ninety-nine cents)
    def expand_currency(match):
        symbol = match.group(1)
        dollars = int(match.group(2))
        cents = int(match.group(3)) if match.group(3) else 0
        
        currency_name = "dollars" if symbol == "$" else "pounds" if symbol == "£" else "euros"
        
        try:
            if cents > 0:
                return f"{num2words(dollars)} {currency_name} and {num2words(cents)} cents"
            else:
                return f"{num2words(dollars)} {currency_name}"
        except:
            return match.group(0)
    
    text = re.sub(r'([$£€])(\d+)(?:\.(\d{2}))?', expand_currency, text)
    
    # Expand large numbers with commas (e.g., 1,234,567 → one million two hundred...)
    def expand_large_number(match):
        num_str = match.group(0).replace(',', '')
        try:
            return num2words(int(num_str))
        except:
            return match.group(0)
    
    text = re.sub(r'\b\d{1,3}(?:,\d{3})+\b', expand_large_number, text)
    
    # Expand standalone years in context (e.g., "in 1984" stays as is, but "between 1984 and 1990")
    # Keep 4-digit years as-is since TTS handles them well
    
    # Expand percentages (e.g., 75% → seventy-five percent)
    def expand_percent(match):
        num = match.group(1)
        try:
            if '.' in num:
                return f"{num2words(float(num))} percent"
            else:
                return f"{num2words(int(num))} percent"
        except:
            return match.group(0)
    
    text = re.sub(r'(\d+(?:\.\d+)?)\s*%', expand_percent, text)
    
    # Add strategic pauses after transition words for better TTS prosody
    # These words benefit from a brief pause after them for emphasis
    transition_words = [
        r'\bHowever\b', r'\bTherefore\b', r'\bMeanwhile\b', r'\bSuddenly\b',
        r'\bFinally\b', r'\bUnfortunately\b', r'\bFortunately\b', r'\bMoreover\b',
        r'\bNevertheless\b', r'\bConsequently\b', r'\bFurthermore\b', r'\bIndeed\b',
        r'\bStill\b', r'\bThus\b', r'\bHence\b', r'\bOtherwise\b',
        r'\bhowever\b', r'\btherefore\b', r'\bmeanwhile\b', r'\bsuddenly\b',
        r'\bfinally\b', r'\bunfortunately\b', r'\bfortunately\b', r'\bmoreover\b',
        r'\bnevertheless\b', r'\bconsequently\b', r'\bfurthermore\b', r'\bindeed\b',
        r'\bstill\b', r'\bthus\b', r'\bhence\b', r'\botherwise\b',
    ]
    for word in transition_words:
        # Add comma after transition word if not already followed by punctuation
        text = re.sub(rf'({word})(?![,\.!?;:])', r'\1,', text)
    
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
    
    # Remove remaining non-allowed punctuation (keep only . , ? ! - and alphanumerics/spaces)
    # Allowed: letters (including Unicode/accented), digits, spaces, . , ? ! - ' "
    # Use explicit character class instead of \w to preserve Unicode letters
    text = re.sub(r"[^\w\s.,?!'\"\u00C0-\u024F()-]", '', text, flags=re.UNICODE)
    
    # Clean up hyphen usage: hyphen with space on either side becomes period
    text = re.sub(r'\s+-\s+', '. ', text)
    
    # Remove orphaned quotes
    text = re.sub(r'(?<!\w)"(?!\w)', '', text)
    text = re.sub(r"(?<!\w)'(?!\w)", '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Clean up multiple consecutive punctuation after processing
    text = re.sub(r'[.,]{2,}', '.', text)  # Multiple comma/period → period
    text = re.sub(r'\s+([.,?!])', r'\1', text)  # Remove space before punctuation
    
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
