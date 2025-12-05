"""
Pronunciation correction utilities for Open Narrator.
Detects difficult-to-pronounce words and looks up correct pronunciations.
"""

import re
import requests
from typing import List, Dict, Tuple, Optional


import pysbd

import enchant

# Initialize g2p-en for fallback pronunciation generation
try:
    from g2p_en import G2p
    _g2p = G2p()
except ImportError:
    _g2p = None

# Initialize English dictionary for word validation
try:
    _english_dict = enchant.Dict("en_US")
except enchant.errors.DictNotFoundError:
    try:
        _english_dict = enchant.Dict("en_GB")
    except enchant.errors.DictNotFoundError:
        _english_dict = None

def find_difficult_words(text: str, verbose: bool = False) -> List[str]:
    """
    Identify words that are likely difficult to pronounce.
    
    Only flags words that are:
    - NOT in the English dictionary (foreign names, surnames, non-English terms)
    - Capitalized mid-sentence (proper nouns)
    
    Standard English words (even if capitalized) are skipped.
    
    Returns list of unique difficult words.
    """
    if _english_dict is None:
        if verbose:
            print("DEBUG: English dictionary not available, falling back to pattern matching")
        return _find_difficult_words_fallback(text, verbose)
    
    difficult_words = set()
    
    # Use pysbd for better sentence segmentation
    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text)
    
    for sentence in sentences:
        words = sentence.split()
        
        for i, word in enumerate(words):
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w\'-]', '', word)
            if not clean_word or len(clean_word) < 3:
                continue
            
            # Skip if all caps (likely acronym)
            if clean_word.isupper():
                continue
            
            # Only consider words capitalized mid-sentence (proper nouns)
            if i == 0 or not clean_word[0].isupper():
                continue
            
            # Check if word is in English dictionary (case-insensitive)
            lower_word = clean_word.lower()
            
            # If it's a standard English word, skip it
            if _english_dict.check(lower_word) or _english_dict.check(clean_word):
                if verbose:
                    print(f"DEBUG: Skipping dictionary word: {clean_word}")
                continue
            
            # This is a proper noun NOT in the dictionary - likely a name/surname
            difficult_words.add(clean_word)
            if verbose:
                print(f"DEBUG: Found non-dictionary proper noun: {clean_word}")
    
    return sorted(list(difficult_words))


def _find_difficult_words_fallback(text: str, verbose: bool = False) -> List[str]:
    """
    Fallback method when dictionary is not available.
    Uses pattern matching to identify potentially difficult words.
    """
    difficult_words = set()
    
    # Use pysbd for better sentence segmentation
    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text)
    
    for sentence in sentences:
        words = sentence.split()
        
        for i, word in enumerate(words):
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w\'-]', '', word)
            if not clean_word or len(clean_word) < 3:
                continue
            
            # Skip if all caps (likely acronym)
            if clean_word.isupper():
                continue
            
            # Only consider words capitalized mid-sentence (proper nouns)
            if i == 0 or not clean_word[0].isupper():
                continue
            
            # Check for foreign-looking patterns (non-English letter combinations)
            lower = clean_word.lower()
            
            # Foreign patterns: multiple consecutive consonants, unusual combos
            if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', lower):
                difficult_words.add(clean_word)
                continue
            
            # Non-English letter patterns
            if re.search(r'(mb|chk|tch|sch|pn|gn|kn)[aeiou]', lower):
                difficult_words.add(clean_word)
                continue
            
            # Words with apostrophes in unusual positions (not contractions)
            if "'" in clean_word and not re.match(r".*'(s|t|d|ll|ve|re|m)$", lower):
                difficult_words.add(clean_word)
    
    return sorted(list(difficult_words))


