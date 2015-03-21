# Introduction #
With the CodeRunner, arbitrary snippets of Python code, using any of the libraries shipping with DeVIDE, can be inserted into a functional network.  This is a pretty powerful concept that enables **very** rapid prototyping of new ideas or quick implementation of processing solutions.

# An example #
We'll illustrate with an example.  First build up this small network:

![http://devide.googlecode.com/svn/wiki/help_images/coderunner_ex_dvn.png](http://devide.googlecode.com/svn/wiki/help_images/coderunner_ex_dvn.png)

Double click on the CodeRunner, causing its View to appear.  The View's top-half consists of an editor component with three tabs: Scratch, Setup and Execute.  Paste the block of code below into the Setup tab:

```
# this block goes into the "Setup" tab of the CodeRunner
import vtk
fe = vtk.vtkFeatureEdges()
tf = vtk.vtkTubeFilter()
tf.SetRadius(0.01)
tf.SetNumberOfSides(16)
tf.SetInputConnection(fe.GetOutputPort())
```

... and the following block into the "Execute" tab:

```
# this block goes into the "Execute" tab of the CodeRunner
fe.SetInput(obj.inputs[0])
tf.Update()
obj.outputs[0] = tf.GetOutput()
```

Now click on the "Execute" button at the bottom of the CodeRunner View.  In your [slice3dVWR](HelpSlice3dVWR.md), you should see something looking more or less like the figure below:

![http://devide.googlecode.com/svn/wiki/help_images/coderunner_ex_viewer.png](http://devide.googlecode.com/svn/wiki/help_images/coderunner_ex_viewer.png)

Pretty slick eh?

# Working with Scratch, Setup and Execute tabs #

Using CodeRunner modules, you can insert arbitrary code segments into your DeVIDE networks.  The "Scratch" tab is for experimentation, the "Setup" tab code runs ONCE for any changes that you make (you should use this for building pipelines for example), and the "Execute" tab runs every time the network is executed and the CodeRunner's inputs have changed or any of the CodeRunner tabs have been modified.

Whilst editing any of the tabs, press Control-Enter to execute just that tab at that moment. Clicking on the "Execute" button at the bottom of the View requests the whole network to be run.  Liberal use of Control-Enter whilst editing will make sure that all Python objects that you have created will be instantiated.  Besides the fact that code-completion and inline documentation can then do its thing, you can easily experiment at run-time.