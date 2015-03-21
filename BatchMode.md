# Introduction #

You can run DeVIDE in batch mode, for example to apply the same network to hundreds of different datasets.

In this mode, DeVIDE has NO user interface, so you can run it remotely on machines in a cluster for example.  The drawback is that you can't use any viewer modules (DICOMBrowser, slice3dVWR, etc) in your networks.

If you **do** need a graphical user interface, for example because you want to see the various viewers, or you just don't need to run your networks remotely, you can also use the CodeRunner method for batch processing.  See [BatchModeWithUI](BatchModeWithUI.md) for details.

# Preparing your network #

Make sure the network you'll want to run has names assigned to the modules that you'll want to reconfigure in batch mode, for example any data readers so that you can reconfigure the filenames that they read.  In the batch mode driver script (we'll get to that later), you'll be able to configure any module by its unique name.

# Creating the driver script #

The driver script looks something like this (let's call it offline\_driver.py):
```
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

# start the script with:
# dre devide --interface script --script example_offline_driver.py --script-params 0.0,100.0

def main():
    # script_params is everything that gets passed on the DeVIDE
    # commandline after --script-params
    # first get the two strings split by a comma
    l,u = script_params.split(',')
    # then cast to float
    LOWER = float(l)
    UPPER = float(u)
    
    print "offline_driver.py starting"

    # load the DVN that you prepared
    # load_and_realise_network returns module dictionary + connections
    mdict,conn = interface.load_and_realise_network(
        'BatchModeWithoutUI-ex.dvn')

    # parameter is the module name that you assigned in DeVIDE
    # using right-click on the module, then "Rename"
    thresh_conf = interface.get_module_config('threshold')
    # what's returned is module_instance._config (try this in the
    # devide module introspection interface by introspecting "Module
    # (self)" and then typing "dir(obj._config)"
    thresh_conf.lowerThreshold = LOWER
    thresh_conf.upperThreshold = UPPER
    # set module config back again
    interface.set_module_config('threshold', thresh_conf)

    # get, change and set writer config to change filename
    writer_conf = interface.get_module_config('vtp_wrt')
    writer_conf.filename = 'result_%s-%s.vtp' % (str(LOWER),str(UPPER))
    interface.set_module_config('vtp_wrt', writer_conf)

    # run the network
    interface.execute_network(mdict.values())
    
    print "offline_driver.py done."

main()
```

The complete working script can be found here: http://code.google.com/p/devide/source/browse/trunk/devide/examples/example_offline_driver.py and the DVN that it needs to load can be found here: http://code.google.com/p/devide/source/browse/trunk/devide/examples/BatchModeWithoutUI-ex.dvn

You can obviously do all kinds of loops and almost anything else that Python allows.

# Executing DeVIDE in batch mode #

After all this preparation, you can start DeVIDE as follows:
```
python --interface script --script your_driver.py --script-params "0.0,100.0"
```

To pass more parameters, do this:
```
python --interface script --script your_driver.py --script-params "250.0,500.0,somestring"
```