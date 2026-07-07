import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

from modules.postprocessing.data_parser import DataParser


def test_parse_simple():
    parser = DataParser()
    text = "* title_main: Test Title\n* author_personal_name: John Doe"
    result = parser.parse_text_to_json(text)
    assert result["title_main"] == "Test Title"
    assert result["author_personal_name"] == "John Doe"


def test_parse_null_values():
    parser = DataParser()
    text = "* title_main: Test\n* publication_year: null"
    result = parser.parse_text_to_json(text)
    assert result["title_main"] == "Test"
    assert result["publication_year"] is None


def test_parse_array_fields():
    parser = DataParser()
    text = "* subject_terms: AI|ML|NLP\n* general_notes: Note 1"
    result = parser.parse_text_to_json(text)
    assert result["subject_terms"] == ["AI", "ML", "NLP"]
    assert result["general_notes"] == ["Note 1"]


def test_parse_empty_array_fields():
    parser = DataParser()
    text = "* subject_terms: null\n* isbn: null"
    result = parser.parse_text_to_json(text)
    assert result["subject_terms"] == []
    assert result["isbn"] == []


def test_parse_default_values():
    parser = DataParser()
    result = parser.parse_text_to_json("")
    assert result["document_type"] is None
    assert result["title_main"] is None
    assert result["subject_terms"] == []
    assert result["extraction_metadata"]["source_pages_used"] == []