def search_wikipedia_pronunciation(word: str) -> Optional[Dict[str, str]]:
    """
    Search Wiktionary for pronunciation information.
    Returns the first IPA pronunciation found on the page.
    
    Note: Future enhancement planned to detect language from sentence context
    and return the appropriate language-specific pronunciation.
    
    Returns dict with 'ipa' and 'source' if found, None otherwise.
    """
    headers = {
        "User-Agent": "OpenNarrator/1.0 (Audiobook Generator; https://github.com/opennarrator)"
    }
    
    try:
        api_url = "https://en.wiktionary.org/w/api.php"
        params = {
            "action": "query",
            "titles": word,
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "rvslots": "main"
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        
        page = list(pages.values())[0]
        if "revisions" not in page or page.get("missing") is not None:
            return None
        
        content = page["revisions"][0]["slots"]["main"]["*"]
        
        # IPA characters that indicate actual pronunciation (not URLs or other text)
        IPA_CHARS = r'[əɪɛæɑɔʊʌŋθðʃʒˈˌːˑɐɒɜɝɞɨʉɯɵøœɶɑ̃ɔ̃æ̃]'
        
        # Find IPA in standard Wiktionary format: {{IPA|lang|/pronunciation/}}
        # This is the most reliable pattern
        ipa_template_match = re.search(r'\{\{IPA\|[a-z]{2,3}\|(/[^/}]+/)', content)
        if ipa_template_match:
            ipa = ipa_template_match.group(1).strip()
            # Must contain at least one IPA character
            if re.search(IPA_CHARS, ipa):
                return {'ipa': ipa, 'source': 'Wiktionary'}
        
        # Alternative format: {{IPA|/pronunciation/}}
        ipa_template_match2 = re.search(r'\{\{IPA\|(/[^/}]+/)', content)
        if ipa_template_match2:
            ipa = ipa_template_match2.group(1).strip()
            if re.search(IPA_CHARS, ipa):
                return {'ipa': ipa, 'source': 'Wiktionary'}
        
        # Look for IPA within pronunciation sections (after "IPA:" or similar)
        # But exclude URLs by requiring IPA characters
        pron_section = re.search(r'===\s*Pronunciation\s*===.*?(?====|$)', content, re.DOTALL | re.IGNORECASE)
        if pron_section:
            pron_content = pron_section.group(0)
            # Find /.../ patterns that contain IPA characters and are NOT URLs
            ipa_matches = re.findall(r'/([^/\n]{2,30})/', pron_content)
            for ipa_candidate in ipa_matches:
                # Exclude URLs (contain dots like .org, .com, .net)
                if '.' in ipa_candidate and re.search(r'\.(org|com|net|edu|gov|io|uk)', ipa_candidate):
                    continue
                # Must contain at least one IPA-specific character
                if re.search(IPA_CHARS, ipa_candidate):
                    return {'ipa': f'/{ipa_candidate}/', 'source': 'Wiktionary'}
                
    except Exception as e:
        pass  # Silently skip errors
    
    return None


def g2p_fallback(word: str) -> Optional[Dict[str, str]]:
    """
    Generate pronunciation using g2p-en (grapheme-to-phoneme) as fallback.
    Returns phonemes in ARPAbet notation, which can be converted to phonetic spelling.
    """
    if _g2p is None:
        return None
    
    try:
        # g2p returns list of phonemes
        phonemes = _g2p(word)
        
        # Convert phoneme list to readable string
        # Remove numeric stress markers for cleaner output
        phoneme_str = ' '.join(phonemes)
        phoneme_clean = re.sub(r'\d', '', phoneme_str)
        
        # Convert ARPAbet to more readable pronunciation
        arpabet_to_readable = {
            'AA': 'ah', 'AE': 'a', 'AH': 'uh', 'AO': 'aw', 'AW': 'ow',
            'AY': 'eye', 'B': 'b', 'CH': 'ch', 'D': 'd', 'DH': 'th',
            'EH': 'eh', 'ER': 'er', 'EY': 'ay', 'F': 'f', 'G': 'g',
            'HH': 'h', 'IH': 'ih', 'IY': 'ee', 'JH': 'j', 'K': 'k',
            'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ng', 'OW': 'oh',
            'OY': 'oy', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'sh',
            'T': 't', 'TH': 'th', 'UH': 'oo', 'UW': 'oo', 'V': 'v',
            'W': 'w', 'Y': 'y', 'Z': 'z', 'ZH': 'zh',
        }
        
        readable_parts = []
        for phoneme in phoneme_clean.split():
            phoneme_upper = phoneme.upper()
            if phoneme_upper in arpabet_to_readable:
                readable_parts.append(arpabet_to_readable[phoneme_upper])
            else:
                readable_parts.append(phoneme.lower())
        
        readable = '-'.join(readable_parts)
        
        return {
            'phonemes': phoneme_str,
            'phonetic_spelling': readable,
            'source': 'G2P (generated)'
        }
    except Exception as e:
        pass
    
    return None


def ipa_to_phonetic_spelling(ipa: str, word: str) -> str:
    """
    Convert IPA notation to a phonetic spelling that TTS can handle.
    This is a simplified conversion - may need refinement.
    """
    # Common IPA to phonetic mappings
    conversions = {
        'ə': 'uh',
        'ɪ': 'ih',
        'i': 'ee',
        'ɛ': 'eh',
        'æ': 'a',
        'ɑ': 'ah',
        'ɔ': 'aw',
        'ʊ': 'oo',
        'u': 'oo',
        'ʌ': 'uh',
        'eɪ': 'ay',
        'aɪ': 'eye',
        'ɔɪ': 'oy',
        'aʊ': 'ow',
        'oʊ': 'oh',
        'ŋ': 'ng',
        'θ': 'th',
        'ð': 'th',
        'ʃ': 'sh',
        'ʒ': 'zh',
        'tʃ': 'ch',
        'dʒ': 'j',
        'ˈ': '',  # Primary stress marker - remove
        'ˌ': '',  # Secondary stress marker - remove
        '.': '',  # Syllable boundary - remove
    }
    
    phonetic = ipa
    for ipa_char, replacement in conversions.items():
        phonetic = phonetic.replace(ipa_char, replacement)
    
    # Remove any remaining special characters
    phonetic = re.sub(r'[^\w\s-]', '', phonetic)
    
    return phonetic.strip()


def create_pronunciation_dict(words: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Create a dictionary of pronunciations for difficult words.
    Tries Wiktionary first, then falls back to g2p-en for unknown words.
    Returns dict mapping word -> pronunciation info.
    """
    pronunciation_dict = {}
    
    for word in words:
        print(f"Looking up pronunciation for: {word}")
        
        # Try Wiktionary first
        result = search_wikipedia_pronunciation(word)
        
        if result:
            # Try to create phonetic spelling from IPA
            if 'ipa' in result:
                phonetic = ipa_to_phonetic_spelling(result['ipa'], word)
                result['phonetic_spelling'] = phonetic
            elif 'respelling' in result:
                result['phonetic_spelling'] = result['respelling']
            
            pronunciation_dict[word] = result
            print(f"  Found (Wiktionary): {result.get('phonetic_spelling', result.get('ipa', 'N/A'))}")
        else:
            # Try g2p fallback
            g2p_result = g2p_fallback(word)
            if g2p_result:
                pronunciation_dict[word] = g2p_result
                print(f"  Generated (G2P): {g2p_result.get('phonetic_spelling', 'N/A')}")
            else:
                print(f"  No pronunciation found")
    
    return pronunciation_dict


def apply_pronunciation_corrections(text: str, corrections: Dict[str, str]) -> str:
    """
    Apply pronunciation corrections to text.
    corrections: dict mapping original_word -> phonetic_spelling
    """
    corrected_text = text
    
    for original, phonetic in corrections.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(original) + r'\b'
        corrected_text = re.sub(pattern, phonetic, corrected_text, flags=re.IGNORECASE)
    
    return corrected_text
