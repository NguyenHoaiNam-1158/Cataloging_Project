"""Fuzzy matching utilities for department name correction."""

import unicodedata
from rapidfuzz import process, fuzz
from typing import List, Tuple, Optional


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text: remove diacritics + lowercase."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_diacritics = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    return no_diacritics.lower()


class FuzzyMatcher:
    """Wrapper cho rapidfuzz voi Vietnamese normalization.

    Su dung token_set_ratio de match OCR errors (thieu dau, doi thu tu tu),
    kem tie-break bang ty le length de uu tien ten ngan hon khi cung diem.
    """

    def __init__(self, choices: List[str], threshold: int = 85):
        self.choices = choices
        self.threshold = threshold
        self._normalized_choices = [
            normalize_vietnamese(c) for c in choices
        ]

    def find_best(self, query: str) -> Optional[Tuple[str, float]]:
        """Tim match tot nhat. Tra ve (original_string, score) hoac None."""
        if not query or not self.choices:
            return None
        norm_query = normalize_vietnamese(query)
        if not norm_query:
            return None

        results = process.extract(
            norm_query, self._normalized_choices,
            scorer=fuzz.token_set_ratio, limit=3,
        )
        if not results:
            return None

        best, second = results[0], results[1] if len(results) > 1 else None
        score = best[1]
        if score < self.threshold:
            return None

        # Tie-break: neu diem gan nhau (chenh lech <= 5) va best dai hon
        # => chon ten ngan hon (dac trung hon cho corporate cap1/cap2 nho)
        if second and abs(score - second[1]) <= 5:
            best_len = len(self._normalized_choices[best[2]])
            second_len = len(self._normalized_choices[second[2]])
            if second_len < best_len and second[1] >= self.threshold:
                return self.choices[second[2]], second[1]

        return self.choices[best[2]], score
