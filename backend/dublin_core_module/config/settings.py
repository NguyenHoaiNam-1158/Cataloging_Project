class DublinCoreSettings:
    
    ELEMENTS = [
        "title", "creator", "subject", "description", "publisher",
        "contributor", "date", "type", "format", "identifier",
        "source", "language", "relation", "coverage", "rights",
    ]

    REQUIRED_ELEMENTS = ["title", "creator", "date", "type"]

    DOC_TYPE_LABELS = {
        "luan_van": "Luận văn",
        "luan_an": "Luận án",
        "khoa_luan": "Khóa luận",
        "bao_cao_nckh": "Báo cáo nghiên cứu khoa học",
        "sach": "Sách",
        "tap_chi": "Tạp chí",
    }

    DCMI_TYPE = "Text"

    DEFAULT_LANGUAGE = "vie"

    CORPORATE_SEPARATOR = "|"


settings = DublinCoreSettings()
