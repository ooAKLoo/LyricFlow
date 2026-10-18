import unittest

from engine.cloud_alignment import align_lyrics_with_asr, normalize_word_times
from engine.rap_optimizer import detect_rap_segments
from providers.qwen_audio_coach import _validate_result
from providers.volcengine_flash_asr import _normalize_response


class VolcengineResponseTests(unittest.TestCase):
    def test_normalizes_word_timestamps_without_inventing_confidence(self):
        result = _normalize_response({
            "audio_info": {"duration": 2400},
            "result": {
                "text": "ride it out",
                "utterances": [{
                    "text": "ride it out",
                    "start_time": 300,
                    "end_time": 1800,
                    "words": [
                        {"text": "ride", "start_time": 300, "end_time": 700, "confidence": 0},
                        {"text": "it", "start_time": 710, "end_time": 900, "confidence": 0.92},
                        {"text": "out", "start_time": 910, "end_time": 1800},
                    ],
                }],
            },
        })

        self.assertEqual(result["duration"], 2.4)
        self.assertEqual([word["word"] for word in result["words"]], ["ride", "it", "out"])
        self.assertIsNone(result["words"][0]["confidence"])
        self.assertEqual(result["words"][1]["confidence"], 0.92)


class CloudAlignmentTests(unittest.TestCase):
    def test_preserves_canonical_words_and_uses_asr_timing_as_evidence(self):
        aligned = align_lyrics_with_asr(
            {
                "lines": [{
                    "text": "Ride it out",
                    "start": 10.0,
                    "end": 12.0,
                    "words": [],
                }],
            },
            {
                "provider": "test_asr",
                "words": [
                    {"word": "ride", "start": 10.1, "end": 10.6, "confidence": 0.9},
                    {"word": "it", "start": 10.62, "end": 10.8, "confidence": 0.8},
                    {"word": "out", "start": 10.81, "end": 11.5, "confidence": 0.9},
                ],
            },
            duration=20,
        )

        words = aligned["lines"][0]["words"]
        self.assertEqual([word["word"] for word in words], ["Ride", "it", "out"])
        self.assertEqual([word["start"] for word in words], [10.1, 10.62, 10.81])
        self.assertEqual(aligned["alignment_quality"], 1.0)
        self.assertEqual(aligned["alignment_source"], "test_asr")

    def test_interpolates_unmatched_words_but_marks_their_source(self):
        aligned = align_lyrics_with_asr(
            {
                "lines": [{
                    "text": "Keep the rhythm",
                    "start": 2.0,
                    "end": 4.0,
                    "words": [],
                }],
            },
            {
                "provider": "test_asr",
                "words": [
                    {"word": "keep", "start": 2.1, "end": 2.5},
                    {"word": "rhythm", "start": 3.0, "end": 3.7},
                ],
            },
            duration=10,
        )

        words = aligned["lines"][0]["words"]
        self.assertEqual(words[1]["timing_source"], "interpolated")
        self.assertLess(words[1]["start"], words[1]["end"])

    def test_discards_anchor_outside_line_and_keeps_all_times_valid(self):
        words = [
            {"word": "now", "start": 4.4, "end": 4.8, "timing_source": "asr_match"},
            {"word": "we", "start": None, "end": None, "timing_source": "interpolated"},
            {"word": "go", "start": 6.2, "end": 6.5, "timing_source": "asr_match"},
        ]

        normalize_word_times(words, 4.0, 6.0)

        self.assertEqual(words[-1]["timing_source"], "interpolated")
        self.assertTrue(all(4.0 <= word["start"] < word["end"] <= 6.0 for word in words))


class QwenCoachValidationTests(unittest.TestCase):
    def test_rejects_low_confidence_and_out_of_range_cues(self):
        result = _validate_result({
            "performed_text": "ride‿it OUT",
            "coach_summary_zh": "把中间连成一口气。",
            "difficulty": 8,
            "beat_hint": "落在第二拍",
            "cues": [
                {
                    "word_index": 0,
                    "end_word_index": 1,
                    "type": "linking",
                    "confidence": 0.88,
                    "source": "ride it",
                    "heard_as": "rai-dit",
                },
                {
                    "word_index": 1,
                    "type": "elision",
                    "confidence": 0.4,
                },
                {
                    "word_index": 9,
                    "type": "stress",
                    "confidence": 0.9,
                },
            ],
        }, word_count=3)

        self.assertEqual(result["difficulty"], 5)
        self.assertEqual(len(result["cues"]), 1)
        self.assertEqual(result["cues"][0]["type"], "linking")


class RapSectionDetectionTests(unittest.TestCase):
    def test_marks_sustained_fast_section_and_rejects_repetitive_outro(self):
        lines = [
            _timed_line("slow opening words", 0, 3),
            _timed_line("when I was thirteen I had my first love", 3, 6),
            _timed_line("there was nobody that compared to my baby", 6, 7.3),
            _timed_line("and nobody came between us or could ever come above", 7.3, 9.1),
            _timed_line("she had me going crazy every single day", 9.1, 11.1),
            _timed_line("do not need no coffee when she calls my name", 11.1, 13.2),
            _timed_line("yeah yeah yeah now I am all gone", 30, 31.5),
            _timed_line("yeah yeah yeah now I am all gone", 31.5, 33),
            _timed_line("yeah yeah yeah now I am all gone", 33, 34.5),
        ]

        detected = detect_rap_segments(lines)

        self.assertGreaterEqual(len(detected), 4)
        self.assertTrue(all(line["is_rap"] for line in lines[1:6]))
        self.assertTrue(all(not line["is_rap"] for line in lines[6:]))


def _timed_line(text: str, start: float, end: float) -> dict:
    return {
        "text": text,
        "start": start,
        "end": end,
        "words": [{"word": word} for word in text.split()],
    }


if __name__ == "__main__":
    unittest.main()
