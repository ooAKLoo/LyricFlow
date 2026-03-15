"""Audio Verification Layer
Uses Parselmouth (Praat) to verify rule engine predictions against actual audio.
"""


def verify_annotation(
    vocals_path: str,
    word_start: float,
    word_end: float,
    next_word_start: float | None,
    annotation: dict,
) -> dict:
    """Verify annotation against actual audio. Returns verification factor."""
    ann_type = annotation.get("type", "")

    try:
        import parselmouth
        from parselmouth.praat import call

        sound = parselmouth.Sound(vocals_path)

        if ann_type == "linking" and next_word_start is not None:
            return _verify_linking(sound, word_end, next_word_start)
        elif ann_type == "weak_form":
            return _verify_weak_form(sound, word_start, word_end)
        elif ann_type == "elision":
            return _verify_elision(sound, word_start, word_end)

    except ImportError:
        # Parselmouth not available, trust rule engine
        pass
    except Exception:
        pass

    return {"factor": 0.8, "verified": "unavailable"}


def _verify_linking(sound, word1_end: float, word2_start: float) -> dict:
    """Verify linking: check gap duration and energy continuity."""
    from parselmouth.praat import call

    gap_duration = word2_start - word1_end

    # Gap > 60ms = clear pause, no linking
    if gap_duration > 0.06:
        return {"factor": 0.1, "verified": False, "gap_ms": gap_duration * 1000}

    # Check energy continuity at word boundary
    try:
        intensity = call(sound, "To Intensity", 100, 0)
        e1 = call(intensity, "Get value at time", word1_end, "cubic")
        e2 = call(intensity, "Get value at time", word2_start, "cubic")
        mid_time = (word1_end + word2_start) / 2
        e_mid = call(intensity, "Get value at time", mid_time, "cubic")

        # If midpoint energy doesn't drop more than 3dB below average of edges
        avg_edge = (e1 + e2) / 2
        if avg_edge - e_mid < 3:
            return {"factor": 1.0, "verified": True, "gap_ms": gap_duration * 1000}
        else:
            return {"factor": 0.6, "verified": "uncertain", "gap_ms": gap_duration * 1000}
    except Exception:
        # If gap is small, likely linked even without energy check
        if gap_duration < 0.03:
            return {"factor": 1.0, "verified": True, "gap_ms": gap_duration * 1000}
        return {"factor": 0.6, "verified": "uncertain"}


def _verify_weak_form(sound, word_start: float, word_end: float) -> dict:
    """Verify weak form: check duration ratio and formant centralization."""
    from parselmouth.praat import call

    duration = word_end - word_start

    # Very short duration (< 150ms) strongly suggests weak form
    if duration < 0.15:
        return {"factor": 1.0, "verified": True, "duration_ms": duration * 1000}

    # Check formants - weak forms tend toward schwa (F1≈500Hz, F2≈1500Hz)
    try:
        formant = call(sound, "To Formant (burg)", 0, 5, 5500, 0.025, 50)
        mid_time = (word_start + word_end) / 2
        f1 = call(formant, "Get value at time", 1, mid_time, "hertz", "linear")
        f2 = call(formant, "Get value at time", 2, mid_time, "hertz", "linear")

        # Check if formants are close to schwa
        if f1 and f2:
            f1_dist = abs(f1 - 500) / 500
            f2_dist = abs(f2 - 1500) / 1500
            centralization = 1 - (f1_dist + f2_dist) / 2

            if centralization > 0.7:
                return {"factor": 1.0, "verified": True}
            elif centralization > 0.4:
                return {"factor": 0.8, "verified": "likely"}
    except Exception:
        pass

    # Duration-based heuristic
    if duration < 0.25:
        return {"factor": 0.8, "verified": "likely"}

    return {"factor": 0.6, "verified": "uncertain"}


def _verify_elision(sound, word_start: float, word_end: float) -> dict:
    """Verify elision: check energy at expected phoneme position."""
    from parselmouth.praat import call

    try:
        intensity = call(sound, "To Intensity", 100, 0)

        # Check energy at the end of the word (where elision typically occurs)
        check_time = word_end - 0.02  # 20ms before word end
        if check_time < word_start:
            check_time = (word_start + word_end) / 2

        e_end = call(intensity, "Get value at time", check_time, "cubic")

        # Get average energy for the word
        e_mean = call(
            intensity, "Get mean", word_start, word_end, "energy"
        )

        # If end energy is significantly lower than mean, elision likely
        if e_mean and e_end:
            diff = e_mean - e_end
            if diff > 10:  # > 10dB drop
                return {"factor": 1.0, "verified": True}
            elif diff > 5:
                return {"factor": 0.8, "verified": "likely"}
    except Exception:
        pass

    return {"factor": 0.6, "verified": "uncertain"}
