# $Id$

"""Mixins that are useful for classes using vtk_kit.

@author: Charl P. Botha <http://cpbotha.net/>
"""

from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj
from external.vtkPipeline.vtkMethodParser import VtkMethodParser
from module_base import ModuleBase
from moduleMixins import introspectModuleMixin # temporary
import moduleUtils # temporary, most of this should be in utils.
import re
import utils

#########################################################################
class PickleVTKObjectsModuleMixin(object):
    """This mixin will pickle the state of all vtk objects whose binding
    attribute names have been added to self._vtkObjects, e.g. if you have
    a self._imageMath, '_imageMath' should be in the list.

    Your module has to derive from module_base as well so that it has a
    self._config!

    Remember to call the __init__ of this class with the list of attribute
    strings representing vtk objects that you want pickled.  All the objects
    have to exist and be initially configured by then.

    Remember to call close() when your child class close()s.
    """

    def __init__(self, vtkObjectNames):
        # you have to add the NAMES of the objects that you want pickled
        # to this list.
        self._vtkObjectNames = vtkObjectNames

        self.statePattern = re.compile ("To[A-Z0-9]")

        # make sure that the state of the vtkObjectNames objects is
        # encapsulated in the initial _config
        self.logic_to_config()

    def close(self):
        # make sure we get rid of these bindings as well
        del self._vtkObjectNames

    def logic_to_config(self):
        parser = VtkMethodParser()


        for vtkObjName in self._vtkObjectNames:

            # pickled data: a list with toggle_methods, state_methods and
            # get_set_methods as returned by the vtkMethodParser.  Each of
            # these is a list of tuples with the name of the method (as
            # returned by the vtkMethodParser) and the value; in the case
            # of the stateMethods, we use the whole stateGroup instead of
            # just a single name
            vtkObjPD = [[], [], []]

            vtkObj = getattr(self, vtkObjName)
            
            parser.parse_methods(vtkObj)
            # parser now has toggle_methods(), state_methods() and
            # get_set_methods();
            # toggle_methods: ['BlaatOn', 'AbortExecuteOn']
            # state_methods: [['SetBlaatToOne', 'SetBlaatToTwo'],
            #                 ['SetMaatToThree', 'SetMaatToFive']]
            # get_set_methods: ['NumberOfThreads', 'Progress']


            for method in parser.toggle_methods():
                # if you query ReleaseDataFlag on a filter with 0 outputs,
                # VTK yields an error
                if vtkObj.GetNumberOfOutputPorts() == 0 and \
                   method == 'ReleaseDataFlagOn':
                    continue

                # we need to snip the 'On' off
                val = eval("vtkObj.Get%s()" % (method[:-2],))
                vtkObjPD[0].append((method, val))

            for stateGroup in parser.state_methods():
                # we search up to the To
                end = self.statePattern.search (stateGroup[0]).start ()
                # so we turn SetBlaatToOne to GetBlaat
                get_m = 'G'+stateGroup[0][1:end]
                # we're going to have to be more clever when we set_config...
                # use a similar trick to get_state in vtkMethodParser
                val = eval('vtkObj.%s()' % (get_m,))
                vtkObjPD[1].append((stateGroup, val))

            for method in parser.get_set_methods():
                val = eval('vtkObj.Get%s()' % (method,))
                vtkObjPD[2].append((method, val))

            # finally set the pickle data in the correct position
            setattr(self._config, vtkObjName, vtkObjPD)

    def config_to_logic(self):
        # go through at least the attributes in self._vtkObjectNames

        for vtkObjName in self._vtkObjectNames:
            try:
                vtkObjPD = getattr(self._config, vtkObjName)
                vtkObj = getattr(self, vtkObjName)
            except AttributeError:
                print "PickleVTKObjectsModuleMixin: %s not available " \
                      "in self._config OR in self.  Skipping." % (vtkObjName,)

            else:
                
                for method, val in vtkObjPD[0]:
                    if val:
                        eval('vtkObj.%s()' % (method,))
                    else:
                        # snip off the On
                        eval('vtkObj.%sOff()' % (method[:-2],))

                for stateGroup, val in vtkObjPD[1]:
                    # keep on calling the methods in stategroup until
                    # the getter returns a value == val.
                    end = self.statePattern.search(stateGroup[0]).start()
                    getMethod = 'G'+stateGroup[0][1:end]

                    for i in range(len(stateGroup)):
                        m = stateGroup[i]
                        eval('vtkObj.%s()' % (m,))
                        tempVal = eval('vtkObj.%s()' % (getMethod,))
                        if tempVal == val:
                            # success! break out of the for loop
                            break

                for method, val in vtkObjPD[2]:
                    eval('vtkObj.Set%s(val)' % (method,))

