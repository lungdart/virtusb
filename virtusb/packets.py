""" USBIP packet definitions """
#pylint: disable=C0103,C0326,R0903
from packeteer import fields, packets

### USB Sub-packets
class UrbSetup(packets.LittleEndian):
    """ URB Setup Block """
    fields = [
        fields.UInt8('bmRequestType', default=0x00),
        fields.UInt8('bRequest',      default=0x00),
        fields.UInt16('wValue',       default=0x0000),
        fields.UInt16('wIndex',       default=0x0000),
        fields.UInt16('wLength',      default=0x0000)
    ]

class EndpointDescriptor(packets.LittleEndian):
    """ USB Endpoint Descriptor """
    fields = [
        fields.UInt8('bLength',          default=0),
        fields.UInt8('bDescriptorType',  default=0),
        fields.UInt8('bEndpointAddress', default=0),
        fields.UInt8('bmAttributes',     default=0),
        fields.UInt16('wMaxPacketSize',  default=0),
        fields.UInt8('bInterval',        default=0)
    ]

class InterfaceDescriptor(packets.LittleEndian):
    """ USB Interface Descriptor """
    fields = [
        fields.UInt8('bLength',            default=0),
        fields.UInt8('bDescriptorType',    default=0),
        fields.UInt8('bInterfaceNumber',   default=0),
        fields.UInt8('bAlternateSetting',  default=0),
        fields.UInt8('bNumEndpoints',      default=0),
        fields.UInt8('bInterfaceClass',    default=0),
        fields.UInt8('bInterfaceSubClass', default=0),
        fields.UInt8('bInterfaceProtocol', default=0),
        fields.UInt8('iInterface',         default=0),
        fields.List('endpoints',
                    fields.Packet(default=EndpointDescriptor()),
                    size='bNumEndpoints')
    ]

class ConfigurationDescriptor(packets.LittleEndian):
    """ USB Configuration Descriptor """
    fields = [
        fields.UInt8('bLength',             default=0),
        fields.UInt8('bDescriptorType',     default=0),
        fields.UInt16('wTotalLength',       default=0),
        fields.UInt8('bNumInterfaces',      default=0),
        fields.UInt8('bConfigurationValue', default=0),
        fields.UInt8('iConfiguration',      default=0),
        fields.UInt8('bmAttributes',        default=0),
        fields.UInt8('bMaxPower',           default=0),
        fields.List('interfaces',
                    fields.Packet(default=InterfaceDescriptor()),
                    size='bNumInterfaces')
    ]

class DeviceDescriptor(packets.LittleEndian):
    """ USB Device descriptor sub packet """
    fields = [
        fields.UInt8('bLength',            default=0),
        fields.UInt8('bDescriptorType',    default=0),
        fields.UInt16('bcdUSB',            default=0),
        fields.UInt8('bDeviceClass',       default=0),
        fields.UInt8('bDeviceSubClass',    default=0),
        fields.UInt8('bDeviceProtocol',    default=0),
        fields.UInt8('bMaxPacketSize',     default=0),
        fields.UInt16('idVendor',          default=0),
        fields.UInt16('idProduct',         default=0),
        fields.UInt16('bcdDevice',         default=0),
        fields.UInt8('iManufacturer',      default=0),
        fields.UInt8('iProduct',           default=0),
        fields.UInt8('iSerialNumber',      default=0),
        fields.UInt8('bNumConfigurations', default=0)
    ]

### USBIP Operation packets
USBIP_VERSION  = 0x0111
OP_REQ_DEVLIST = 0x8005
OP_REP_DEVLIST = 0x0005
OP_REQ_IMPORT  = 0x8003
OP_REP_IMPORT  = 0x0003

class OpReqDevlist(packets.BigEndian):
    """ OP - Device list request """
    fields = [
        fields.UInt16('version', default=USBIP_VERSION),
        fields.UInt16('command', default=OP_REQ_DEVLIST),
        fields.UInt32('status',  default=0)
    ]

class OpRepDevlist(packets.BigEndian):
    """ OP - Device list response """
    # Packet contains a nested variable size device data structure
    class Device(packets.BigEndian):
        """ Repeating device data """
        class Iface(packets.BigEndian):
            """ Repeating interface data """
            fields = [
                fields.UInt8('iface_class',    default=0xff),
                fields.UInt8('iface_subclass', default=0xff),
                fields.UInt8('iface_proto',    default=0xff),
                fields.Padding()
            ]
        fields = [
            fields.String('path',           default='/',   size=256),
            fields.String('bus_id',         default='1-1', size=32),
            fields.UInt32('bus_num',        default=1),
            fields.UInt32('device_num',     default=1),
            fields.UInt32('speed',          default=2),
            fields.UInt16('vendor_id',      default=0x0000),
            fields.UInt16('product_id',     default=0x0000),
            fields.UInt16('device_version', default=0),
            fields.UInt8('device_class',    default=0xff),
            fields.UInt8('device_subclass', default=0xff),
            fields.UInt8('device_protocol', default=0xff),
            fields.UInt8('config_value',    default=1),
            fields.UInt8('config_count',    default=1),
            fields.UInt8('iface_count',     default=0),
            fields.List('ifaces',
                        fields.Packet(default=Iface()),
                        size='iface_count')
        ]

    fields = [
        fields.UInt16('version',      default=USBIP_VERSION),
        fields.UInt16('command',      default=OP_REP_DEVLIST),
        fields.UInt32('status',       default=0),
        fields.UInt32('device_count', default=0),
        fields.List('devices',
                    fields.Packet(default=Device()),
                    size='device_count')
    ]

