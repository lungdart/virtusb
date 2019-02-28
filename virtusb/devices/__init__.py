import copy

class VirtualDevice(object):
    def __init__(self, descriptor):
        self.descriptor = copy.deepcopy(descriptor)
        self.speed = 2 # Hard coded high-speed device

        # Set the default config and interfaces as active
        self.set_config()
        self.set_interface()

    @property
    def current_config(self):
        """ Fetch the current config """
        return self.descriptor.current_config

    @property
    def current_interface(self):
        """ Fetch the current interface """
        return self.descriptor.current_interface

    def set_config(self, value=0):
        """ Set the current config """
        self.descriptor.set_config(value)

    def set_interface(self, value=0):
        """ Set the current interface """
        self.descriptor.set_interface(value)
