""" VirtUSB package """
#pylint: disable=C0326
import logging
import logging.config
import six

DEBUG    = 10
INFO     = 20
WARNING  = 30
ERROR    = 40
CRITICAL = 50

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

def gen_name(name=None):
    """ Converts the given name into a logging hierarchy name """
    if not name:
        name = 'virtusb'
    else:
        name = 'virtusb.' + str(name)
    return name

def get_logger(name=None):
    """ Get the packages logger """
    logger = logging.getLogger(gen_name(name))

    # Configure logger handler if it's not already
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)

    return logger

def set_level(level):
    """ Set the default verbosity level of the root logger """
    logger = get_logger()
    logger.setLevel(level)
