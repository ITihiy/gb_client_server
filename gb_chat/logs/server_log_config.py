import logging
import os
from logging.handlers import TimedRotatingFileHandler

server_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log')
log_file = TimedRotatingFileHandler(log_file_path, encoding='utf-8', when='d', interval=1)
log_file.setFormatter(server_formatter)
logger = logging.getLogger('server_logger')
logger.addHandler(log_file)
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    logger.info('INFO message')
    logger.debug('DEBUG message')
    logger.error('ERROR message')
    logger.critical('CRITICAL message')
