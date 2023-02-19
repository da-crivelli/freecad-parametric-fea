import logging
import logging.config

# taken from https://guicommits.com/how-to-log-in-python-like-a-pro/
ERROR_LOG_FILENAME = "./freecadparametricfea.log"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {  # The formatter name, it can be anything that I wish
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d " \
                      "%(levelname)s %(message)s",  # What to add in the message
            "datefmt": "%Y-%m-%d %H:%M:%S",  # How to display dates
        },
        "simple": {  # The formatter name
            "format": "%(message)s",  # As simple as possible!
        },
    },
    "handlers": {
        "logfile": {  # The handler name
            "formatter": "default",  # Refer to the formatter defined above
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",  # OUTPUT: Which class to use
            "filename": ERROR_LOG_FILENAME,
            "backupCount": 2,
        },
        "verbose_output": {  # The handler name
            "formatter": "simple",  # Refer to the formatter defined above
            "level": "DEBUG",  # FILTER: All logs
            "class": "logging.StreamHandler",  # OUTPUT: Which class to use
            "stream": "ext://sys.stdout",  # Stream to console
        },
    },
    "loggers": {
        "FreecadParametricFEA": {  # The name of the logger
            "level": "INFO",  # FILTER: only INFO logs onwards
            "handlers": [
                "logfile",  # Refer the handler defined above
            ],
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
