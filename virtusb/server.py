""" USBIP TCP Server """
#pylint: disable=C0326

import SocketServer
import signal
from virtusb import packets

# Get a logger
from virtusb import log
LOGGER = log.get_logger()

class UsbIpServer(object):
    """ USBIP TCP Server """
    def __init__(self, controller):
        self.controller = controller
        self.attached   = []
        self.server     = None
        self.thread     = None

    def interrupt_handler(self, *args):
        """ Handle interrupt signals """
        LOGGER.warning('Interrupt signal received (Ctrl+C)')
        self.stop()

    def start(self, bind_ip='0.0.0.0', bind_port=3240):
        """ Start the server """
        LOGGER.info('Starting USBIP server on {}:{}'.format(bind_ip, bind_port))

        # Configure the socket server
        SocketServer.ThreadingTCPServer.allow_reuse_address = True
        self.server            = SocketServer.ThreadingTCPServer((bind_ip, bind_port), UsbIpHandler)
        self.server.controller = self.controller
        self.server.keep_alive = True

        # Start the server in it's own thread
        signal.signal(signal.SIGINT, self.interrupt_handler)
        self.server.serve_forever()

    def stop(self):
        """ Stop the server """
        LOGGER.info('Stopping the USBIP server')

        # Detach all devices
        self.detach_all()

        # Shutdown the server
        self.server.keep_alive = False
        self.server.shutdown()
        self.server.server_close()

        # Wait for the thread to finish
        self.thread.join()
        self.thread = None

    def attach(self, device_id):
        """ Attach a single device with USBIP by device id """
        LOGGER.debug('Attaching device {}'.format(device_id))

    def detach(self, device_id):
        """ Detach a single device with USBIP by device id """
        LOGGER.debug('Detaching device {}'.format(device_id))

    def attach_all(self):
        """ Attach all devices with USBIP """
        pass

    def detach_all(self):
        """ Detach all devices with USBIP """
        pass

class UsbIpHandler(SocketServer.BaseRequestHandler):
    """ Request handler for the USBIP server """
    def handle(self):
        """ Handle packets """
        pass

    def pkt_op_req_devlist(self, packet):
        """ Handle OP_REQ_DEVLIST packets """
        LOGGER.debug('Received OP_REQ_DEVLIST')

    def pkt_op_req_import(self, packet):
        """ Handle OP_REQ_IMPORT packets """
        LOGGER.debug('Received OP_REQ_IMPORT')

    def pkt_usbip_cmd_submit(self, packet):
        """ Handle USBIP_CMD_SUBMIT packets """
        LOGGER.debug('Received USBIP_CMD_SUBMIT')

    def pkt_usbip_cmd_unlink(self, packet):
        """ Handle USBIP_CMD_UNLINK packets """
        LOGGER.debug('Received USBIP_CMD_UNLINK')
