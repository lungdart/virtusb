""" Test CLI handling """
#pylint: disable=C0326,R0205
from __future__ import unicode_literals, print_function
import pytest #pylint: disable=unused-import
from virtusb import cli
from tests.mocking.dummy_device import DummyDevice

class ExtendedParser(cli.Parser):
    def __init__(self):
        super(ExtendedParser, self).__init__()
        self.parser.add_argument('--test', action='store_true', help='DUMMY')

#@pytest.mark.skip()
def test_default_parser():
    """ Tests the default argument parser """
    parser      = cli.Parser()
    defaults    = parser.parse()
    count_short = parser.parse(['-n', '42'])
    count_long  = parser.parse(['--count', '42'])

    assert defaults.count    == 1
    assert count_short.count == 42
    assert count_long.count  == 42

#@pytest.mark.skip()
def test_extended_parser():
    """ Test extending the parser works as expected """
    parser = ExtendedParser()
    defaults    = parser.parse()
    dummy = parser.parse(['--test', '-n', '99'])

    assert defaults.count == 1
    assert not defaults.test
    assert dummy.count == 99
    assert dummy.test

#@pytest.mark.skip()
def test_server_factory():
    """ Tests the CLI server factory"""
    single_server = cli.server_factory(DummyDevice, 1)
    multi_server = cli.server_factory(DummyDevice, 3)

    assert len(single_server.controller.devices) == 1
    assert isinstance(single_server.controller.devices[0], DummyDevice)
    assert len(multi_server.controller.devices) == 3
    for device in single_server.controller.devices:
        assert isinstance(device, DummyDevice)


@pytest.mark.skip(reason='Not implemented (Requires a device script)')
def test_virtusb_main():
    """ Tests the built in main that loads external devices """
