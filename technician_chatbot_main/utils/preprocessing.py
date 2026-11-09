# utils/preprocessing.py

import string
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

lemmatizer = WordNetLemmatizer()

# Minimal, customizable set of stopwords for rule-based matching.
# DO NOT remove any negations or auxiliaries relevant for simple troubleshooting sentences.
_min_stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'with', 'by', 'and'}

# Still remove some punctuation, but KEEP apostrophes for contractions.
_punctuation_to_remove = ''.join(set(string.punctuation) - {"'"})

_punctuation_translation = str.maketrans('', '', _punctuation_to_remove)

def preprocess_text(text: str) -> str:
    """
    Normalize input for rule-based matching:
    - Lowercase
    - Remove most punctuation, keep apostrophes
    - Tokenize on whitespace/punctuation, but keep contractions
    - Lemmatize
    - Remove a very limited set of stopwords (never remove negation or "won't")
    - For very short queries (<=3 words after tokenize), don't remove any stopwords
    - Return normalized string suitable for matching
    """
    text = text.strip().lower()
    # Remove unwanted punctuation but keep apostrophes (so contractions like "won't" are intact)
    text = text.translate(_punctuation_translation)

    # Tokenize on whitespace (safe as contractions are kept as single word)
    tokens = text.split()

    # Lemmatize each token (this won't break "won't" or "can't")
    lemmas = [lemmatizer.lemmatize(token) for token in tokens]

    # For very short queries - skip stopword removal to preserve matching
    if len(lemmas) <= 3:
        filtered = lemmas
    else:
        filtered = [w for w in lemmas if w not in _min_stopwords]

    # Re-join to a phrase for matching
    return " ".join(filtered)
