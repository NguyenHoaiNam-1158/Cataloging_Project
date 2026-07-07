import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

from modules.llm_adapters.base_adapter import BaseLLMAdapter
from modules.llm_adapters.gemini_adapter import GeminiAdapter
from modules.llm_adapters.qwen_adapter import QwenAdapter
from modules.ocr_adapters.base_ocr_adapter import BaseOCRAdapter


def test_base_llm_adapter_abstract():
    assert "extract_data" in BaseLLMAdapter.__abstractmethods__
    assert "extract_text_data" in BaseLLMAdapter.__abstractmethods__


def test_gemini_adapter_implements_base():
    assert issubclass(GeminiAdapter, BaseLLMAdapter)


def test_qwen_adapter_implements_base():
    assert issubclass(QwenAdapter, BaseLLMAdapter)


def test_base_ocr_adapter_abstract():
    assert "process_pdf" in BaseOCRAdapter.__abstractmethods__
