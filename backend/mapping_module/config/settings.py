import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("MAPPING_MODULE")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LA5PGzWA-ySKfXoocYZ1pZieloqU56g2_n2EKzXaZfNg")
    
    DEFAULT_ORG_CODE = "DHYD"
    DEFAULT_LANGUAGE = "vie"
    DEFAULT_COUNTRY_CODE = "vm "
    CATALOGING_RULES = "AACR2"
    DEFAULT_DIMENSION = "30 cm"
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DEPARTMENTS_JSON_PATH = os.path.join(BASE_DIR, "resources", "ump_departments.json")
    RAG_INDEX_DIR = os.path.join(BASE_DIR, "rag_index")

    NLM_OUTPUT_FILE = os.path.join(RAG_INDEX_DIR, "nlm_classification.json")
    LCC_OUTPUT_FILE = os.path.join(RAG_INDEX_DIR, "lcc_master_index_plumber_fast.json")
    SUBJECT_650_OUTPUT_FILE = os.path.join(RAG_INDEX_DIR, "subject_650_index.json")
    FINAL_OUTPUT_FILE = "final_marc21_record.json"
    
    BASE_URL = "https://classification.nlm.nih.gov"
    DELAY = 1.5 
    PDF_FOLDER = r"E:\Cataloging_Project\backend\mapping_module\file_tailieu"
    PDF_FOLDER_650 = r"E:\Cataloging_Project\backend\mapping_module\file_subject_650"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    ALL_SCHEDULES = [
        "QS","QT","QU","QV","QW","QX","QY","QZ",
        "W","WA","WB","WC","WD","WE","WF","WG","WH","WI","WJ",
        "WK","WL","WM","WN","WO","WP","WQ","WR","WS","WT","WU",
        "WV","WW","WX","WY","WZ"
    ]

    DOCUMENT_TYPE_MAP = {
        "bb": "BB", "bgdt": "BGDT", "cbkh": "CBKH", "ck": "CK",
        "dpt": "DPT", "gt": "GT", "ht": "HT", "kl": "KL",
        "la": "LA", "nckh": "NCKH", "tc": "TC", "tckt": "TCKT",
        "tk": "TK", "vbsc": "VBSC",
    }

    NATURE_CONTENT_MAP = {
        "luan van": "LA", "luan an": "LA", "khoa luan": "LA",
        "bao cao nckh": "NCKH", "sach": "CK", "tap chi": "TC",
    }

    DOC_TYPE_008_MAP = {
        "luan_van": "m   ", "luan_an": "m   ", "khoa_luan": "m   ",
        "bao_cao_nckh": "t   ", "sach": "    ", "tap_chi": "    ",
    }

    log = logger

GEMINI_API_KEY = Settings.GEMINI_API_KEY
BASE_DIR = Settings.BASE_DIR
DEFAULT_CATALOGING_AGENCY = Settings.DEFAULT_ORG_CODE
DEFAULT_LANGUAGE = Settings.DEFAULT_LANGUAGE
DEFAULT_COUNTRY = Settings.DEFAULT_COUNTRY_CODE
CATALOGING_RULES = Settings.CATALOGING_RULES
DOC_TYPE_008_MAP = Settings.DOC_TYPE_008_MAP
UMP_DEPARTMENTS_PATH = Settings.DEPARTMENTS_JSON_PATH
LCC_OUTPUT_FILE = Settings.LCC_OUTPUT_FILE
NLM_OUTPUT_FILE = Settings.NLM_OUTPUT_FILE
FINAL_OUTPUT_FILE = Settings.FINAL_OUTPUT_FILE

BASE_URL = Settings.BASE_URL
DELAY = Settings.DELAY
PDF_FOLDER = Settings.PDF_FOLDER
PDF_FOLDER_650 = Settings.PDF_FOLDER_650
HEADERS = Settings.HEADERS
ALL_SCHEDULES = Settings.ALL_SCHEDULES

log = logger