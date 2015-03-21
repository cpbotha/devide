By writing a simple Python driver script, you can run DeVIDE in offline / batch-processing / command-line mode to process a large number of datasets.  In this mode, no graphics display is required, all output is text-based.

See this example of a driver script to get started: http://code.google.com/p/devide/source/browse/trunk/devide/examples/example_offline_driver.py

Once your script is done, invoke it as follows:
```
/data/scratch/jwd/inst/dre devide --interface script --script example_offline_driver.py
```

You can also pass parameters to the script as follows:

```
/data/scratch/jwd/inst/dre devide --interface script --script example_offline_driver.py --script-params "0.5,some_filename,0.35"
```

These will be made available in your script as variable name "script\_params".

# Performance #

As there is some overhead involved with each startup of DeVIDE, it makes sense to have your Python driver script do as much as possible of the looping and iteration through your datasets.