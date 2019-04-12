""" Pre-configure logging before running tests """
from virtusb import log
import pytest

@pytest.fixture(autouse=True)
def configure():
    """ Enable all logging levels for testing """
    log.set_level(log.DEBUG)
