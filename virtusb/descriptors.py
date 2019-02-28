""" USB Descriptor Classes """
#pylint: disable=C0326,R0902,R0903
import copy

class Device(object):
    """ USB Device Descriptor """
    def __init__(self, **kwargs):
        #pylint: disable=invalid-name
        # Immutable values
        self.bLength         = 18
        self.bDescriptorType = 0x01

        # TODO: Unsupported values
        self.bcdUSB         = 0x1001
        self.bMaxPacketSize = 64
        self.iManufacturer  = 0
        self.iProduct       = 0
        self.iSerialNumber  = 0

        # Mutable values
        self.bDeviceClass    = kwargs.get("bDeviceClass",    0xff)
        self.bDeviceSubClass = kwargs.get("bDeviceSubClass", 0xff)
        self.bDeviceProtocol = kwargs.get("bDeviceProtocol", 0xff)
        self.idVendor        = kwargs.get("idVendor",        0x0000)
        self.idProduct       = kwargs.get("idProduct",       0x0000)
        self.bcdDevice       = kwargs.get("bcdDevice",       0x0000)

        # Sub descriptors
        self._configurations    = None
        self.bNumConfigurations = None
        self.clear_configurations()
        self.set_configurations(kwargs.get("configurations", []))
        #pylint: enable=invalid-name

    @property
    def configurations(self):
        """ Property to force configurations to be read only """
        return copy.deepcopy(self._configurations)

    def set_configurations(self, configurations):
        """ Set the list of configurations and dependent values """
        assert isinstance(configurations, (list, tuple))
        self._configurations    = configurations
        self.bNumConfigurations = len(configurations)

    def clear_configurations(self):
        """ Remove all configurations """
        self._configurations    = []
        self.bNumConfigurations = 0

class Configuration(object):
    """ USB Configuration Descriptor """
    def __init__(self, **kwargs):
        #pylint: disable=invalid-name
        # Immutable values
        self.bLength             = 9
        self.bDescriptorType     = 0x02

        # TODO: Unsupported values
        self.bMaxPower      = 250
        self.iConfiguration = 0

        # Mutable values
        self.bConfigurationValue = kwargs.get("bConfigurationValue", 1)
        self.bmAttributes        = kwargs.get("bmAttributes",        0xe0)

        # Sub descriptors
        self._interfaces    = None
        self.bNumInterfaces = None
        self.wTotalLength   = None
        self.clear_interfaces()
        self.set_interfaces(kwargs.get("interfaces", []))
        #pylint: enable=invalid-name

    @property
    def interfaces(self):
        """ Property to force interfaces to be read only """
        return copy.deepcopy(self._interfaces)

    def set_interfaces(self, interfaces):
        """ Set the list of interface descriptors and dependent values """
        assert isinstance(interfaces, (list, tuple))
        self._interfaces = interfaces
        self.bNumInterfaces = len(interfaces)
        self.wTotalLength = self.bLength
        for iface in self._interfaces:
            self.wTotalLength += iface.bLength
            for endpoint in iface.endpoints:
                self.wTotalLength += endpoint.bLength

    def clear_interfaces(self):
        """ Remove all interfaces """
        self._interfaces    = []
        self.bNumInterfaces = 0
        self.wTotalLength   = self.bLength

class Interface(object):
    """ USB Interface Descriptor """
    def __init__(self, **kwargs):
        #pylint: disable=invalid-name
        # Immutable values
        self.bLength         = 9
        self.bDescriptorType = 0x04

        # TODO: Unsupported values
        self.iInterface = kwargs.get("iInterface")

        # Mutable values
        self.bInterfaceNumber   = kwargs.get("bInterfaceNumber",   0)
        self.bAlternateSetting  = kwargs.get("bAlternateSetting",  0)
        self.bInterfaceClass    = kwargs.get("bInterfaceClass",    0xff)
        self.bInterfaceSubClass = kwargs.get("bInterfaceSubClass", 0xff)
        self.bInterfaceProtocol = kwargs.get("bInterfaceProtocol", 0xff)

        # Sub descriptors
        self._endpoints    = None
        self.bNumEndpoints = None
        self.clear_endpoints()
        self.set_endpoints(kwargs.get("endpoints", []))
        #pylint: enable=invalid-name

    @property
    def endpoints(self):
        """ Property to force endpoints to be read only """
        return copy.deepcopy(self._endpoints)

    def set_endpoints(self, endpoints):
        """ Set the list of endpoint descriptors and dependent values """
        assert isinstance(endpoints, (list, tuple))
        self._endpoints    = endpoints
        self.bNumEndpoints = len(endpoints)

    def clear_endpoints(self):
        """ Remove all endpoints """
        self._endpoints    = []
        self.bNumEndpoints = 0

class Endpoint(object):
    """ USB Endpoint Descriptor """
    def __init__(self, **kwargs):
        #pylint: disable=invalid-name
        # Immutable values
        self.bLength         = 7
        self.bDescriptorType = 0x05

        # TODO: Unsupported values
        self.wMaxPacketSize = 64
        self.bInterval      = 0

        # Mutable values
        self.bEndpointAddress    = kwargs.get("bEndpointAddress", 0x01)
        self.bmAttributes        = kwargs.get("bmAttributes",     0x02)
        #pylint: enable=invalid-name
