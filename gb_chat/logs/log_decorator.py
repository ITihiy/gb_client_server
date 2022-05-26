import sys
import logging
import logs.client_log_config
import logs.server_log_config


def log(func):
    def inner(*args, **kwargs):
        logger_name = 'server_logger' if 'server.py' in sys.argv[0] else 'client_logger'
        LOGGER = logging.getLogger(logger_name)
        result = func(*args, **kwargs)
        LOGGER.info(
            f'function {func.__name__} called with {args}, {kwargs} from {sys._getframe().f_back.f_code.co_name}')
        return result

    return inner