#########################################################################    
# note that the pickle mixin comes first, as its config_to_logic/logic_to_config
# should be chosen over that of noConfig
class SimpleVTKClassModuleBase(PickleVTKObjectsModuleMixin,
                               introspectModuleMixin,
                               ModuleBase):
    """Use this base to make a DeVIDE module that wraps a single VTK
    object.  The state of the VTK object will be saved when the network
    is.
    
    You only have to override the __init__ method and call the __init__
    of this class with the desired parameters.

    The __doc__ string of your module class will be replaced with the
    __doc__ string of the encapsulated VTK class (and will thus be
    shown if the user requests module help).  If you don't want this,
    call the ctor with replaceDoc=False.

    inputFunctions is a list of the complete methods that have to be called
    on the encapsulated VTK class, e.g. ['SetInput1(inputStream)',
    'SetInput1(inputStream)'].  The same goes for outputFunctions, except that
    there's no inputStream involved.  Use None in both cases if you want
    the default to be used (SetInput(), GetOutput()).
    """
    
    def __init__(self, module_manager, vtkObjectBinding, progressText,
                 inputDescriptions, outputDescriptions,
                 replaceDoc=True,
                 inputFunctions=None, outputFunctions=None):

        self._viewFrame = None
        self._configVtkObj = None

        # first these two mixins
        ModuleBase.__init__(self, module_manager)

        self._theFilter = vtkObjectBinding
        
        if replaceDoc:
            myMessage = "<em>"\
                        "This is a special DeVIDE module that very simply " \
                        "wraps a single VTK class.  In general, the " \
                        "complete state of the class will be saved along " \
                        "with the rest of the network.  The documentation " \
                        "below is that of the wrapped VTK class:</em>"
            
            self.__doc__ = '%s\n\n%s' % (myMessage, self._theFilter.__doc__)
        
        # now that we have the object, init the pickle mixin so
        # that the state of this object will be saved
        PickleVTKObjectsModuleMixin.__init__(self, ['_theFilter'])        

        # make progress hooks for the object
        moduleUtils.setupVTKObjectProgress(self, self._theFilter,
                                           progressText)        

        self._inputDescriptions = inputDescriptions
        self._outputDescriptions = outputDescriptions

        self._inputFunctions = inputFunctions
        self._outputFunctions = outputFunctions

    def _createViewFrame(self):
        parentWindow = self._module_manager.getModuleViewParentWindow()

        import resources.python.defaultModuleViewFrame
        reload(resources.python.defaultModuleViewFrame)

        dMVF = resources.python.defaultModuleViewFrame.defaultModuleViewFrame
        viewFrame = moduleUtils.instantiateModuleViewFrame(
            self, self._module_manager, dMVF)

        # ConfigVtkObj parent not important, we're passing frame + panel
        # this should populate the sizer with a new sizer7
        # params: noParent, noRenwin, vtk_obj, frame, panel
        self._configVtkObj = ConfigVtkObj(None, None,
                                          self._theFilter,
                                          viewFrame, viewFrame.viewFramePanel)

        moduleUtils.createStandardObjectAndPipelineIntrospection(
            self, viewFrame, viewFrame.viewFramePanel,
            {'Module (self)' : self}, None)

        # we don't want the Execute button to be default... else stuff gets
        # executed with every enter in the command window (at least in Doze)
        moduleUtils.createECASButtons(self, viewFrame,
                                      viewFrame.viewFramePanel,
                                      False)
            
        self._viewFrame = viewFrame
        return viewFrame

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)
        
        PickleVTKObjectsModuleMixin.close(self)
        introspectModuleMixin.close(self)

        if self._viewFrame is not None:
            self._configVtkObj.close()
            self._viewFrame.Destroy()
            
        ModuleBase.close(self)
        # get rid of our binding to the vtkObject
        del self._theFilter

    def get_output_descriptions(self):
        return self._outputDescriptions

    def get_output(self, idx):
        # this will only every be invoked if your get_output_descriptions has
        # 1 or more elements
        if self._outputFunctions:
            return eval('self._theFilter.%s' % (self._outputFunctions[idx],))
        else:
            return self._theFilter.GetOutput()

    def get_input_descriptions(self):
        return self._inputDescriptions

    def set_input(self, idx, inputStream):
        # this will only be called for a certain idx if you've specified that
        # many elements in your get_input_descriptions

        if self._inputFunctions:
            exec('self._theFilter.%s' %
                 (self._inputFunctions[idx]))

        else:
            if idx == 0:
                self._theFilter.SetInput(inputStream)
            else:
                self._theFilter.SetInput(idx, inputStream)

    def execute_module(self):
        # it could be a writer, in that case, call the Write method.
        if hasattr(self._theFilter, 'Write') and \
           callable(self._theFilter.Write):
            self._theFilter.Write()
            
        else:
            self._theFilter.Update()

    def streaming_execute_module(self):
        """All VTK classes should be streamable.
        """
        # it could be a writer, in that case, call the Write method.
        if hasattr(self._theFilter, 'Write') and \
           callable(self._theFilter.Write):
            self._theFilter.Write()
            
        else:
            self._theFilter.Update()

 
    def view(self):
        if self._viewFrame is None:
            # we have an initial config populated with stuff and in sync
            # with theFilter.  The viewFrame will also be in sync with the
            # filter
            self._viewFrame = self._createViewFrame()
        
        self._viewFrame.Show(True)
        self._viewFrame.Raise()

    def config_to_view(self):
        # the pickleVTKObjectsModuleMixin does logic <-> config
        # so when the user clicks "sync", logic_to_config is called
        # which transfers picklable state from the LOGIC to the CONFIG
        # then we do double the work and call update_gui, which transfers
        # the same state from the LOGIC straight up to the VIEW
        self._configVtkObj.update_gui()

    def view_to_config(self):
        # same thing here: user clicks "apply", view_to_config is called which
        # zaps UI changes straight to the LOGIC.  Then we have to call
        # logic_to_config explicitly which brings the info back up to the
        # config... i.e. view -> logic -> config
        # after that, config_to_logic is called which transfers all state AGAIN
        # from the config to the logic
        self._configVtkObj.apply_changes()
        self.logic_to_config()


#########################################################################
