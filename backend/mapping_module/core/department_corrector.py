"""Department name corrector using Fuzzy Matching against Phu luc 6."""

import json
import logging
from rapidfuzz import process, fuzz
from mapping_module.config.settings import Settings
from mapping_module.utils.fuzzy_matcher import FuzzyMatcher, normalize_vietnamese

logger = logging.getLogger(__name__)

CAP1_PREFIXES = [
    "truong", "khoa", "phong", "benh vien", "trung tam",
]
CAP2_PREFIXES = [
    "bo mon", "trung tam",
]


class DepartmentCorrector:
    """Sua corporate_name theo Phu luc 6 bang Fuzzy Matching."""

    def __init__(self):
        self.departments = self._load_departments()
        self.cap1_names = list(set(d["tenDonViCap1"] for d in self.departments))
        self.cap2_names = [
            d["tenDonViCap2"]
            for d in self.departments
            if d.get("tenDonViCap2")
        ]

        self.matcher_cap1 = FuzzyMatcher(self.cap1_names, threshold=85)
        self.matcher_cap2 = FuzzyMatcher(self.cap2_names, threshold=85)
        self._cap2_norm = [normalize_vietnamese(c) for c in self.cap2_names]

        self._cap2_to_pair = {}
        for d in self.departments:
            if d.get("tenDonViCap2"):
                self._cap2_to_pair[d["tenDonViCap2"]] = (
                    d["tenDonViCap1"],
                    d["tenDonViCap2"],
                )

    def _load_departments(self) -> list:
        try:
            with open(Settings.DEPARTMENTS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Khong the load departments: {e}")
            return []

    def correct_corporate_name(self, raw_name: str) -> dict:
        """Sua corporate_name ve dung chuan theo Phu luc 6."""
        if not raw_name or not raw_name.strip():
            return {
                "corrected_name": raw_name,
                "cap1": None,
                "cap2": None,
                "confidence": 0,
                "match_method": "empty",
                "needs_review": True,
            }

        clean_name = raw_name.strip()
        norm_query = normalize_vietnamese(clean_name)

        has_delimiter = any(d in clean_name for d in ("-", "|", ",", "–", "—"))
        is_cap2_prefix = any(norm_query.startswith(p) for p in CAP2_PREFIXES)
        is_cap1_prefix = any(norm_query.startswith(p) for p in CAP1_PREFIXES)

        # Cap2-pure hoac khong ro prefix -> uu tien match cap2 (token_set)
        if is_cap2_prefix or (not is_cap1_prefix and not has_delimiter):
            cap2_direct = self.matcher_cap2.find_best(clean_name)
            if cap2_direct:
                matched_cap2, score = cap2_direct
                pair = self._cap2_to_pair.get(matched_cap2)
                if pair:
                    return {
                        "corrected_name": f"{pair[0]}|{pair[1]}",
                        "cap1": pair[0],
                        "cap2": pair[1],
                        "confidence": score,
                        "match_method": "fuzzy_cap2",
                        "needs_review": score < 90,
                    }

        # Toc hop (co delimiter) -> tim cap2 partial ben trong query
        cap2_match = self._find_cap2_partial(norm_query, clean_name) if (has_delimiter and is_cap1_prefix) else None
        if cap2_match:
            matched_cap2, score = cap2_match
            pair = self._cap2_to_pair.get(matched_cap2)
            if pair:
                return {
                    "corrected_name": f"{pair[0]}|{pair[1]}",
                    "cap1": pair[0],
                    "cap2": pair[1],
                    "confidence": score,
                    "match_method": "fuzzy_cap2",
                    "needs_review": score < 90,
                }

        # Khi query co ve cap1 (hoac khong ro) - match cap1
        match_cap1 = self.matcher_cap1.find_best(clean_name)
        if match_cap1:
            return self._build_cap1_result(match_cap1[0], match_cap1[1], clean_name)

        return self._no_match(clean_name)

    def _find_cap2_partial(self, norm_query: str, original_query: str):
        """Tim cap2 ben trong query dung partial_ratio.

        Vi cap2 = 'Bo mon X' hoac 'Trung tam Y', query thuong chua ca cap1 + cap2.
        partial_ratio cho diem cao khi cap2 la substring/gan-substring cua query.
        """
        if not norm_query or not self.cap2_names:
            return None

        results = process.extract(
            norm_query, self._cap2_norm,
            scorer=fuzz.partial_ratio, limit=3,
        )
        if not results:
            return None

        best = results[0]
        score = best[1]
        if score < 75:
            return None

        # Kiem tra gen nhau: neu co nhieu cap2 cung diem, chon cap2
        # co phan 'Bo mon|Trung tam' giong query nhat.
        if score < 88:
            second = results[1] if len(results) > 1 else None
            if second and abs(score - second[1]) <= 5:
                best_idx, second_idx = best[2], second[2]
                best_len = len(self._cap2_norm[best_idx])
                second_len = len(self._cap2_norm[second_idx])
                if second_len < best_len:
                    return self.cap2_names[second_idx], second[1]
                return self.cap2_names[best_idx], score

        return self.cap2_names[best[2]], score

    def _build_cap1_result(self, matched_cap1: str, score: float, original: str):
        related = [
            d for d in self.departments if d["tenDonViCap1"] == matched_cap1
        ]
        cap2_options = [
            d["tenDonViCap2"]
            for d in related
            if d.get("tenDonViCap2")
        ]

        # Neu query chua ca ten cap2, thu match cap2 trong do
        if norm := normalize_vietnamese(original):
            for cap2 in cap2_options:
                if normalize_vietnamese(cap2) in norm:
                    return {
                        "corrected_name": f"{matched_cap1}|{cap2}",
                        "cap1": matched_cap1,
                        "cap2": cap2,
                        "confidence": score,
                        "match_method": "fuzzy_cap1_with_cap2",
                        "needs_review": score < 90,
                    }

        if len(cap2_options) == 1:
            return {
                "corrected_name": f"{matched_cap1}|{cap2_options[0]}",
                "cap1": matched_cap1,
                "cap2": cap2_options[0],
                "confidence": score,
                "match_method": "fuzzy_cap1_single",
                "needs_review": score < 90,
            }
        return {
            "corrected_name": matched_cap1,
            "cap1": matched_cap1,
            "cap2": None,
            "confidence": score,
            "match_method": "fuzzy_cap1_multi" if len(cap2_options) > 1 else "fuzzy_cap1_only",
            "needs_review": True,
        }

    def _no_match(self, clean_name: str) -> dict:
        return {
            "corrected_name": clean_name,
            "cap1": clean_name,
            "cap2": None,
            "confidence": 0,
            "match_method": "no_match",
            "needs_review": True,
        }
