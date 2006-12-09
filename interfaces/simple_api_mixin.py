# simple api mixin to be used by RPC and command line interfaces
# of DeVIDE that require simple methods for speaking to a running
# instance

class SimpleAPIMixin:

    def __init__(self, devide_app):
        self.devide_app = devide_app

    def close(self):
        del self.devide_app

    def load_and_realise_network(self, filename):
        ln = self.devide_app.network_manager.load_network
        pms_dict, connection_list, glyph_pos_dict = ln(filename)
        rn = self.devide_app.network_manager.realise_network
        new_modules_dict, new_connections = rn(pms_dict, connection_list)
        return new_modules_dict, new_connections

    def execute_network(self, meta_modules):
        self.devide_app.network_manager.execute_network(meta_modules)

    def clear_network(self):
        # graphEditor.clearAllGlyphsFromCanvas() - delete network func
        # has to be moved to NetworkManager
        pass

    def get_module_instance(self, module_name):
        mm = self.devide_app.get_module_manager()
        mm.get_instance(module_name)

    def get_module_config(self, module_name):
        mi = self.get_instance(module_name)
        return mi.getConfig()

    def set_module_config(self, module_name, config):
        mi = self.get_instance(module_name)
        mi.setConfig(config)