class OpReqImport(packets.BigEndian):
    """ OP - Import request """
    fields = [
        fields.UInt16('version', default=USBIP_VERSION),
        fields.UInt16('command', default=OP_REQ_IMPORT),
        fields.UInt32('status',  default=0),
        fields.String('bus_id',  default='1-1', size=32)
    ]

class OpRepImport(packets.BigEndian):
    """ OP - Import response """
    fields = [
        fields.UInt16('version',        default=USBIP_VERSION),
        fields.UInt16('command',        default=OP_REP_IMPORT),
        fields.UInt32('status',         default=0),
        fields.String('full_path',      default='/',   size=256),
        fields.String('bus_id',         default='1-1', size=32),
        fields.UInt32('bus_no',         default=1),
        fields.UInt32('device_no',      default=1),
        fields.UInt32('device_speed',   default=2),
        fields.UInt16('vendor_id',      default=0x0000),
        fields.UInt16('product_id',     default=0x0000),
        fields.UInt16('device_version', default=0),
        fields.UInt8('device_class',    default=0xff),
        fields.UInt8('device_subclass', default=0xff),
        fields.UInt8('device_protocol', default=0xff),
        fields.UInt8('config_value',    default=1),
        fields.UInt8('config_count',    default=1),
        fields.UInt8('iface_count',     default=0)
    ]

### USBIP Communication packets
USBIP_CMD_SUBMIT = 0x0001
USBIP_RET_SUBMIT = 0x0003
USBIP_CMD_UNLINK = 0x0002
USBIP_RET_UNLINK = 0x0004

class UsbIpCmdSubmit(packets.BigEndian):
    """ USBIP - Submit request """
    fields = [
        fields.Padding(),
        fields.Padding(),
        fields.UInt16('command',        default=USBIP_CMD_SUBMIT),
        fields.UInt32('seq_num',        default=0),
        fields.UInt32('dev_id',         default=0),
        fields.UInt32('direction',      default=0x00000000),
        fields.UInt32('endpoint',       default=0x00000000),
        fields.UInt32('transfer_flags', default=0x00000000),
        fields.UInt32('buffer_len',     default=0),
        fields.UInt32('start_frame',    default=0),
        fields.UInt32('packet_count',   default=0),
        fields.UInt32('interval',       default=0),
        fields.Packet('setup',          default=UrbSetup())
    ]

class UsbIpRetSubmit(packets.BigEndian):
    """ USBIP - Submit response """
    fields = [
        fields.Padding(),
        fields.Padding(),
        fields.UInt16('command',        default=USBIP_RET_SUBMIT),
        fields.UInt32('seq_num',      default=0),
        fields.UInt32('dev_id',       default=0),
        fields.UInt32('direction',    default=0x00000000),
        fields.UInt32('endpoint',     default=0x00000000),
        fields.UInt32('status',       default=0),
        fields.UInt32('actual_len',   default=0),
        fields.UInt32('start_frame',  default=0),
        fields.UInt32('packet_count', default=0),
        fields.UInt32('error_count',  default=0),
        fields.Packet('setup',        default=UrbSetup())
    ]

class UsbIpCmdUnlink(packets.BigEndian):
    """ USBIP - Unlink request """
    fields = [
        fields.Padding(),
        fields.Padding(),
        fields.UInt16('command',   default=USBIP_CMD_UNLINK),
        fields.UInt32('seq_num',   default=0),
        fields.UInt32('dev_id',    default=0),
        fields.UInt32('direction', default=0x00000000),
        fields.UInt32('endpoint',  default=0x00000000),
        fields.UInt32('seq_num',   default=0)
    ]

class UsbIpRetUnlink(packets.BigEndian):
    """ USBIP - Unlink response """
    fields = [
        fields.Padding(),
        fields.Padding(),
        fields.UInt16('command',   default=USBIP_RET_UNLINK),
        fields.UInt32('seq_num',   default=0),
        fields.UInt32('dev_id',    default=0),
        fields.UInt32('direction', default=0x00000000),
        fields.UInt32('endpoint',  default=0x00000000),
        fields.UInt32('status',    default=0)
    ]
