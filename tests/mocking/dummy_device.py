""" Mock USB device for testing """
#pylint: disable=C0326,R0205
from virtusb import descriptors
from virtusb.controller import VirtualDevice

class DummyDevice(VirtualDevice):
    """ Mock device for testing purposes """
    _dummy_descriptor = descriptors.Device(
        bcdUSB              = 0x0101,
        bDeviceClass        = 0xff,
        bDeviceSubClass     = 0xff,
        bDeviceProtocol     = 0xff,
        bMaxPacketSize      = 64,
        idVendor            = 0xdead,
        idProduct           = 0xbeef,
        bcdDevice           = 0x0100,
        iManufacturer       = 0x00,
        iProduct            = 0x00,
        iSerialNumber       = 0x00,
        bNumConfigurations  = 0x01,
        configurations      = [descriptors.Configuration(
            bNumInterfaces       = 0x01,
            bConfigurationValue  = 0x01,
            iConfiguration       = 0x00,
            bmAttributes         = 0xe0,
            bMaxPower            = 0xfa,
            interfaces           = [descriptors.Interface(
                bInterfaceNumber    = 0x00,
                bAlternateSetting   = 0x00,
                bNumEndpoints       = 0x02,
                bInterfaceClass     = 0xff,
                bInterfaceSubClass  = 0xff,
                bInterfaceProtocol  = 0xff,
                iInterface          = 0x00,
                endpoints           = [descriptors.Endpoint(
                    bEndpointAddress    = 0x01,
                    bmAttributes        = 0x02,
                    wMaxPacketSize      = 64,
                    bInterval           = 0x00
                )]
            )]
        )]
    )
    def __init__(self):
        super(DummyDevice, self).__init__(self._dummy_descriptor)
