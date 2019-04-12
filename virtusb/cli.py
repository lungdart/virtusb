""" Command line argument parser """
#pylint: disable=C0326,R0205
from __future__ import unicode_literals
import os
import argparse
from virtusb import log
from virtusb.server import UsbIpServer
from virtusb.controller import VirtualController

LOGGER = log.get_logger()

class Parser(object): #pylint: disable=too-few-public-methods
    """ Argument parser extension """
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Simulate a USB device")
        self.parser.add_argument(
            '-n', '--count', type=int, default=1,
            help='Number of virtual devices to simulator')
        self.parser.add_argument(
            '-v', '--verbose', action='count', default=0,
            help='Add more logging verbosity')

    def parse(self, args=None):
        """ Parse the given arguments, or the command line """
        if args is None:
            args = []
        options = self.parser.parse_args(args)

        # Set logging level based on verbosity
        if options.verbose == 0:
            log.set_level(log.WARNING)
        if options.verbose == 1:
            log.set_level(log.INFO)
        if options.verbose >= 2:
            log.set_level(log.DEBUG)

        return options

def server_factory(device, count):
    """ Generate a virtusb server """
    controller = VirtualController()
    controller.devices = [device() for _ in range(count)]
    server = UsbIpServer(controller)

    if os.getuid() == 0:
        #pylint: disable=line-too-long
        LOGGER.warning('Super user permissions required for usbip. sudo will be used to escalate permissions when needed. You may be prompted for a password depending on your system configuration.')

    return server
