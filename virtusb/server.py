""" USBIP TCP Server """
#pylint: disable=C0326,W1202,R0205

import socket
import signal
import struct
from threading import Thread
from subprocess import Popen, PIPE
from six.moves.socketserver import ThreadingTCPServer, BaseRequestHandler
from virtusb import log, packets

LOGGER = log.get_logger()
RECV_TIMEOUT_SEC = 5

class UsbIpServer(object):
    """ USBIP TCP Server """
    def __init__(self, controller):
        self.controller = controller
        self.keep_alive = False
        self.server     = None
        self.thread     = None
        self.ports      = {}

    def interrupt_handler(self, *args): #pylint: disable=unused-argument
        """ Handle interrupt signals """
        LOGGER.warning('Interrupt signal received (Ctrl+C)')
        self.stop()

    def start(self, bind_ip='0.0.0.0', bind_port=3240):
        """ Start the server """
        LOGGER.info('Starting USBIP server on {}:{}'.format(bind_ip, bind_port))

        # Configure the socket server
        ThreadingTCPServer.allow_reuse_address = True
        self.server = ThreadingTCPServer((bind_ip, bind_port), UsbIpHandler)
        self.server.controller = self.controller
        self.server.keep_alive = True

        # Start the server in it's own thread
        signal.signal(signal.SIGINT, self.interrupt_handler)
        self.thread = Thread(target=self.server.serve_forever)
        self.thread.start()

    def stop(self):
        """ Stop the server """
        LOGGER.info('Stopping the USBIP server')

        # Detach all devices
        self.detach_all()

        # Shutdown the server
        self.keep_alive = False
        self.server.shutdown()
        self.server.server_close()

        # Wait for the thread to finish
        self.thread.join()
        self.thread = None

    def attach(self, device_id):
        """ Attach a single device with USBIP by device id """
        LOGGER.debug('Attaching device {}'.format(device_id))

        # Validate the device id
        split = device_id.split('-')
        assert len(split) == 2
        assert int(split[0]) == self.controller.bus_no
        assert int(split[1]) <= len(self.controller.devices)

        # Attach the device. Failing to attach a valid device should be treated
        #  as a fatal error since the end user may have to manually configure
        #  their environment back to a clean state
        args = ['usbip', 'attach', '-r', '127.0.0.1', '-b', device_id]
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        code = process.returncode
        if code != 0:
            msg = 'Error while attaching device {} ({})'.format(device_id, code)
            msg += '\n{}\n{}'.format(out, err)
            LOGGER.fatal(msg)
            raise RuntimeError(msg)
        new_port = len(self.ports)
        self.ports[new_port] = device_id

    def detach(self, port): #pylint: disable=no-self-use
        """ Detach a single device with USBIP by port number """
        LOGGER.debug('Detaching port {}'.format(port))

        # Detach the port. There are normal reasons why a device may fail to
        #  detach, but for safety, warn the user when it occurs.
        args = ['usbip', 'datach', '-p', port]
        process = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        code = process.returncode
        if code != 0:
            msg = 'Error while detaching port {} ({})'.format(port, code)
            msg += '\n{}\n{}'.format(out, err)
            LOGGER.warning(msg)

    def attach_all(self):
        """ Attach all devices with USBIP """
        for idx in range(len(self.controller.devices)):
            device_id = '{}-{}'.format(self.controller.bus_no, idx)
            self.attach(device_id)

    def detach_all(self):
        """ Detach all devices with USBIP """
        for port,_ in self.ports:
            self.detach(port)

