import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s - %(lineno)d",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "app.log",
            "formatter": "detailed",
        },
    },
    "loggers": {
        "": {  # 根日志记录器
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)
