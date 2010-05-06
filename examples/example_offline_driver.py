# example driver script for offline / command-line processing with DeVIDE

# the following variables are magically set in this script:
# interface - instance of ScriptInterface, with the following calls:
#   meta_modules = load_and_realise_network()
#   execute_network(self, meta_modules)
#   clear_network(self)
#   instance = get_module_instance(self, module_name)
#   config = get_module_config(self, module_name)
#   set_module_config(self, module_name, config)
# See devide/interfaces/simple_api_mixin.py for details.

def main():
    print "hello from offline DeVIDE!"
    meta_modules = load_and_realise_network('/complete/path/to/dvnfile.dvn')
    
    # 1. First we are going to configure the reader module to load the file we want.
    # you can get and change the config of any module that you have named in a previous
    # DeVIDE session with right click | rename module.
    # a. get the configuration
    config = get_module_config('named_reader')
    # b. change the configuration
    config._filename = 'some_data_file.vti'
    # c. set he configuration back into the module
    set_module_config('named_reader', config)

    # after having setup more modules (for example the module writing the output of your
    # network), run the network.
    execute_network()

    # you could now repeat the process for other filenames or even other
    # networks.  You can also make use of any Python niceties!

main()

