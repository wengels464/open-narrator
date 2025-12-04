"""
Pronunciation correction utilities for Open Narrator.
Detects difficult-to-pronounce words and looks up correct pronunciations.
"""

import re
import requests
from typing import List, Dict, Tuple, Optional


def find_difficult_words(text: str) -> List[str]:
    """
    Identify words that are likely difficult to pronounce.
    Focuses on:
    - Proper nouns (capitalized mid-sentence)
    - Foreign-looking words (unusual letter combinations)
    - Words with unusual capitalization patterns
    
    Returns list of unique difficult words.
    """
    difficult_words = set()
    
    # Split into sentences to detect mid-sentence capitals
    sentences = re.split(r'[.!?]+', text)
    
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
            
            # Check if capitalized mid-sentence (likely proper noun)
            if i > 0 and clean_word[0].isupper():
                difficult_words.add(clean_word)
                continue
            
            # Check for foreign-looking patterns
            # Multiple consecutive consonants, unusual letter combos
            if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', clean_word.lower()):
                difficult_words.add(clean_word)
                continue
            
            # Check for non-English letter patterns
            if re.search(r'(mb|chk|tch|sch|pn|gn|kn)[aeiou]', clean_word.lower()):
                difficult_words.add(clean_word)
                continue
            
            # Words with apostrophes in unusual positions (not contractions)
            if "'" in clean_word and not re.match(r".*'(s|t|d|ll|ve|re|m)$", clean_word.lower()):
                difficult_words.add(clean_word)
    
    return sorted(list(difficult_words))


def search_wikipedia_pronunciation(word: str) -> Optional[Dict[str, str]]:
    """
    Search Wikipedia for pronunciation information.
    Returns dict with 'ipa' and 'respelling' if found.
    """
    try:
        # Search Wikipedia API
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "opensearch",
            "search": word,
            "limit": 1,
            "format": "json"
        }
        
        response = requests.get(search_url, params=search_params, timeout=5)
        response.raise_for_status()
        search_results = response.json()
        
        if not search_results[1]:  # No results
            return None
        
        page_title = search_results[1][0]
        
        # Get page content
        content_params = {
            "action": "query",
            "titles": page_title,
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "rvslots": "main"
        }
        
        response = requests.get(search_url, params=content_params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None
        
        page = list(pages.values())[0]
        if "revisions" not in page:
            return None
        
        content = page["revisions"][0]["slots"]["main"]["*"]
        
        # Extract IPA pronunciation
        # Look for {{IPA|...}} or {{IPAc-en|...}} templates
        ipa_match = re.search(r'\{\{IPA(?:c-en)?\|([^}]+)\}\}', content)
        if ipa_match:
            ipa = ipa_match.group(1).strip()
            # Clean up the IPA notation
            ipa = re.sub(r'\|', '', ipa)  # Remove pipe separators
            ipa = re.sub(r'lang=\w+', '', ipa)  # Remove language tags
            ipa = ipa.strip()
            
            return {
                "word": word,
                "ipa": ipa,
                "source": f"Wikipedia: {page_title}"
            }
        
        # Look for pronunciation respelling
        respell_match = re.search(r'\{\{respell\|([^}]+)\}\}', content, re.IGNORECASE)
        if respell_match:
            respelling = respell_match.group(1).strip()
            return {
                "word": word,
                "respelling": respelling,
                "source": f"Wikipedia: {page_title}"
            }
        
        return None
        
    except Exception as e:
        print(f"Error searching Wikipedia for '{word}': {e}")
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
    Returns dict mapping word -> pronunciation info.
    """
    pronunciation_dict = {}
    
    for word in words:
        print(f"Looking up pronunciation for: {word}")
        result = search_wikipedia_pronunciation(word)
        
        if result:
            # Try to create phonetic spelling
            if 'ipa' in result:
                phonetic = ipa_to_phonetic_spelling(result['ipa'], word)
                result['phonetic_spelling'] = phonetic
            elif 'respelling' in result:
                result['phonetic_spelling'] = result['respelling']
            
            pronunciation_dict[word] = result
            print(f"  Found: {result.get('phonetic_spelling', result.get('ipa', 'N/A'))}")
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
