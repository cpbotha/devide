# simple api mixin to be used by RPC and command line interfaces
# of DeVIDE that require simple methods for speaking to a running
# instance

class SimpleAPIMixin:

    def __init__(self, devide_app):
        self.devide_app = devide_app

    def close(self):
        del self.devide_app

    def load_network(self, filename):
        pass

    def execute_network(self):
        pass

    def clear_network(self):
        pass

    def get_module_instance(self, module_name):
        pass

