# backend/quiet_logging.py

import os

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1") 
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


import logging
import warnings

_NOISY_LOGGERS = (
    "httpx", "httpcore",                       # dòng "HTTP Request: HEAD https://huggingface..."
    "faiss", "faiss.loader",                   # "Loading faiss with AVX2 support..."
    "sentence_transformers", "SentenceTransformer",  # "No device provided, using cpu"
    "transformers",
    "huggingface_hub", "filelock",             # "sending unauthenticated requests to the HF Hub"
    "urllib3",
)


def quiet_third_party(level: int = logging.WARNING) -> None:
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(level)
    # Ẩn FutureWarning của google.generativeai và các cảnh báo deprecate khác
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)


def setup_logging(app_level: int = logging.INFO) -> None:
    """Cấu hình log cho hệ thống + làm im lặng thư viện bên thứ ba.

    Gọi 1 lần, ở NGAY ĐẦU main.py, trước mọi import nặng.
    """
    logging.basicConfig(
        level=app_level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    quiet_third_party()
