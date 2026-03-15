"""Weak form detection rules (弱读检测)
Function words in unstressed positions reduce to schwa /ə/.
"""

WEAK_FORMS = {
    "to": {"strong": "tuː", "weak": "tə"},
    "and": {"strong": "ænd", "weak": "ən"},
    "for": {"strong": "fɔːr", "weak": "fər"},
    "the": {"strong": "ðiː", "weak": "ðə"},
    "a": {"strong": "eɪ", "weak": "ə"},
    "an": {"strong": "æn", "weak": "ən"},
    "of": {"strong": "ɒv", "weak": "əv"},
    "you": {"strong": "juː", "weak": "jə"},
    "your": {"strong": "jɔːr", "weak": "jər"},
    "can": {"strong": "kæn", "weak": "kən"},
    "could": {"strong": "kʊd", "weak": "kəd"},
    "would": {"strong": "wʊd", "weak": "wəd"},
    "should": {"strong": "ʃʊd", "weak": "ʃəd"},
    "must": {"strong": "mʌst", "weak": "məst"},
    "have": {"strong": "hæv", "weak": "əv"},
    "has": {"strong": "hæz", "weak": "əz"},
    "had": {"strong": "hæd", "weak": "əd"},
    "do": {"strong": "duː", "weak": "də"},
    "does": {"strong": "dʌz", "weak": "dəz"},
    "am": {"strong": "æm", "weak": "əm"},
    "are": {"strong": "ɑːr", "weak": "ər"},
    "was": {"strong": "wɒz", "weak": "wəz"},
    "were": {"strong": "wɜːr", "weak": "wər"},
    "is": {"strong": "ɪz", "weak": "z"},
    "be": {"strong": "biː", "weak": "bɪ"},
    "been": {"strong": "biːn", "weak": "bɪn"},
    "will": {"strong": "wɪl", "weak": "l"},
    "shall": {"strong": "ʃæl", "weak": "ʃəl"},
    "at": {"strong": "æt", "weak": "ət"},
    "but": {"strong": "bʌt", "weak": "bət"},
    "or": {"strong": "ɔːr", "weak": "ər"},
    "from": {"strong": "frɒm", "weak": "frəm"},
    "some": {"strong": "sʌm", "weak": "səm"},
    "than": {"strong": "ðæn", "weak": "ðən"},
    "that": {"strong": "ðæt", "weak": "ðət"},
    "as": {"strong": "æz", "weak": "əz"},
    "her": {"strong": "hɜːr", "weak": "ər"},
    "him": {"strong": "hɪm", "weak": "ɪm"},
    "his": {"strong": "hɪz", "weak": "ɪz"},
    "he": {"strong": "hiː", "weak": "ɪ"},
    "she": {"strong": "ʃiː", "weak": "ʃɪ"},
    "me": {"strong": "miː", "weak": "mɪ"},
    "us": {"strong": "ʌs", "weak": "əs"},
    "them": {"strong": "ðɛm", "weak": "ðəm"},
    "not": {"strong": "nɒt", "weak": "nət"},
}


def detect_weak_form(word: str, position: int, sentence_length: int) -> dict | None:
    """Detect weak form for function words in non-final position."""
    clean = word.lower().strip("'\",.!?;:-")

    if clean not in WEAK_FORMS:
        return None

    # Function words at sentence end are typically strong
    is_sentence_end = position >= sentence_length - 1

    if is_sentence_end:
        return None

    forms = WEAK_FORMS[clean]
    weak_val = forms["weak"]
    if isinstance(weak_val, list):
        weak_val = weak_val[0]

    return {
        "type": "weak_form",
        "subtype": "weak_reduction",
        "symbol": "( )",
        "strong_ipa": forms["strong"],
        "weak_ipa": weak_val,
        "explanation_zh": f"功能词 {clean} 弱读为 /{weak_val}/",
        "confidence": 0.85,
        "target_word": None,
    }
