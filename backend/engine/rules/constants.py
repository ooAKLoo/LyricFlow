"""IPA phonetic constants for pronunciation detection."""

VOWELS = set("ɑæʌɔaɪeɛɝɪioʊuəː")

CONSONANTS = set("bcdfɡhjklmnŋprsʃtθðvwzʒ")

# Multi-character consonants
MULTI_CONSONANTS = {"tʃ", "dʒ"}

# Function words that commonly undergo weak form reduction
FUNCTION_WORDS = {
    "a", "an", "the", "to", "for", "of", "and", "but", "or",
    "in", "on", "at", "by", "from", "with", "as",
    "is", "am", "are", "was", "were", "be", "been",
    "do", "does", "did",
    "have", "has", "had",
    "will", "would", "shall", "should",
    "can", "could", "may", "might", "must",
    "he", "him", "his", "her", "she", "it", "its",
    "we", "us", "our", "they", "them", "their",
    "you", "your", "me", "my",
    "that", "this", "some", "any",
    "not", "just",
}

# Words where /h/ can be dropped
H_DROP_WORDS = {"he", "him", "her", "his", "has", "have", "had"}
