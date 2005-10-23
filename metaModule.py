import time

class metaModule:
    """Class used to store module-related information.

    @todo: The functionality of this class has grown with the event-driven
    conversion.  Think about what exactly its current function is and how
    we should factor it out of the moduleManager.
    @todo: at the moment, some interfaces work with a real module instance
    as well as a metaModule.  Should be consistent and use all metaModules.

    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, instance, instanceName):
        """Instance is the actual class instance and instanceName is a unique
        name that has been chosen by the user or automatically.
        """
        self.instance = instance        
        self.instanceName = instanceName

        # time when module was last invalidated (through parameter changes)
        # default is current time.  Along with 0.0 executeTime, this will
        # guarantee initial execution.
        self.modifiedTime = time.time()
        # time when module was last brought up to date
        # default to 0.0; that will guarantee an initial execution
        self.executeTime = 0.0
        # dictionary mapping from (outputIndex, consumerModule,
        # consumerInputIdx) tuples
        # to the time when data was last transferred from the encapsulated
        # instance through this path
        self.transferTimes = {}

        # this will create self.inputs, self.outputs and self.transferTimes
        self.resetInputsOutputs()

    def close(self):
        del self.instance
        del self.inputs
        del self.outputs

    def applyViewToLogic(self):
        """Transfer information from module view to its underlying logic
        (model) and all the way back up.

        The reason for the two-way transfer is so that other logic-linked
        view variables get the opportunity to update themselves.  This method
        will also take care of adapting the modifiedTime.

        At the moment this is only called by the event handlers for the
        standard ECASH interface devices.
        """

        vtc_res = self.instance.viewToConfig()
        ctl_res = self.instance.configToLogic()

        mustModify = True
        if vtc_res is None and ctl_res is None:
            # this is an old-style module, we assume that it's made changes
            mustModify = True

        elif not vtc_res and not ctl_res:
            # this means both are false, i.e. NO changes were made to
            # the config and no changes were made to the logic... this
            # means we need not modify
            mustModify = False

        else:
            # all other cases (for a new style module) means we have to mod
            mustModify = True

        if mustModify:
            # set modified time to now
            self.modify()
        
        self.instance.logicToConfig()
        self.instance.configToView()

    def syncViewWithLogic(self):
        """Transfer configuration information from underlying logic, via
        config datastructure to view.

        At the moment this is only called by the event handlers for the
        standard ECASH buttons.
        """
        
        self.instance.logicToConfig()
        self.instance.configToView()

    def findConsumerInOutputConnections(
        self, outputIdx, consumerInstance, consumerInputIdx=-1):
        """Find the given consumer module and its input index in the
        list for the given output index.
        
        @param consumerInputIdx: input index on consumer module.  If this is
        -1, the code will only check for the correct consumerInstance and
        will return the first occurrence.
        @return: index of given instance if found, -1 otherwise.
        """

        ol = self.outputs[outputIdx]

        found = False
        for i in range(len(ol)):
            ci, cii = ol[i]
            if ci == consumerInstance and \
                   (consumerInputIdx == -1 or cii == consumerInputIdx):
                found = True
                break

        #import pdb
        #pdb.set_trace()

        if found:
            return i
        else:
            return -1

    def connectInput(self, inputIdx, producerModule, producerOutputIdx):
        """Record connection on the specified inputIdx.

        This is one half of recording a complete connection: the supplier
        module should also record the connection of this consumer.

        @raise Exception: if input is already connected.
        @return: Nothing.
        """

        # check that the given input is not already connected
        if self.inputs[inputIdx] is not None:
            raise Exception, \
                  "%d'th input of module %s already connected." % \
                  (inputIdx, self.instance.__class__.__name__)

        # record the input connection
        self.inputs[inputIdx] = (producerModule, producerOutputIdx)

    def disconnectInput(self, inputIdx):
        """Record disconnection on the given input of the encapsulated
        instance.

        @return: Nothing.
        """
        
        self.inputs[inputIdx] = None

    def connectOutput(self, outputIdx, consumerInstance, consumerInputIdx):
        """Record connection on the given output of the encapsulated module.

        @return: True if connection recorded, False if not (for example if
        connection already exists)
        """

        if self.findConsumerInOutputConnections(
            outputIdx, consumerInstance, consumerInputIdx) >= 0:
            # this connection has already been made, bail.
            return

        # do the connection
        ol = self.outputs[outputIdx]
        ol.append((consumerInstance, consumerInputIdx))

        # this is a new connection, so set the transfer times to 0
        self.transferTimes[
            (outputIdx, consumerInstance, consumerInputIdx)] = 0.0

    def disconnectOutput(self, outputIdx, consumerInstance, consumerInputIdx):
        """Record disconnection on the given output of the encapsulated module.
        """

        # find index of the given consumerInstance and consumerInputIdx
        # in the list of consumers connected to producer port outputIdx
        cidx = self.findConsumerInOutputConnections(
            outputIdx, consumerInstance, consumerInputIdx)

        # if this is a valid index, nuke it
        if cidx >= 0:
            ol = self.outputs[outputIdx]
            del ol[cidx]

            # also remove the relevant slot from our transferTimes
            del self.transferTimes[
                (outputIdx, consumerInstance, consumerInputIdx)]

        else:
            # consumer not found, the connection didn't exist
            raise Exception, \
                  "Attempt to disconnect output which isn't connected."
        

    def resetInputsOutputs(self):
        numIns = len(self.instance.getInputDescriptions())
        numOuts = len(self.instance.getOutputDescriptions())
        # numIns list of tuples of (supplierModule, supplierOutputIdx)
        # if the input is not connected, that position in the list is None
        # supplierModule is a module instance, not a metaModule
        self.inputs = [None] * numIns
        # numOuts list of lists of tuples of (consumerModule,
        # consumerInputIdx); consumerModule is an instance, not a metaModule
        # be careful with list concatenation, it makes copies, which are mostly
        # shallow!!!
        self.outputs = [[] for _ in range(numOuts)]

    def executeModule(self):
        """Used by moduleManager to execute module.

        This method also takes care of timestamping the execution time if
        execution was successful.
        """

        if self.instance:
            # this is the actual user function.
            # if something goes wrong, an exception will be thrown and
            # correctly handled by the invoking module manager
            self.instance.executeModule()

            # if we get here, everything is okay and we can record
            # the execution time.
            self.executeTime = time.time()

    def modify(self):
        """Used by the moduleManager to timestamp the modified time.

        This should be called whenever module state has changed in such a way
        as to invalidate the current state of the module.  At the moment,
        this is called by L{applyViewToLogic()} as well as by the
        moduleManager.
        """

        self.modifiedTime = time.time()

    def shouldExecute(self):
        """Determine whether the encapsulated module needs to be executed.
        """
        
        return self.modifiedTime > self.executeTime

    def shouldTransferOutput(
        self, outputIndex, consumerInstance, consumerInputIdx):
        """Determine whether output should be transferred through
        the given output index to the input index on the given consumer module.

        If the transferTime is older than executeTime, we should transfer.
        Semantics with viewer modules (internal division into source and
        sink modules by the scheduler) are taken care of by the scheduler.
        """

        # first double check that we're actually connected on this output
        # to the given consumerModule
        if self.findConsumerInOutputConnections(
            outputIndex, consumerInstance) >= 0:
            consumerFound = True
        else:
            consumerFound = False

        if consumerFound:
            tTime = self.transferTimes[
                (outputIndex, consumerInstance, consumerInputIdx)]

            return tTime < self.executeTime

        else:
            return False

    def timeStampTransferTime(
        self, outputIndex, consumerInstance, consumerInputIdx):
        """Timestamp given transfer time with current time.

        This method is called right after a successful transfer has been made.
        """

        # and set the timestamp
        self.transferTimes[
            (outputIndex, consumerInstance, consumerInputIdx)] = time.time()
