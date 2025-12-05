import re

text = "Smith's book and the cat's toy"
print("Original:", text)

# Line 15 - smart quote conversion
text = text.replace('"', '"').replace('"', '"').replace(''', "'").replace(''', "'")
print("After smart quote conversion:", text)

# Line 200 - orphaned quote removal
text_after = re.sub(r"(?<!\w)'(?!\w)", '', text)
print("After orphaned quote removal:", text_after)

# Test with curly apostrophe
text2 = "Smith's book"  # curly apostrophe
print("\nWith curly apostrophe:", repr(text2))
text2 = text2.replace(''', "'").replace(''', "'")
print("After conversion:", repr(text2))
text2 = re.sub(r"(?<!\w)'(?!\w)", '', text2)
print("After orphaned removal:", text2)
