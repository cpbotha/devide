# Introduction #

You can run DeVIDE in batch mode also with a graphical user interface, by using a CodeRunner in a live session, for example to apply the same network to hundreds of different datasets.

This is different from the normal BatchMode, in which no graphical user interface is available.

# Details #

Start up DeVIDE normally, and load or create the network that you want to execute in batch mode.  Then, create a CodeRunner and adapt the following example in the **Scratch** tab (very very important):
```
def main():
    print "CodeRunner batch mode starting"

    # we're going to need the module_manager quite often for changing
    # module configuration and for running the network.
    mm = obj.module_manager

    # parameter is the module name that you assigned
    # what's returned is module_instance
    thresh_mod = mm.get_instance('threshold')
    # then get the config from the module
    thresh_conf = thresh_mod.get_config()
    # change the parameters you need
    thresh_conf.lowerThreshold = 0.0
    thresh_conf.upperThreshold = 100.0
    # set module config again
    thresh_mod.set_config(thresh_conf)

    # get, change and set writer config to change filename
    writer_mod = mm.get_instance('vtp_wrt')
    writer_conf = writer_mod.get_config()
    # this will write result.vtp to your current working directory
    # change this to the full path if you want it somewhere else
    writer_conf.filename = 'result.vtp'
    writer_mod.set_config(writer_conf)

    # run the network
    mm.execute_network()

    # I could put the above code in a loop, to use the same network
    # to process multiple datasets.
    
    print "CodeRunner batch mode example done."

main()
```

In the scratch tab, select File | Run current edit from the menubar to start your batch processing script.

You can also download a fully working DVN example, including the CodeRunner above, by clicking here: http://code.google.com/p/devide/source/browse/trunk/devide/examples/BatchModeWithUI-ex.dvn