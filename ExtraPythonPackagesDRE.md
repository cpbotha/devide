# Introduction #

So sometimes you'd really like to install some extra Python packages in the DRE. This is fortunately really easy with easy\_install.

# Details #

## Once-off installation of easy\_install ##

First you have to install easy\_install itself. **This only has to happen once**, and probably won't be necessary when 11.x is finally released. Do this installation as follows:

  * download ez\_setup.py from http://pypi.python.org/pypi/setuptools
  * install it with:
```
dre python /where/you/put/it/ez_setup.py
```
for example under Windows:
```
c:\Program Files\DeVIDE-RE\dre python c:\temp\ez_setup.py
```

## Installing Python packages ##

Now you can install any Python package in the DRE by using easy\_install. For example:
```
c:\Program Files\DeVIDE-RE\python\Scripts\easy_install pymongo
```
will find pymongo on the Python package repository and install it in the DRE.