import logging
import sys

#hàm định dạng log

def setup_logging():
    #sys.stdout.reconfigure(encoding='utf-8')
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            #logging.FileHandler("app.log")
            # Có thể thêm logging.FileHandler("app.log") ở đây nếu muốn lưu log ra file text
        ]
    )