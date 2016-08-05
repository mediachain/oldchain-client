import logging
from logging.config import dictConfig
from copy import deepcopy

BASE_CONFIG = dict(
    version=1,
    disable_existing_loggers=False,
    formatters={
        'standard': {'format':
                     '[%(asctime)s %(levelname)s %(name)s] - %(message)s'}
    },
    handlers={
        'null': {'class': 'logging.NullHandler',
                 'level': logging.DEBUG},

        'console': {'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': logging.DEBUG}
    },
    loggers={
        '': {'handlers': ['null'],
             'level': logging.DEBUG}
    }
)


_LOGGER_CONFIG = BASE_CONFIG


def get_logger(name):
    global _LOGGER_CONFIG
    dictConfig(_LOGGER_CONFIG)
    return logging.getLogger(name)


def config_logging(logger_name='mediachain',
                   console=True,
                   filename=None,
                   filemode='a',
                   level=logging.DEBUG):
    config = deepcopy(BASE_CONFIG)

    enabled_handlers = []
    if console:
        enabled_handlers.append('console')
    if filename:
        config['handlers']['file'] = {'class': 'logging.FileLogger',
                                      'formatter': 'standard',
                                      'filename': filename,
                                      'mode': filemode}
        enabled_handlers.append('file')

    config['loggers'] = {
        logger_name: {
            'handlers': enabled_handlers,
            'level': level
        }
    }
    global _LOGGER_CONFIG
    _LOGGER_CONFIG = config
    dictConfig(config)
