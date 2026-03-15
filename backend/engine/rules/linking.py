"""Linking detection rules (连读检测)
- C-V Linking: consonant + vowel
- V-V Linking: vowel + vowel (with glide insertion)
- R-Linking: British English r-linking
"""

from engine.rules.constants import VOWELS, CONSONANTS


def detect_linking(word1_ipa: str, word2_ipa: str, dialect: str = "en-us") -> dict | None:
    """Detect linking between two adjacent words."""
    if not word1_ipa or not word2_ipa:
        return None

    last_phone = word1_ipa[-1]
    first_phone = word2_ipa[0]

    # Rule 1: C-V Linking (consonant ending + vowel beginning)
    if last_phone in CONSONANTS and first_phone in VOWELS:
        return {
            "type": "linking",
            "subtype": "cv_linking",
            "symbol": "⌢",
            "explanation_zh": f"辅音 /{last_phone}/ 连接到元音 /{first_phone}/",
            "confidence": 0.9,
        }

    # Rule 2: V-V Linking (vowel + vowel, with glide insertion)
    if last_phone in VOWELS and first_phone in VOWELS:
        # /i/-type vowels → insert /j/ glide
        if last_phone in "iɪeɪ":
            return {
                "type": "linking",
                "subtype": "vv_linking_j",
                "symbol": "⌢",
                "explanation_zh": f"元音 /{last_phone}/ 后插入 /j/ 连接到 /{first_phone}/",
                "confidence": 0.75,
            }
        # /u/-type vowels → insert /w/ glide
        if last_phone in "uʊoʊ":
            return {
                "type": "linking",
                "subtype": "vv_linking_w",
                "symbol": "⌢",
                "explanation_zh": f"元音 /{last_phone}/ 后插入 /w/ 连接到 /{first_phone}/",
                "confidence": 0.75,
            }

    # Rule 3: R-Linking (British English only)
    if dialect == "en-gb" and last_phone == "r" and first_phone in VOWELS:
        return {
            "type": "linking",
            "subtype": "r_linking",
            "symbol": "⌢",
            "explanation_zh": f"/r/ 恢复发音，连接到元音 /{first_phone}/",
            "confidence": 0.85,
        }

    return None
