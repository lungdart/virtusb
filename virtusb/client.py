""" Client to test the USBIP server code base against """
#pylint: disable=C0326,R0205
import copy
import socket
import traceback
from virtusb import packets

class VirtualDriver(object): #pylint: disable=too-few-public-methods
    """ Driver base class """
    def __init__(self, client, port):
        self.client = client
        self.port = port

class UsbIpClient(object):
    """ Fake USBIP client that has the same command set as the Linux usbip command """
    def __init__(self):
        self._server  = None
        self._socket  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ports   = []
        self._seq_num = 1
        self._drivers = {}

    def add_driver(self, vendor_id, product_id, cls):
        """ Add a device driver the client can use to handle known devices """
        key = (vendor_id << 16) + product_id
        self._drivers[key] = cls

    def _connected(self):
        """ Test if the client socket is connected to the server """
        return self._server is not None

    def _connect(self, ip='127.0.0.1', port=3240): #pylint: disable=invalid-name
        """ Connect the socket to the server """
        if self._connected():
            raise RuntimeError('Client socket already connected')
        self._server = (ip, port)
        self._socket.connect(self._server)

    def _close(self):
        """ Close the socket """
        if not self._connected():
            raise RuntimeError('Client socket has no connection to close')
        self._socket.close()
        self._server = None

    def _sendall(self, data):
        """ Send data. Keeps track of the sequence number """
        if not self._connected():
            raise RuntimeError('Client socket has no connection to send to')
        self._socket.sendall(data)
        self._seq_num += 1

    def _recv(self, size):
        """ Receive data """
        if not self._connected():
            raise RuntimeError('Client socket has no connection to read from')
        return self._socket.recv(size)

    def _list_handler(self):
        """ Handle getting the list of remote devices """
        # Request has no parameters, so a blank request will do
        request = packets.OpReqDevlist()
        data = request.pack()
        self._sendall(data)

        # The response is dynamically sized, with no upper bound, so we need to
        #  get the data in chunks to figure out how much total data to fetch
        #  before building the corresponding packet
        raw = self._recv(12)
        assert raw is not None
        response = packets.OpRepDevlist.from_raw(raw, partial=True)
        assert response['version'] == request['version']
        assert response['command'] == packets.OP_REP_DEVLIST
        assert response['status']  == 0

        devices = []
        for _ in range(response['device_count']):
            raw = self._recv(312)
            assert raw is not None
            device = packets.OpRepDevlist.Device.from_raw(raw, partial=True)
            ifaces = []
            for _ in range(device['iface_count']):
                raw = self._recv(4)
                iface = packets.OpRepDevlist.Device.Iface.from_raw(raw)
                ifaces.append(iface)
            device['ifaces'] = ifaces
            devices.append(device)
        response['devices'] = devices

        return response

    def _import_handler(self, bus_id):
        """ Handle importing USB devices """
        request = packets.OpReqImport(bus_id=bus_id)
        data = request.pack()
        self._sendall(data)

        raw = self._recv(320)
        response = packets.OpRepImport.from_raw(raw)
        assert response['status'] == 0

        return response

    def _submit_handler( #pylint: disable=too-many-arguments
            self, port,
            endpoint=0, direction=0, transfer_flags=0x00000000,
            buffer_len=0, request_type=0x00, request=0x00,
            value=0x0000, data=None):
        """ Handle submitting commands to an imported USB device """
        # send the request based off the input arguments
        request = packets.UsbIpCmdSubmit(
            seq_num        = self._seq_num,
            dev_id         = self._ports[port]['device_id'],
            direction      = direction,
            endpoint       = endpoint,
            transfer_flags = transfer_flags,
            buffer_len     = buffer_len,
            setup = packets.UrbSetup(
                bmRequestType = request_type,
                bRequest      = request,
                wValue        = value,
                wIndex        = 0x0000,
                wLength       = buffer_len
                ))
        raw = request.pack()
        if data is not None:
            raw += data
        self._sendall(raw)

        # Fetch the response packet
        raw = self._recv(48)
        response = packets.UsbIpRetSubmit.from_raw(raw)
        assert response['status']      == 0
        assert response['error_count'] == 0

        # Fetch optional response data
        response_data = None
        if direction == 1:
            size = response['actual_len']
            if size > 0:
                response_data = self._recv(size)
                assert len(response_data) <= buffer_len

        return response, response_data

    def list(self):
        """ List all available remote devices """
        self._connect()
        try:
            response = self._list_handler()
        finally:
            self._close()
        return response['devices']

    def attach(self, bus_id):
        """ Attach a device to a new port on the client """
        self._connect()
        try:
            # Make import response
            response = self._import_handler(bus_id)
            new_port = len(self._ports)
            device_id = (response['bus_no'] << 16) + response['device_no']
            self._ports.append({'port': new_port, 'device_id': device_id})

            # The real USBIP requests descriptors after attaching. The requests
            #  are made twice, with different buffer lengths. The first request
            #  is used to determine the actual size to request, and than the
            #  buffer length is changed to make the request again
            kwargs = dict(
                port           = new_port,
                endpoint       = 0,
                direction      = 0x0001,
                transfer_flags = 0x00000200,
                request_type   = 0x80,
                request        = 0x06)
            kwargs['value']      = 0x0100
            kwargs['buffer_len'] = 64
            self._submit_handler(**kwargs)
            kwargs['buffer_len'] = 18
            response, data       = self._submit_handler(**kwargs)
            dev_desc             = packets.DeviceDescriptor.from_raw(data)
            self._ports[new_port]['device_descriptor'] = dev_desc

            kwargs['value']      = 0x0200
            kwargs['buffer_len'] = 9
            response, data       = self._submit_handler(**kwargs)
            conf_desc = packets.ConfigurationDescriptor.from_raw(data, partial=True)
            kwargs['buffer_len'] = conf_desc['wTotalLength']
            response, data       = self._submit_handler(**kwargs)
            conf_desc_full       = packets.ConfigurationDescriptor.from_raw(data)
            self._ports[new_port]['config_descriptor'] = conf_desc_full

            # Create a driver instance for this device on it's attached port
            driver_id = (dev_desc['idVendor'] << 16) + dev_desc['idProduct']
            try:
                driver = self._drivers[driver_id]
            except KeyError:
                driver = VirtualDriver
            self._ports[new_port]['driver'] = driver(self, new_port)

            # Set the configuration
            self._submit_handler(
                port           = new_port,
                endpoint       = 0,
                direction      = 0x0001,
                transfer_flags = 0x00000000,
                buffer_len     = 0,
                request_type   = 0,
                request        = 0x09,
                value          = conf_desc_full['bConfigurationValue'])
            return self._ports[new_port]

        # Socket is kept alive after attaching, so only close it if something
        #  goes wrong
        except Exception: #pylint: disable=broad-except
            self._close()
            raise

    def detach(self, port):
        """ Detach a port from the client """
        assert len(self._ports) >= port
        del self._ports[port]

        # Port closes if no attached devices remain
        if not self._ports:
            self._close()

    def port(self):
        """ Fetch a list of ports with attached devices """
        return copy.deepcopy(self._ports)
