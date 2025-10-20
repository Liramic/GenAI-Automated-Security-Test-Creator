import logging
import datetime
import os

# create a unique id with datetime:
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_file_path = os.path.join(LOGS_DIR, f"{now_str}.log")

# general object per run:
logger = logging.getLogger('TestGenLogger')
logger.setLevel(logging.INFO)

# Avoid adding handlers multiple times if module re-imported
if not logger.handlers:
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # also log to console for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def log_warning(msg):
    logger.warning(msg)