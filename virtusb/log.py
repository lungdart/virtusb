""" VirtUSB package """
import logging
import logging.config
import six

# Configure the logger for custom formatting
class ColoredFormatter(logging.Formatter):
    """ ANSI Colored Formatter """
    def format(self, record):
        """ Format the message """
        # Set the formatting style based on logging value
        if record.levelno == logging.DEBUG:
            fmt = '%(asctime)s %(name)s \033[94m%(levelname)s\033[0m - %(message)s'
        elif record.levelno == logging.INFO:
            fmt = '%(asctime)s %(name)s \033[92m%(levelname)s\033[0m - %(message)s'
        elif record.levelno == logging.WARNING:
            fmt = '%(asctime)s %(name)s \033[93m%(levelname)s\033[0m - %(message)s'
        elif record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            fmt = '%(asctime)s %(name)s \033[91m%(levelname)s\033[0m - %(message)s'
        else:
            fmt = '%(asctime)s %(name)s %(levelname)s - %(message)s'

        # Format the message
        if six.PY2:
            self._fmt = fmt
        else:
            self._style._fmt = fmt #pylint: disable=protected-access
        return super(ColoredFormatter, self).format(record)

# Set the logging configuration to use the custom formatter
logging.config.dictConfig({
    'version':1,
    'formatters': {
        'default': {'()': ColoredFormatter}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': logging.DEBUG
        }
    },
    'root': {
        'handlers': ['console'],
        'level': logging.DEBUG
    }
})

def get_logger(name='virtusb'):
    """ Get the logger instance """
    return logging.getLogger(name)