class UsbIpHandler(BaseRequestHandler):
    """ Request handler for the USBIP server """
    def handle(self):
        """ Handle packets """
        # Keep the connection open for as long as the client is connected
        self.request.settimeout(RECV_TIMEOUT_SEC)
        while self.server.keep_alive:
            try:
                raw = self.request.recv(4)
            # A timeout just means there are no pending packets. restart the
            #  loop, allowing the keep alive check to take place again
            except socket.timeout:
                continue
            # No data on the line indicates the client has disconnected
            if not raw:
                break

            # OP_REQ packets contain a non-zero value in the first 2 bytes,
            #  whereas USBIP_CMD packets are always null bytes.
            header = struct.unpack('>HH', raw)
            op_req = (header[0] > 0)
            command = header[1]
            if op_req and command == packets.OP_REQ_DEVLIST:
                raw += self.request.recv(4)
                packet = packets.OpReqDevlist.from_raw(raw)
                response, data = self.pkt_op_req_devlist(packet)
            elif op_req and command == packets.OP_REQ_IMPORT:
                raw += self.request.recv(36)
                packet = packets.OpReqImport.from_raw(raw)
                response, data = self.pkt_op_req_import(packet)
            elif not op_req and command == packets.USBIP_CMD_SUBMIT:
                raw += self.request.recv(44)
                packet = packets.UsbIpCmdSubmit.from_raw(raw)
                response, data = self.pkt_usbip_cmd_submit(packet)
            elif not op_req and command == packets.USBIP_CMD_UNLINK:
                raw += self.request.recv(4)
                packet = packets.UsbIpCmdUnlink.from_raw(raw)
                response, data = self.pkt_usbip_cmd_unlink(packet)

            # Unknown packet/data received, state is unrecoverable
            else:
                msg = 'Unknown packet received'
                LOGGER.error(msg)
                raise RuntimeError(msg)

            # Send the response packet with optional return data
            out_raw = response.pack()
            if data:
                out_raw += data
            self.request.sendall(out_raw)
            LOGGER.debug('Sent response ({}B)'.format(len(raw)))

    def pkt_op_req_devlist(self, packet):
        """ Handle OP_REQ_DEVLIST packets """
        LOGGER.debug('Received OP_REQ_DEVLIST')

        # Prepare an empty response packet
        response = packets.OpRepDevlist(version=packet['version'])

        # Create a list of devices in the controller, including their interfaces
        controller = self.server.controller
        dev_list = []
        for idx, device in enumerate(controller.devices):
            iface_list = []
            for iface in device.active_config.interfaces:
                iface_list.append(packets.OpRepDevlist.Device.Iface(
                    iface_class    = iface.bInterfaceClass,
                    iface_subclass = iface.bInterfaceSubClass,
                    iface_proto    = iface.bInterfaceProtocol))
            device_no = idx + 1
            bus_no = controller.bus_no
            bus_id = '{}-{}'.format(bus_no, device_no)
            dev_list.append(packets.OpRepDevlist.Device(
                path            = controller.path + bus_id,
                bus_id          = bus_id,
                bus_num         = bus_no,
                device_num      = device_no,
                speed           = device.speed,
                vendor_id       = device.descriptor.idVendor,
                product_id      = device.descriptor.idProduct,
                device_version  = device.descriptor.bcdDevice,
                device_class    = device.descriptor.bDeviceClass,
                device_subclass = device.descriptor.bDeviceSubClass,
                device_protocol = device.descriptor.bDeviceProtocol,
                config_count    = device.descriptor.bNumConfigurations,
                config_value    = device.active_config.bConfigurationValue,
                iface_count     = device.active_config.bNumInterfaces,
                ifaces          = iface_list))

        # Add the device list to the response
        response['devices'] = dev_list
        return response, None

    def pkt_op_req_import(self, packet):
        """ Handle OP_REQ_IMPORT packets """
        LOGGER.debug('Received OP_REQ_IMPORT')

        # Prepare an empty response packet
        response = packets.OpRepImport(version=packet['version'])

        # Fetch the requested device on the controller to import
        bus_id = packet['bus_id']
        controller = self.server.controller
        try:
            parts = bus_id.split('-')
            bus_no = int(parts[0])
            if bus_no != controller.bus_no:
                raise ValueError
            device_no = int(parts[1])
            device = controller.get_device(device_no)

        # Invalid bus ID's are non fatal errors, respond with a bad status
        except (ValueError, IndexError):
            LOGGER.error('Requested to import invalid bus_id ({})'.format(bus_id))
            response['status'] = 1
            return response, None

        # Request the device to begin it's simulation
        device.start()

        # Fill out response with the devices data
        response['full_path']       = controller.path + bus_id
        response['bus_id']          = bus_id
        response['bus_no']          = bus_no
        response['device_no']       = device_no
        response['device_speed']    = device.speed
        response['vendor_id']       = device.descriptor.idVendor
        response['product_id']      = device.descriptor.idProduct
        response['device_version']  = device.descriptor.bcdDevice
        response['device_class']    = device.descriptor.bDeviceClass
        response['device_subclass'] = device.descriptor.bDeviceSubClass
        response['device_protocol'] = device.descriptor.bDeviceProtocol
        response['config_count']    = device.descriptor.bNumConfigurations
        response['config_value']    = device.active_config.bConfigurationValue
        response['iface_count']     = device.active_config.bNumInterfaces
        return response, None

    def pkt_usbip_cmd_submit(self, packet):
        """ Handle USBIP_CMD_SUBMIT packets """
        LOGGER.debug('Received USBIP_CMD_SUBMIT')

        # Prepare an empty response packet
        response = packets.UsbIpRetSubmit(
            seq_num=packet['seq_num'], dev_id=packet['dev_id'])

        # Fetch any additional data that came with the request
        buffer_len = packet['buffer_len']
        if packet['direction'] == 1 and buffer_len > 0:
            in_data = self.request.recv(buffer_len)
        else:
            in_data = None

        # Send the request to the controller to handle
        try:
            out_data = self.server.controller.handle(packet, in_data)
        except RuntimeError as error:
            LOGGER.error('Error handling USB_CMD_SUBMIT: {}'.format(str(error)))
            response['status'] = 1
            return response, None

        # Send the response with optional data
        if out_data is not None:
            response['actual_len'] = len(out_data)
        return response, out_data

    def pkt_usbip_cmd_unlink(self, packet):
        """ Handle USBIP_CMD_UNLINK packets """
        LOGGER.debug('Received USBIP_CMD_UNLINK')

        # Prepare an empty response packet
        dev_id = packet['dev_id']
        response = packets.UsbIpRetUnlink(
            seq_num=packet['seq_num'], dev_id=dev_id)

        # Request the device to stop it's simulation
        device = self.server.controller.get_device(dev_id)
        device.stop()

        return response
