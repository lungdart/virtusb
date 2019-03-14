""" Test base USBIP server components """
import pytest
from virtusb.server import UsbIpServer
from virtusb.controller import VirtualController
from tests.mocking.client import UsbIpClient
from tests.mocking.dummy_device import DummyDevice

def test_list_empty():
    """ Test listing all devices on an empty controller """
    controller = VirtualController()
    server = UsbIpServer(controller)
    server.start()
    client = UsbIpClient()

    try:
        devices = client.list()
        assert len(devices) == 0 #pylint: disable=len-as-condition
    finally:
        server.stop()

def test_list_single():
    """ Test listing all devices on a controller with a single device """
    controller = VirtualController()
    controller.devices = [DummyDevice()]
    server = UsbIpServer(controller)
    server.start()
    client = UsbIpClient()

    try:
        devices = client.list()
        assert len(devices) == 1
    finally:
        server.stop()

def test_list_multi():
    """ Test listing all devices on a controller with multiple devices """
    controller = VirtualController()
    controller.devices = [DummyDevice(), DummyDevice(), DummyDevice()]
    server = UsbIpServer(controller)
    server.start()
    client = UsbIpClient()

    try:
        devices = client.list()
        assert len(devices) == len(controller.devices)
    finally:
        server.stop()
