""" USB Virtual Controller """
#pylint: disable=R0205,C0326,W1202
from virtusb import log, packets
LOGGER = log.get_logger()

# USB Direction
HOST_TO_DEVICE            = 0x00
DEVICE_TO_HOST            = 0x80

# USB Request codes
USB_REQ_GET_STATUS        = 0x00
USB_REQ_GET_DESCRIPTOR    = 0x06
USB_REQ_SET_DESCRIPTOR    = 0x07
USB_REQ_GET_CONFIGURATION = 0x08
USB_REQ_SET_CONFIGURATION = 0x09

# USB Descriptor values
USB_DEVICE_DESCRIPTOR   = 0x0100
USB_CONFIG_DESCRIPTOR   = 0x0200


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
        if req_type == DEVICE_TO_HOST and request == USB_REQ_GET_DESCRIPTOR:
            if value == USB_DEVICE_DESCRIPTOR:
                LOGGER.debug('Descriptor request: DEVICE')
                return self.pack_device_descriptor(device)
            if value == USB_CONFIG_DESCRIPTOR:
                LOGGER.debug('Descriptor request: CONFIGURATION')
                return self.pack_config_descriptor(device)

        # Handle get status
        if req_type == DEVICE_TO_HOST and request == USB_REQ_GET_STATUS:
            LOGGER.debug('Status request')
            return self.pack_status(device)

        # Handle setting configuration
        if req_type == HOST_TO_DEVICE and request == USB_REQ_SET_CONFIGURATION:
            LOGGER.debug('Set configuration request: {}'.format(value))
            device.set_configuration(value)
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
    def pack_status(device): #pylint: disable=unused-argument
        """ Pack a devices status """
        # TODO: Implement
        return b''

    def unhandled_request(self, setup): #pylint: disable=unused-argument
        """ Unhandled request for logging purposes """
        return None

class VirtualDevice(object):
    """ Virtual USB Device """
    def __init__(self, device_descriptor):
        self.descriptor    = device_descriptor
        self.active_config = None
        self.speed         = 2 # Hardcoded high speed device
        self.max_payload   = 64 # TODO: Dynamically set payload
        self.set_configuration()

    def _find_config_from_value(self, config_value):
        """ Find a configuration descriptor instance from it's value """
        for config in self.descriptor.configurations:
            if config.bConfigurationValue == config_value:
                return config
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

    def handle(self, packet, data=None):
        """ Override this method to control how a USB device handles submit requests """

    def start(self):
        """ Override this method for starting an optional device simulator """

    def stop(self):
        """ Override this method for stopping an optional device simulator """
