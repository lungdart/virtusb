""" Command line argument parser """
#pylint: disable=C0326,R0205
from __future__ import unicode_literals
import argparse
from virtusb.server import UsbIpServer
from virtusb.controller import VirtualController

class Parser(object): #pylint: disable=too-few-public-methods
    """ Argument parser extension """
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Simulate a USB device")
        self.parser.add_argument(
            '-n', '--count', type=int, default=1,
            help='Number of virtual devices to simulator')

    def parse(self, args=None):
        """ Parse the given arguments, or the command line """
        if args is None:
            args = []
        options = self.parser.parse_args(args)
        return options

def server_factory(device, count):
    """ Generate a virtusb server """
    controller = VirtualController()
    controller.devices = [device() for _ in range(count)]
    server = UsbIpServer(controller)

    return server
