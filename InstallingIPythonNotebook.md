IPython 0.12 has an absolutely super fantastic new feature called the [Notebook](http://ipython.org/ipython-doc/dev/interactive/htmlnotebook.html). See this screenshot:

![http://wiki.devide.googlecode.com/hg/help_images/ipython_notebook_dre.png](http://wiki.devide.googlecode.com/hg/help_images/ipython_notebook_dre.png)

Of course you want this in your DRE right?!

Here's the recipe (for Linux):

  1. First follow the steps for upgrading your 12.2.7 installation to a development snapshot: [UpdateDeVIDE12\_2ToDEV](UpdateDeVIDE12_2ToDEV.md) -- we're primarily interested in getting the pip support fixed.
  1. Make sure that libzmq-dev is installed on your system. You'll need root for this.
  1. then:
```
dre shell
pip uninstall ipython
pip install tornado
pip install pyzmq
pip install ipython
which ipython # check that this is the DRE one
ipython --pylab inline
```
  1. Optionally, install SciPy for additional CRAZY SCIENTIFIC FUN by following these instructions: [InstallingSciPy](InstallingSciPy.md)

Whenever you need to run ipython notebook, you have to do:
```
dre shell
ipython --pylab inline
```

("dre ipython" is temporarily broken due to changes in the new ipython, hence the two line invocation)