""" USB Virtual Controller """
#pylint: disable=R0205,C0326
from __future__ import unicode_literals
import struct
from virtusb import log, packets
LOGGER = log.get_logger()

# USB Request codes
USB_REQ_GET_STATUS        = 0x00
USB_REQ_GET_DESCRIPTOR    = 0x06
USB_REQ_SET_DESCRIPTOR    = 0x07
USB_REQ_GET_CONFIGURATION = 0x08
USB_REQ_SET_CONFIGURATION = 0x09
USB_REQ_SET_INTERFACE     = 0x0b

# USB Descriptor values
USB_DEVICE_DESCRIPTOR   = 0x0100
USB_CONFIG_DESCRIPTOR   = 0x0200

# USB Direction checks
def host_to_device(request_type):
    """ Check if the direction is host to device """
    return (request_type & 0x80) == 0x00

def device_to_host(request_type):
    """ Check if the direction is device to host """
    return (request_type & 0x80) == 0x80

# USB Virtual Components
class VirtualController(object):
    """ Virtual USB Controller """
    def __init__(self, bus_no=1, path='/sys/devices/pci0000:00/0000:00:14.0/usb1/'):
        self.bus_no   = bus_no
        self.path     = path
        self.devices  = []

    def get_device(self, device_id):
        """ Fetch the device by it's id """
        bus_no     = device_id >> 16
        device_no  = device_id & 0x0000ffff
        device_idx = device_no - 1
        assert bus_no == self.bus_no
        assert device_idx >= 0
        assert device_idx < len(self.devices)

        return self.devices[device_idx]

    def handle(self, packet, data=None):
        """ Handle submitted URBs """
        #pylint: disable=too-many-return-statements
        # Request the device to handle non control requests
        device_id = packet['dev_id']
        device    = self.get_device(device_id)
        if packet['endpoint'] != 0:
            return device.handle(packet, data)

        # Handle get descriptors
        setup    = packet['setup']
        req_type = setup['bmRequestType']
        request  = setup['bRequest']
        value    = setup['wValue']
        if device_to_host(req_type) and request == USB_REQ_GET_DESCRIPTOR:
            if value == USB_DEVICE_DESCRIPTOR:
                LOGGER.debug('Descriptor request: DEVICE')
                return self.pack_device_descriptor(device)
            if value == USB_CONFIG_DESCRIPTOR:
                LOGGER.debug('Descriptor request: CONFIGURATION')
                return self.pack_config_descriptor(device)

        # Handle get status
        if device_to_host(req_type) and request == USB_REQ_GET_STATUS:
            LOGGER.debug('Status request')
            return self.pack_status(device)

        # Handle setting configuration
        if host_to_device(req_type) and request == USB_REQ_SET_CONFIGURATION:
            LOGGER.debug('Set configuration request: %i', value)
            device.set_configuration(value)
            return None

        if host_to_device(req_type) and request == USB_REQ_SET_INTERFACE:
            interface = value >> 1
            LOGGER.debug('Set interface request: %i', interface)
            device.set_interface(interface)
            return None

        # Report unhandled requests
        LOGGER.error('Unhandled request')
        return self.unhandled_request(setup)

    @staticmethod
    def pack_device_descriptor(device):
        """ Pack the devices descriptor into a packet """
        descriptor = device.descriptor
        packet = packets.DeviceDescriptor(
            bLength            = descriptor.bLength,
            bDescriptorType    = descriptor.bDescriptorType,
            bcdUSB             = descriptor.bcdUSB,
            bDeviceClass       = descriptor.bDeviceClass,
            bDeviceSubClass    = descriptor.bDeviceSubClass,
            bDeviceProtocol    = descriptor.bDeviceProtocol,
            bMaxPacketSize     = descriptor.bMaxPacketSize,
            idVendor           = descriptor.idVendor,
            idProduct          = descriptor.idProduct,
            bcdDevice          = descriptor.bcdDevice,
            iManufacturer      = descriptor.iManufacturer,
            iProduct           = descriptor.iProduct,
            iSerialNumber      = descriptor.iSerialNumber,
            bNumConfigurations = descriptor.bNumConfigurations
        )
        return packet.pack()

    @staticmethod
    def pack_config_descriptor(device):
        """ Pack the devices configuration descriptor with interfaces and endpoints """
        LOGGER.debug('Descriptor request: CONFIGURATION')

        # Build each interface, including their endpoints
        config = device.active_config
        iface_packets = []
        for iface in config.interfaces:
            # Build each interfaces endpoints
            ep_packets = []
            for endpoint in iface.endpoints:
                ep_packets.append(packets.EndpointDescriptor(
                    bLength = endpoint.bLength,
                    bDescriptorType = endpoint.bDescriptorType,
                    bEndpointAddress = endpoint.bEndpointAddress,
                    bmAttributes = endpoint.bmAttributes,
                    wMaxPacketSize = endpoint.wMaxPacketSize,
                    bInterval = endpoint.bInterval))
            iface_packets.append(packets.InterfaceDescriptor(
                bLength = iface.bLength,
                bDescriptorType = iface.bDescriptorType,
                bInterfaceNumber = iface.bInterfaceNumber,
                bAlternateSetting = iface.bAlternateSetting,
                bNumEndpoints = iface.bNumEndpoints,
                bInterfaceClass = iface.bInterfaceClass,
                bInterfaceSubClass = iface.bInterfaceSubClass,
                bInterfaceProtocol = iface.bInterfaceProtocol,
                iInterface = iface.iInterface,
                endpoints = ep_packets))
        # Build the config including all interfaces
        packet = packets.ConfigurationDescriptor(
            bLength             = config.bLength,
            bDescriptorType     = config.bDescriptorType,
            wTotalLength        = config.wTotalLength,
            bNumInterfaces      = config.bNumInterfaces,
            bConfigurationValue = config.bConfigurationValue,
            iConfiguration      = config.iConfiguration,
            bmAttributes        = config.bmAttributes,
            bMaxPower           = config.bMaxPower,
            interfaces          = iface_packets)

        return packet.pack()

    @staticmethod
    def pack_status(device):
        """ Pack a devices status """
        #pylint: disable=unused-argument
        # TODO: Implement
        return b''

    def unhandled_request(self, setup):
        #pylint: disable=no-self-use
        """ Unhandled request for logging purposes """
        LOGGER.debug('%s', repr(setup))

