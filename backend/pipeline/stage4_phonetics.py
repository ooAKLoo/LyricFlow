"""Stage 4: Phonetic Transcription (IPA)
Dual-engine: CMU Dict + phonemizer (eSpeak-ng)
"""

import json
from pathlib import Path

from config import DATA_DIR

# Load supplementary dictionaries
_slang_dict = None
_arpa_to_ipa = None


def _load_slang_dict() -> dict:
    global _slang_dict
    if _slang_dict is None:
        path = DATA_DIR / "slang_dict.json"
        if path.exists():
            _slang_dict = json.loads(path.read_text(encoding="utf-8"))
        else:
            _slang_dict = {}
    return _slang_dict


# ARPAbet → IPA mapping
ARPA_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ",
    "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "ER": "ɝ",
    "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ",
    "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð",
    "F": "f", "G": "ɡ", "HH": "h", "JH": "dʒ",
    "K": "k", "L": "l", "M": "m", "N": "n",
    "NG": "ŋ", "P": "p", "R": "r", "S": "s",
    "SH": "ʃ", "T": "t", "TH": "θ", "V": "v",
    "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}


def phonetic_transcription(alignment_result: dict, dialect: str = "en-us") -> dict:
    """Add IPA transcription to each aligned word."""
    lines = alignment_result.get("lines", [])

    for line in lines:
        for word_data in line.get("words", []):
            word = word_data.get("word", "")
            ipa = get_ipa(word, dialect)
            word_data["ipa"] = ipa

    return {"lines": lines}


def get_ipa(word: str, dialect: str = "en-us") -> str:
    """Get IPA for a word using multi-source strategy."""
    clean_word = word.lower().strip("'\",.!?;:-")

    if not clean_word:
        return ""

    # Priority 1: Slang/song abbreviation dictionary
    slang = _load_slang_dict()
    if clean_word in slang:
        return slang[clean_word].get("ipa", "")

    # Priority 2: CMU Pronouncing Dictionary
    ipa = _cmu_to_ipa(clean_word)
    if ipa:
        return ipa

    # Priority 3: phonemizer (eSpeak-ng)
    ipa = _espeak_to_ipa(clean_word, dialect)
    if ipa:
        return ipa

    # Fallback: return word as-is
    return clean_word


def _cmu_to_ipa(word: str) -> str | None:
    """Convert word to IPA using CMU Pronouncing Dictionary."""
    try:
        import nltk
        from nltk.corpus import cmudict

        # Ensure cmudict is downloaded
        try:
            cmu = cmudict.dict()
        except LookupError:
            nltk.download("cmudict", quiet=True)
            cmu = cmudict.dict()

        prons = cmu.get(word.lower())
        if not prons:
            return None

        # Take first pronunciation variant
        return "".join(
            ARPA_TO_IPA.get(p.rstrip("012"), p)
            for p in prons[0]
        )
    except ImportError:
        return None


def _espeak_to_ipa(text: str, dialect: str = "en-us") -> str:
    """Convert text to IPA using phonemizer/eSpeak-ng."""
    try:
        from phonemizer import phonemize

        return phonemize(
            text,
            language=dialect,
            backend="espeak",
            strip=True,
            preserve_punctuation=False,
            with_stress=True,
        )
    except (ImportError, RuntimeError):
        return ""
