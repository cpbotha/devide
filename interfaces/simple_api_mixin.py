# simple api mixin to be used by RPC and command line interfaces
# of DeVIDE that require simple methods for speaking to a running
# instance

class SimpleAPIMixin:

    def __init__(self, devide_app):
        self.devide_app = devide_app

    def close(self):
        del self.devide_app

    def load_and_realise_network(self, filename):
        """Load and instantiate a network from a given dvn filename.
        
        e.g. module_dict, conn = load_and_realise_network('test.dvn')
        
        @param filename: name of .dvn network file.
    
        @returns: dictionary mapping from serialised instance name to
        meta_module.  dict.values() returns the the list of MetaModule
        instances in the instantiated network.  Also list of connections.
        """

        ln = self.devide_app.network_manager.load_network
        pms_dict, connection_list, glyph_pos_dict = ln(filename)
        rn = self.devide_app.network_manager.realise_network
        new_modules_dict, new_connections = rn(pms_dict, connection_list)

        mm = self.devide_app.get_module_manager()
        new_modules_dict2 = {}
        for k in new_modules_dict:
            instance = new_modules_dict[k]
            meta_module = mm.get_meta_module(instance)
            new_modules_dict2[k] = meta_module
        
        return new_modules_dict2, new_connections

    def execute_network(self, meta_modules):
        """Given a list of MetaModule instances, execute the network
        represented by those modules.
        
        List of metamodules can be found for example in the values() of the
        
        """
        self.devide_app.network_manager.execute_network(meta_modules)

    def clear_network(self):
        # graphEditor.clearAllGlyphsFromCanvas() - delete network func
        # has to be moved to NetworkManager
        self.devide_app.network_manager.clear_network()

    def get_module_instance(self, module_name):
        mm = self.devide_app.get_module_manager()
        return mm.get_instance(module_name)

    def get_module_config(self, module_name):
        mi = self.get_module_instance(module_name)
        return mi.get_config()

    def set_module_config(self, module_name, config):
        mi = self.get_module_instance(module_name)
        mi.set_config(config)
