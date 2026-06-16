#!/usr/bin/env python3
import json
import re
import os
import sys
import unicodedata

from pymarc import Record, Field, Subfield, Indicators
from pymarc import JSONWriter


def _sf(code: str, value: str) -> Subfield:
    """Tạo Subfield một cách ngắn gọn."""
    return Subfield(code=code, value=value)


def _subfields(*pairs: str) -> list[Subfield]:
    """Chuyển đổi cặp code+value phẳng thành list Subfield.

    Ví dụ: _subfields('a', 'DHYD', 'b', 'vie') -> [Subfield('a','DHYD'), Subfield('b','vie')]
    """
    result = []
    for i in range(0, len(pairs), 2):
        result.append(_sf(pairs[i], pairs[i + 1]))
    return result


class Marc21Mapper:
    """Lớp chính ánh xạ JSON đầu vào thành biểu ghi MARC21."""

    # Ánh xạ document_type -> mã cho vị trí 24-27 của trường 008
    _DOC_TYPE_008_2427 = {
        "luan_van": "m   ",
        "luan_an": "m   ",
        "khoa_luan": "m   ",
        "bao_cao_nckh": "t   ",
        "sach": "    ",
        "tap_chi": "    ",
    }

    # Ánh xạ document_type -> mã cho trường 927
    _DOC_TYPE_927 = {
        "luan_van": "LA",
        "luan_an": "LA",
        "khoa_luan": "KL",
        "bao_cao_nckh": "NCKH",
        "sach": "TK",
        "tap_chi": "TC",
    }

    def __init__(self, data: dict):
        """
        Khởi tạo mapper với dữ liệu JSON đầu vào.
        :param data: Dict chứa dữ liệu trích xuất từ tài liệu.
        """
        self.data = data
        self.record = Record()

    def _safe_get(self, *keys, default=None):
        """Truy xuất an toàn giá trị lồng nhau trong dict."""
        value = self.data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value if value is not None else default

    # ------------------------------------------------------------------
    # LEADER — Bỏ qua. Hệ thống tự tạo sau khi có biểu ghi hoàn chỉnh.
    # ------------------------------------------------------------------
    def map_leader(self):
        pass

    # ------------------------------------------------------------------
    # 008 — Bỏ qua. Dữ liệu từ ảnh là các vị trí nhỏ lẻ, hệ thống tự xây dựng sau.
    # ------------------------------------------------------------------
    def map_008(self):
        pass

    # ------------------------------------------------------------------
    # 020 – ISBN (KHÔNG dùng dấu chấm kết thúc)
    # ------------------------------------------------------------------
    def map_020(self):
        """Trường 020: ISBN. KHÔNG dùng dấu chấm kết thúc."""
        isbn_list = self._safe_get("isbn", default=[])
        if not isbn_list:
            return
        for isbn_obj in isbn_list:
            isbn_number = isbn_obj.get("isbn_number") if isinstance(isbn_obj, dict) else None
            if not isbn_number:
                continue
            price = isbn_obj.get("price") if isinstance(isbn_obj, dict) else None
            sf = _subfields("a", isbn_number)
            if price:
                sf.append(_sf("c", price))
            self.record.add_ordered_field(
                Field(tag="020", indicators=Indicators(" ", " "), subfields=sf)
            )

    # ------------------------------------------------------------------
    # 022 – ISSN (KHÔNG dùng dấu chấm kết thúc)
    # ------------------------------------------------------------------
    def map_022(self):
        """Trường 022: ISSN."""
        issn = self._safe_get("issn")
        if issn:
            self.record.add_ordered_field(
                Field(
                    tag="022",
                    indicators=Indicators("#", "#"),
                    subfields=_subfields("a", issn),
                )
            )

    # ------------------------------------------------------------------
    # 040 – Nguồn biên mục (mặc định DHYD)
    # ------------------------------------------------------------------
    def map_040(self):
        """Trường 040: Nguồn biên mục."""
        self.record.add_ordered_field(
            Field(
                tag="040",
                indicators=Indicators(" ", " "),
                subfields=_subfields("a", "DHYD", "b", "vie", "c", "DHYD"),
            )
        )

    # ------------------------------------------------------------------
    # 041 – Mã ngôn ngữ (mặc định 'vie')
    # ------------------------------------------------------------------
    def map_041(self):
        """Trường 041: Mã ngôn ngữ."""
        self.record.add_ordered_field(
            Field(
                tag="041",
                indicators=Indicators("0", "#"),
                subfields=_subfields("a", "vie"),
            )
        )

    # ------------------------------------------------------------------
    # 050 – Phân loại LC (chỉ sách, optional)
    # ------------------------------------------------------------------
    def map_050(self):
        """Trường 050: Phân loại LC theo Thư viện Quốc hội Hoa Kỳ.
        Chỉ xuất trường này nếu đầu vào JSON có chứa mã phân loại LC.
        """
        doc_type = self._safe_get("document_type")
        lcc_code = self._safe_get("lcc_code") 
        
        if doc_type == "sach" and lcc_code:
            clean_lcc = lcc_code.strip().replace(" ", "")
            
            self.record.add_ordered_field(
                Field(
                    tag="050",
                    indicators=Indicators("1", "4"),  
                    subfields=_subfields("a", clean_lcc)
                )
            )
    # ------------------------------------------------------------------
    # 060 – Phân loại NLM (optional)
    # ------------------------------------------------------------------
    def map_060(self):
        """Trường 060: Phân loại NLM. 
        Hỗ trợ đọc mã NLM trực tiếp từ JSON hoặc thông qua mapping từ chuyên ngành (major).
        """
        nlm_code = self._safe_get("nlm_code")
        major = self._safe_get("major")
        
        # Nếu model chưa trích xuất được mã NLM cụ thể nhưng có chuyên ngành, 
        # hệ thống có thể đối chiếu nhanh qua bảng mapping nội bộ dựa trên khung phân loại NLM 
        if not nlm_code and major:
            major_mapping = {
                "Ung Thư": "QZ 200",
                "Nội Khoa": "WB 115",
                "Giải phẫu học": "QS 4"
            }
            nlm_code = major_mapping.get(major)

        if nlm_code:
            self.record.add_ordered_field(
                Field(
                    tag="060",
                    indicators=Indicators("1", "4"), 
                    subfields=_subfields("a", nlm_code.strip())
                )
            )
    # ------------------------------------------------------------------
    # 090 – Ký hiệu xếp giá nội bộ (optional)
    # ------------------------------------------------------------------
    def map_090(self):
        """Trường 090: Ký hiệu xếp giá nội bộ của thư viện.
        $a: Đồng bộ tự động thông tin từ trường 060 $a.
        $b: Lấy 3 chữ cái đầu của Họ tác giả (IN HOA) + Khoảng trắng + 4 số của năm xuất bản.
        """
        # 1. Lấy thông tin mã phân loại từ trường 060 đã xử lý trước đó
        f060 = self.record.get("060")
        nlm_code = f060.subfields[0].value if f060 and f060.subfields else None
        
        author_name = self._safe_get("author_personal_name")
        pub_year = self._safe_get("publication_year")

        if nlm_code and author_name and pub_year:
            # Loại bỏ các ký tự học vị thừa (như GS.TS., PGS.TS.) để tránh lấy sai họ 
            clean_name = author_name.strip()
            match = re.match(r"^((?:[A-ZĐÀ-Ỹ]+\.\s*)+)\s*(.+)$", clean_name)
            if match:
                clean_name = match.group(2).strip()
            
            name_parts = clean_name.split()
            if name_parts:
                # Đối với tên người Việt chuẩn, họ nằm ở từ đầu tiên 
                last_name = name_parts[0]
                
                # Trích xuất 3 ký tự đầu tiên của họ và chuyển thành chữ IN HOA 
                short_last_name = last_name[:3].upper()
                
                # Cấu trúc mã xếp kệ: 3 chữ cái họ + Khoảng trắng + 4 số năm xuất bản 
                call_number_b = f"{short_last_name} {pub_year}"

                self.record.add_ordered_field(
                    Field(
                        tag="090",
                        indicators=Indicators(" ", " "),
                        subfields=_subfields("a", nlm_code, "b", call_number_b)
                    )
                )

    # ------------------------------------------------------------------
    # 100 – Tác giả cá nhân
    # ------------------------------------------------------------------
    def map_100(self):
        """Trường 100: Tác giả cá nhân (Ind1=1: đảo họ lên trước).

        Xử lý tách học vị (VD: 'GS.TS. LÂM QUANG THÀNH') vào $c.
        """
        author_name = self._safe_get("author_personal_name")
        if not author_name:
            return

        author_role = self._safe_get("author_role")

        # Tách học vị nếu có (cụm viết hoa + dấu chấm ở đầu)
        match = re.match(r"^((?:[A-ZĐÀ-Ỹ]+\.\s*)+)\s*(.+)$", author_name.strip())
        if match:
            title_part = match.group(1).strip()
            clean_name = match.group(2).strip()
            name_parts = clean_name.split()
            if len(name_parts) >= 2:
                last_name = name_parts[0]
                first_names = " ".join(name_parts[1:])
                formatted_name = f"{last_name.title()}, {first_names.title()}"
            else:
                formatted_name = clean_name.title()
            subfields = [_sf("a", formatted_name), _sf("c", title_part)]
            if author_role:
                subfields.append(_sf("e", author_role))
            self.record.add_ordered_field(
                Field(
                    tag="100",
                    indicators=Indicators("1", " "),
                    subfields=subfields,
                )
            )
        else:
            name_parts = author_name.strip().split()
            if len(name_parts) >= 2:
                last_name = name_parts[0]
                first_names = " ".join(name_parts[1:])
                formatted_name = f"{last_name.title()}, {first_names.title()}"
            else:
                formatted_name = author_name.strip().title()
            subfields = [_sf("a", formatted_name)]
            if author_role:
                subfields.append(_sf("e", author_role))
            self.record.add_ordered_field(
                Field(
                    tag="100",
                    indicators=Indicators("1", " "),
                    subfields=subfields,
                )
            )

    # ------------------------------------------------------------------
    # 110 – Tên tập thể
    # ------------------------------------------------------------------
    def map_110(self):
        """Trường 110: Tên tập thể (Ind1=2)."""
        corporate = self._safe_get("corporate_name")
        if corporate:
            self.record.add_ordered_field(
                Field(
                    tag="110",
                    indicators=Indicators("2", " "),
                    subfields=_subfields("a", corporate),
                )
            )

    # ------------------------------------------------------------------
    # 245 – Nhan đề chính
    # ------------------------------------------------------------------
    def map_245(self):
        """Trường 245: Nhan đề chính.

        Quy tắc dấu câu:
          - $a kết thúc bằng ' /'
          - $b kết thúc bằng ' /' hoặc '.'
          - $c kết thúc bằng '.'
        """
        title_main = self._safe_get("title_main")
        if not title_main:
            return

        title_remainder = self._safe_get("title_remainder")
        statement = self._safe_get("statement_of_responsibility")
        part_info = self._safe_get("document_part_info")

        subfields = [_sf("a", f"{title_main} /")]
        if part_info:
            subfields.append(_sf("n", part_info))
        if title_remainder:
            subfields.append(_sf("b", f"{title_remainder} /"))
        if statement:
            subfields.append(_sf("c", f"{statement}."))

        self.record.add_ordered_field(
            Field(tag="245", indicators=Indicators("1", "0"), subfields=subfields)
        )

    # ------------------------------------------------------------------
    # 246 – Dạng nhan đề khác
    # ------------------------------------------------------------------
    def map_246(self):
        """Trường 246: Các dạng nhan đề khác."""
        title_variants = self._safe_get("title_variant", default=[])
        if not title_variants:
            return
        for variant in title_variants:
            if variant:
                self.record.add_ordered_field(
                    Field(
                        tag="246",
                        indicators=Indicators("3", "#"),
                        subfields=_subfields("a", variant),
                    )
                )

    # ------------------------------------------------------------------
    # 250 – Lần xuất bản
    # ------------------------------------------------------------------
    def map_250(self):
        """Trường 250: Lần xuất bản. Kết thúc bằng dấu chấm."""
        edition = self._safe_get("edition_statement")
        if edition:
            edition_text = edition if edition.endswith(".") else f"{edition}."
            self.record.add_ordered_field(
                Field(
                    tag="250",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", edition_text),
                )
            )

    # ------------------------------------------------------------------
    # 260 – Địa chỉ xuất bản
    # ------------------------------------------------------------------
    def map_260(self):
        """Trường 260: Địa chỉ xuất bản.

        Quy tắc dấu câu DHYD:
          - $a kết thúc bằng ' :'
          - $b kết thúc bằng ','
          - $c kết thúc bằng '.'
        """
        place = self._safe_get("place_of_publication", default="[k.nxb]")
        publisher = self._safe_get("publisher_name")
        pub_year = self._safe_get("publication_year", default="")

        if not place and not publisher and not pub_year:
            return

        subfields = []
        if place:
            subfields.append(_sf("a", f"{place} :"))
        if publisher:
            subfields.append(_sf("b", f"{publisher},"))
        if pub_year:
            subfields.append(_sf("c", f"{pub_year}."))

        self.record.add_ordered_field(
            Field(tag="260", indicators=Indicators(" ", " "), subfields=subfields)
        )

    # ------------------------------------------------------------------
    # 300 – Mô tả vật lý
    # ------------------------------------------------------------------
    def map_300(self):
        """Trường 300: Mô tả vật lý."""
        extent = self._safe_get("extent")
        physical_details = self._safe_get("physical_details")
        dimensions = self._safe_get("dimensions")

        if not extent and not physical_details and not dimensions:
            return

        subfields = []
        if extent:
            subfields.append(_sf("a", extent))
        if physical_details:
            subfields.append(_sf("b", physical_details))
        if dimensions:
            subfields.append(_sf("c", dimensions))

        self.record.add_ordered_field(
            Field(tag="300", indicators=Indicators(" ", " "), subfields=subfields)
        )

    # ------------------------------------------------------------------
    # 310 – Định kỳ xuất bản hiện thời (cho tạp chí)
    # ------------------------------------------------------------------
    def map_310(self):
        """Trường 310: Định kỳ xuất bản hiện thời.
        $a: Tần suất (VD: Hàng tháng), $b: Ngày tháng (VD: 1975-).
        Không kết thúc bằng dấu chấm trừ khi từ cuối là viết tắt.
        """
        frequency = self._safe_get("current_frequency")
        if frequency:
            self.record.add_ordered_field(
                Field(
                    tag="310",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", frequency),
                )
            )

    # ------------------------------------------------------------------
    # 321 – Định kỳ xuất bản cũ (cho tạp chí)
    # ------------------------------------------------------------------
    def map_321(self):
        """Trường 321: Định kỳ xuất bản cũ.
        $a: Tần suất cũ, $b: Khoảng thời gian áp dụng.
        """
        former = self._safe_get("former_frequency")
        if former:
            self.record.add_ordered_field(
                Field(
                    tag="321",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", former),
                )
            )

    # ------------------------------------------------------------------
    # 362 – Thời gian xuất bản / Số thứ tự (cho tạp chí)
    # ------------------------------------------------------------------
    def map_362(self):
        """Trường 362: Thời gian xuất bản/số thứ tự.
        Ind1=1: Phụ chú không định dạng.
        $a: VD 'Tập 1, số 1 (tháng Mười, 1992) -'
        """
        pub_dates = self._safe_get("publication_dates")
        if pub_dates:
            self.record.add_ordered_field(
                Field(
                    tag="362",
                    indicators=Indicators("1", "#"),
                    subfields=_subfields("a", pub_dates),
                )
            )

    # ------------------------------------------------------------------
    # 490 – Thông tin tùng thư (KHÔNG kết thúc bằng dấu chấm)
    # ------------------------------------------------------------------
    def map_490(self):
        """Trường 490: Thông tin tùng thư."""
        series = self._safe_get("series_statement")
        volume = self._safe_get("series_volume")
        if series:
            series_text = series
            if volume:
                series_text = f"{series}. {volume}"
            self.record.add_ordered_field(
                Field(
                    tag="490",
                    indicators=Indicators("0", " "),
                    subfields=_subfields("a", series_text),
                )
            )

    # ------------------------------------------------------------------
    # 500 – Phụ chú chung (Optional)
    # ------------------------------------------------------------------
    def map_500(self):
        """Trường 500: Phụ chú chung (tạm thời bỏ qua)."""
        notes = self._safe_get("general_notes", default=[])
        if not notes:
            return
        for note in notes:
            if note:
                note_text = note if note.endswith(".") else f"{note}."
                self.record.add_ordered_field(
                    Field(
                        tag="500",
                        indicators=Indicators(" ", " "),
                        subfields=_subfields("a", note_text),
                    )
                )

    # ------------------------------------------------------------------
    # 502 – Phụ chú luận văn/luận án (bắt buộc nếu là LV/LA)
    # ------------------------------------------------------------------
    def map_502(self):
        """Trường 502: Phụ chú luận văn/luận án."""
        doc_type = self._safe_get("document_type")
        is_thesis = doc_type in ("luan_an", "luan_van", "khoa_luan")

        diss_note = self._safe_get("dissertation_note")
        if diss_note:
            note_text = diss_note if diss_note.endswith(".") else f"{diss_note}."
            self.record.add_ordered_field(
                Field(
                    tag="502",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", note_text),
                )
            )
        elif is_thesis:
            # Tạo phụ chú từ các thông tin có sẵn
            # Format: Luận văn (Chuyên ngành) -- Cơ sở đào tạo, Năm.
            parts = ["Luận văn"]
            major = self._safe_get("major")
            if major:
                parts.append(f"({major})")
            corporate = self._safe_get("corporate_name")
            if corporate:
                parts.append(f"-- {corporate}")
            pub_year = self._safe_get("publication_year")
            if pub_year and len(parts) > 1:
                parts[-1] = f"{parts[-1]}, {pub_year}"
            elif pub_year:
                parts.append(pub_year)
            note_text = " ".join(parts) + "."
            self.record.add_ordered_field(
                Field(
                    tag="502",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", note_text),
                )
            )

    # ------------------------------------------------------------------
    # 504 – Phụ chú thư mục
    # ------------------------------------------------------------------
    def map_504(self):
        """Trường 504: Phụ chú thư mục. Kết thúc bằng dấu chấm."""
        biblio = self._safe_get("bibliography_note")
        num_refs = self._safe_get("number_of_references")
        if not biblio and not num_refs:
            return

        subfields = []
        if biblio:
            biblio_text = biblio if biblio.endswith(".") else f"{biblio}."
            subfields.append(_sf("a", biblio_text))
        if num_refs:
            num_text = num_refs if num_refs.endswith(".") else f"{num_refs}."
            subfields.append(_sf("b", num_text))

        self.record.add_ordered_field(
            Field(tag="504", indicators=Indicators(" ", " "), subfields=subfields)
        )

    # ------------------------------------------------------------------
    # 505 – Phụ chú nội dung được định dạng (Mục lục)
    # ------------------------------------------------------------------
    def map_505(self):
        """Trường 505: Phụ chú nội dung (mục lục).
        Ind1=0: Nội dung đầy đủ, Ind2=#: Cơ bản.
        $a: Nội dung mục lục.
        """
        contents = self._safe_get("table_of_contents", default=[])
        if not contents:
            return
        for entry in contents:
            if entry:
                entry_text = entry if entry.endswith(".") else f"{entry}."
                self.record.add_ordered_field(
                    Field(
                        tag="505",
                        indicators=Indicators("0", "#"),
                        subfields=_subfields("a", entry_text),
                    )
                )

    # ------------------------------------------------------------------
    # 520 – Tóm tắt / Chú giải
    # ------------------------------------------------------------------
    def map_520(self):
        """Trường 520: Tóm tắt hoặc chú giải nội dung.
        Ind1=3: Tóm tắt, Ind2=#.
        $a: Nội dung tóm tắt.
        """
        summary = self._safe_get("summary")
        if summary:
            summary_text = summary if summary.endswith(".") else f"{summary}."
            self.record.add_ordered_field(
                Field(
                    tag="520",
                    indicators=Indicators("3", "#"),
                    subfields=_subfields("a", summary_text),
                )
            )

    # ------------------------------------------------------------------
    # 541 – Nguồn tiếp nhận
    # ------------------------------------------------------------------
    def map_541(self):
        """Trường 541: Nguồn tiếp nhận tài liệu."""
        source = self._safe_get("acquisition_source")
        if source:
            text = source[0].lower() + source[1:] if source else source
            if not text.endswith("."):
                text += "."
            self.record.add_ordered_field(
                Field(
                    tag="541",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("c", text),
                )
            )

    # ------------------------------------------------------------------
    # 630 – Tiêu đề bổ sung cho nhan đề (Nhan đề đồng nhất)
    # ------------------------------------------------------------------
    def map_630(self):
        """Trường 630: Nhan đề đồng nhất.
        $a: Nhan đề chuẩn hóa.
        """
        uniform_title = self._safe_get("uniform_title")
        if uniform_title:
            ut_text = uniform_title if uniform_title.endswith(".") else f"{uniform_title}."
            self.record.add_ordered_field(
                Field(
                    tag="630",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", ut_text),
                )
            )

    # ------------------------------------------------------------------
    # 650 – Thuật ngữ chủ đề
    # ------------------------------------------------------------------
    def map_650(self):
        """Trường 650: Thuật ngữ chủ đề (Ind1=1, Ind2=2 cho MeSH)."""
        subjects = self._safe_get("subject_terms", default=[])
        if not subjects:
            return
        for subject in subjects:
            if subject and isinstance(subject, str):
                self.record.add_ordered_field(
                    Field(
                        tag="650",
                        indicators=Indicators("1", "2"),
                        subfields=_subfields("a", subject),
                    )
                )

    # ------------------------------------------------------------------
    # 653 – Từ khóa tự do (KHÔNG dùng dấu chấm kết thúc)
    # ------------------------------------------------------------------
    def map_653(self):
        """Trường 653: Từ khóa tự do không kiểm soát."""
        subjects = self._safe_get("subject_terms", default=[])
        if subjects:
            for subject in subjects:
                if subject and isinstance(subject, str):
                    self.record.add_ordered_field(
                        Field(
                            tag="653",
                            indicators=Indicators("1", "#"),
                            subfields=_subfields("a", subject),
                        )
                    )

    # ------------------------------------------------------------------
    # 720 – Tên chưa kiểm soát (người hướng dẫn)
    # ------------------------------------------------------------------
    def map_720(self):
        """Trường 720: Tên chưa kiểm soát."""
        advisor_name = self._safe_get("advisor_name")
        if advisor_name:
            self.record.add_ordered_field(
                Field(
                    tag="720",
                    indicators=Indicators("1", " "),
                    subfields=_subfields("a", advisor_name),
                )
            )

    # ------------------------------------------------------------------
    # 773 – Ấn phẩm chủ (dành cho bài trích tạp chí)
    # ------------------------------------------------------------------
    def map_773(self):
        """Trường 773: Mục từ ấn phẩm chủ (bài trích).
        Ind1=0, Ind2=8.
        $t: Nhan đề tạp chí mẹ.
        $g: Tập, số, năm.
        $x: Số ISSN.
        """
        host = self._safe_get("host_item")
        if host and isinstance(host, dict):
            subfields = []
            if host.get("title"):
                subfields.append(_sf("t", host["title"]))
            if host.get("issue"):
                subfields.append(_sf("g", host["issue"]))
            if host.get("issn"):
                subfields.append(_sf("x", host["issn"]))
            if subfields:
                self.record.add_ordered_field(
                    Field(
                        tag="773",
                        indicators=Indicators("0", "8"),
                        subfields=subfields,
                    )
                )

    # ------------------------------------------------------------------
    # 856 – Địa chỉ điện tử và truy cập
    # ------------------------------------------------------------------
    def map_856(self):
        """Trường 856: Địa chỉ điện tử.
        Ind1=4 (HTTP), Ind2=#.
        $u: URL.
        $z: Ghi chú (optional).
        """
        url = self._safe_get("electronic_url")
        if url:
            subfields = [_sf("u", url)]
            note = self._safe_get("electronic_note")
            if note:
                subfields.append(_sf("z", note))
            self.record.add_ordered_field(
                Field(
                    tag="856",
                    indicators=Indicators("4", "#"),
                    subfields=subfields,
                )
            )

    # ------------------------------------------------------------------
    # 915 – Trường cục bộ DHYD
    # ------------------------------------------------------------------
    def map_915(self):
        """Trường 915 (cục bộ DHYD): $a=chuyên ngành, $c=bậc học,
        $f=người hướng dẫn, $g=học vị."""
        major = self._safe_get("major")
        academic_level = self._safe_get("academic_level")
        advisor_name = self._safe_get("advisor_name")
        advisor_title = self._safe_get("advisor_title")

        subfields = []
        if major:
            subfields.append(_sf("a", major))
        if academic_level:
            subfields.append(_sf("c", academic_level))
        if advisor_name:
            if advisor_title:
                subfields.append(_sf("f", f"{advisor_title} {advisor_name}"))
            else:
                subfields.append(_sf("f", advisor_name))
        if advisor_title and not advisor_name:
            subfields.append(_sf("g", advisor_title))

        if subfields:
            self.record.add_ordered_field(
                Field(tag="915", indicators=Indicators(" ", " "), subfields=subfields)
            )

    # ------------------------------------------------------------------
    # 927 – Dạng tư liệu lưu thông (cục bộ DHYD)
    # ------------------------------------------------------------------
    def map_927(self):
        """Trường 927 (cục bộ DHYD): Dạng tư liệu lưu thông.
        Ưu tiên từ document_type, fallback dùng nature_of_content.
        """
        doc_type = self._safe_get("document_type", default="sach")
        code = self._DOC_TYPE_927.get(doc_type)

        # Fallback: suy luận từ nature_of_content nếu document_type không khớp
        if not code:
            nature_text = self._safe_get("nature_of_content", default="")
            nature_lower = nature_text.lower()
            if "luận án" in nature_lower or "luận văn" in nature_lower:
                code = "LA"
            elif "nghiên cứu" in nature_lower or "báo cáo" in nature_lower:
                code = "NCKH"
            elif "giáo trình" in nature_lower or "bài giảng" in nature_lower:
                code = "GT"
            elif "tạp chí" in nature_lower or "báo" in nature_lower:
                code = "TC"
            else:
                code = "TK"

        if code:
            self.record.add_ordered_field(
                Field(
                    tag="927",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", code),
                )
            )

    # ------------------------------------------------------------------
    # 932 – Phụ chú thỏa thuận công khai toàn văn (cục bộ DHYD)
    # ------------------------------------------------------------------
    def map_932(self):
        """Trường 932 (cục bộ DHYD): Phụ chú về thỏa thuận công khai toàn văn.
        $a: Nội dung thỏa thuận.
        """
        agreement = self._safe_get("access_agreement")
        if agreement:
            self.record.add_ordered_field(
                Field(
                    tag="932",
                    indicators=Indicators(" ", " "),
                    subfields=_subfields("a", agreement),
                )
            )

    # ------------------------------------------------------------------
    # Pipeline chính
    # ------------------------------------------------------------------
    def to_record(self) -> Record:
        """Thực thi toàn bộ quy trình ánh xạ và trả về biểu ghi MARC21."""
        self.map_leader()
        self.map_008()
        self.map_040()
        self.map_041()
        self.map_020()
        self.map_022()
        self.map_050()
        self.map_060()
        self.map_090()
        self.map_100()
        self.map_110()
        self.map_245()
        self.map_246()
        self.map_250()
        self.map_260()
        self.map_300()
        self.map_310()
        self.map_321()
        self.map_362()
        self.map_490()
        self.map_500()
        self.map_502()
        self.map_504()
        self.map_505()
        self.map_520()
        self.map_541()
        self.map_630()
        self.map_650()
        self.map_653()
        self.map_720()
        self.map_773()
        self.map_856()
        self.map_915()
        self.map_927()
        self.map_932()
        return self.record


def main():
    """Điểm chạy chính: đọc JSON, map, xuất .mrc và/hoặc .json."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "tài liệu", "extraction_result(strict).json")

    # Mặc định xuất cả 2 định dạng, trừ khi truyền --format
    fmt = "all"
    if len(sys.argv) > 1 and sys.argv[1].startswith("--format="):
        fmt = sys.argv[1].split("=", 1)[1]

    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    mapper = Marc21Mapper(raw_data)
    record = mapper.to_record()

    if fmt in ("mrc", "all"):
        mrc_path = os.path.join(base_dir, "output.mrc")
        with open(mrc_path, "wb") as f:
            f.write(record.as_marc())
        print(f"Wrote binary MARC21 to: {mrc_path}")

    if fmt in ("json", "all"):
        json_out_path = os.path.join(base_dir, "output_marc.json")
        with open(json_out_path, "w", encoding="utf-8") as f:
            writer = JSONWriter(f)
            writer.write(record)
            writer.close()
        print(f"Wrote MARC-in-JSON to: {json_out_path}")

    print(record)


if __name__ == "__main__":
    main()
