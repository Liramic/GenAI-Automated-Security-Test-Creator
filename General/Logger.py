import logging
import datetime

#create a unique id with datetime:
now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d_%H-%M-%S")

#general object per run:
logger = logging.getLogger('TestGenLogger')
logging.basicConfig(filename=f'./Logs/{now_str}.log', level=logging.INFO)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def log_warning(msg):
    logger.warning(msg)