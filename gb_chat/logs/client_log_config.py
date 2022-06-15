import logging
import os

client_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client.log')
log_file = logging.FileHandler(log_file_path, encoding='utf-8')
log_file.setFormatter(client_formatter)
logger = logging.getLogger('client_logger')
logger.addHandler(log_file)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    logger.info('INFO message')
    logger.debug('DEBUG message')
    logger.error('ERROR message')
    logger.critical('CRITICAL message')
