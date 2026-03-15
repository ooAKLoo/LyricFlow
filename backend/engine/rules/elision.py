"""Elision detection rules (吞音检测)
- /t/ elision in consonant clusters
- /d/ elision in consonant clusters
- /h/ dropping in pronouns
"""

from engine.rules.constants import CONSONANTS, H_DROP_WORDS


def detect_elision(
    word1: str, word2: str, ipa1: str, ipa2: str
) -> list[dict]:
    """Detect elision phenomena between two adjacent words."""
    results = []

    if not ipa1 or not ipa2:
        return results

    # Rule 1: /t/ and /d/ elision in consonant clusters
    # When /t/ or /d/ appears between two consonants (end of word1, start of word2)
    if ipa1[-1] in ("t", "d"):
        if len(ipa1) >= 2 and ipa1[-2] in CONSONANTS:
            if ipa2[0] in CONSONANTS:
                results.append({
                    "type": "elision",
                    "subtype": f"/{ipa1[-1]}/_elision",
                    "symbol": "◌̸",
                    "explanation_zh": f"/{ipa1[-1]}/ 在辅音簇中被省略",
                    "confidence": 0.8,
                    "target_word": word2,
                })

    # Rule 2: /h/ dropping in pronouns/auxiliaries
    w2_clean = word2.lower().strip("'\",.!?;:-")
    if w2_clean in H_DROP_WORDS:
        results.append({
            "type": "elision",
            "subtype": "h_dropping",
            "symbol": "◌̸",
            "explanation_zh": f"/h/ 在 {w2_clean} 中被省略",
            "confidence": 0.7,
            "target_word": word2,
        })

    # Rule 3: Final /v/ reduction in "of"
    if word1.lower().strip("'\",.!?;:-") == "of":
        if ipa2[0] in CONSONANTS:
            results.append({
                "type": "elision",
                "subtype": "v_reduction",
                "symbol": "◌̸",
                "explanation_zh": "of 中 /v/ 弱化或省略",
                "confidence": 0.65,
                "target_word": word2,
            })

    return results