class VirtualDevice(object):
    """ Virtual USB Device """
    def __init__(self, device_descriptor):
        self.descriptor    = device_descriptor
        self.active_config = None
        self.active_iface  = None
        self.speed         = 2 # Hardcoded high speed device
        self.max_payload   = 64 # TODO: Dynamically set payload
        self.set_configuration()

    def _find_config_from_value(self, config_value):
        """ Find a configuration descriptor instance from it's value """
        for config in self.descriptor.configurations:
            if config.bConfigurationValue == config_value:
                return config
        return None

    def _find_iface_from_value(self, iface_value):
        """ Find an interface descriptor instance from it's value """
        if self.active_config is None:
            raise RuntimeError('Attempted to look for interface before configuration was set')

        for iface in self.active_config.interfaces:
            if iface.bInterfaceNumber == iface_value:
                return iface
        return None

    def set_configuration(self, config_value=None):
        """ Set the active configuration to the given value """
        # If no value is given, use the first available configuration
        if config_value is None:
            self.active_config = self.descriptor.configurations[0]
            return

        config = self._find_config_from_value(config_value)
        if config is None:
            raise RuntimeError('Invalid config value')
        self.active_config = config

    def set_interface(self, iface_value=None):
        """ Set the active interface to the given value """
        if self.active_config is None:
            LOGGER.warning('Request to set interface before setting configuration. Using first configuration instance.')
            self.set_configuration()

        if iface_value is None:
            self.active_iface = self.active_config.interfaces[0]
            return

        interface = self._find_iface_from_value(iface_value)
        if interface is None:
            raise RuntimeError('Invalid interface value')
        self.active_iface = interface

    def handle(self, packet, data=None):
        """ Override this method to control how a USB device handles submit requests """

    def start(self):
        """ Override this method for starting an optional device simulator """

    def stop(self):
        """ Override this method for stopping an optional device simulator """
