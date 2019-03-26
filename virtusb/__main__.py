""" Run the virtusb module as a standalone server """
from __future__ import unicode_literals
import sys
import os
import argparse
import importlib
# from virtusb.server import UsbIpServer
# from virtusb.controller import VirtualController

def get_device_path(args):
    """ Parse the input arguments """
    parser = argparse.ArgumentParser(description="Simulate a USB device")
    parser.add_argument('device', type=str,
                        help='Path to the virtual USB device script')
    options = parser.parse_args(args)

    device_path = options.device
    if not os.path.isfile(device_path):
        raise RuntimeError('Device file does not exist: {}'.format(device_path))

    return options.device

def get_device_main(file):
    """ Loads the given driver """
    module = importlib.import_module(file)
    callback = module.__main__.main

    return callback

def main():
    """ MAIN """
    args = sys.argv[1:2]
    device_path = get_device_path(args)
    device_main = get_device_main(device_path)

    if len(sys.argv) > 2:
        args = sys.argv[3:]
    else:
        args = None
    device_main(*args)

if __name__ == '__main__':
    main()
