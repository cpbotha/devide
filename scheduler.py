# scheduler.py copyright 2005 Charl P. Botha <http://cpbotha.net/>
# $Id: scheduler.py,v 1.11 2005/11/04 10:07:35 cpbotha Exp $

#########################################################################
class schedulerException(Exception):
    pass
    
class cyclesDetectedException(schedulerException):
    pass

#########################################################################
class schedulerModuleWrapper:
    """Wrapper class that adapts module instance to scheduler-usable
    object.  
    
    We can use this to handle exceptions, such as the viewer
    split.  Module instances are wrapped on an ad hoc basis, so you CAN'T
    use equality testing or 'in' tests to check for matches.  Use the
    L{matches} method.
    
    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, instance = None, view = False, viewSegment = -1):
        self.instance = instance
        self.view = view
        self.viewSegment = viewSegment

    def matches(self, otherModule):
        """Checks if two schedulerModules are equivalent.
        
        Module instances are wrapped with this class on an ad hoc basis,
        so you can not check for equivalency with the equality or 'in'
        operators for example.  Use this method instead.
        
        @param otherModule: module with which equivalency should be tested.
        @return: True if equivalent, False otherwise.
        """
        eq = self.instance == otherModule.instance and \
             self.view == otherModule.view and \
             self.viewSegment == otherModule.viewSegment

        return eq
        
#########################################################################
class scheduler:
    """Coordinates event-driven network execution.

    @todo: document the execution model completely, including for example
    VTK exceptions and when updates are forced, etc.

    @author: Charl P. Botha <http://cpbotha.net/>
    """

    def __init__(self, devideApp):
        """Initialise scheduler instance.

        @param devideApp: an instance of the devideApplication that we'll use
        to communicate with the outside world.

        """
        
        self._devideApp = devideApp

    def modulesToSchedulerModules(self, moduleInstances):
        """Preprocess module instance list before cycle detection or
        topological sorting to take care of exceptions.
        
        Note that the modules are wrapped anew by this method, so equality
        tests with previously existing scheduleModules will not work.  You have
        to use the L{schedulerModuleWrapper.matches()} method.

        @param moduleInstances: list of raw module instances
        @return: list with schedulerModuleWrappers
        """
        
        # replace every view module with two segments: final and initial
        schedulerModuleWrappers = []
        for moduleInstance in moduleInstances:
            if hasattr(moduleInstance, 'IS_VIEW') and moduleInstance.IS_VIEW:
                # break it up into two
                smw1 = schedulerModuleWrapper(moduleInstance, True, 0)
                schedulerModuleWrappers.append(smw1)

                smw2 = schedulerModuleWrapper(moduleInstance, True, 1)
                schedulerModuleWrappers.append(smw2)

            else:
                smw = schedulerModuleWrapper(moduleInstance, False, -1)
                schedulerModuleWrappers.append(smw)

        return schedulerModuleWrappers

    def getConsumerModules(self, schedulerModule):
        """Return consumers of schedulerModule as a list of schedulerModules.
        
        The consumers that are returned have been wrapped on an ad hoc basis,
        so you can't trust normal equality or 'in' tests.  Use the 
        L{schedulerModuleWrapper.matches} method instead.

        @param schedulerModule: determine modules that are connected to outputs
        of this instance.
        @return: list of consumer schedulerModules, ad hoc wrappings.
        """

        if schedulerModule.view and schedulerModule.viewSegment == 0:
            # if schedulerModule is segment 0 of a view, there can't be
            # any consumers by definition.
            return []
        
        mm = self._devideApp.getModuleManager()
        consumers = mm.getConsumerModules(schedulerModule.instance)
        
        sConsumers = []
        for consumer in consumers:
            if hasattr(consumer, 'IS_VIEW') and consumer.IS_VIEW:
                view = True
                # it's a consumer, so segment has to be 0
                viewSegment = 0
                
            else:
                view = False
                viewSegment = -1
                
            sConsumers.append(
                schedulerModuleWrapper(consumer, view, viewSegment))

        return sConsumers

    def getProducerModules(self, schedulerModule):
        """Return producer modules and indices that supply schedulerModule
        with data.

        The producers that are returned have been wrapped on an ad hoc basis,
        so you can't trust normal equality or 'in' tests. Use the
        L{schedulerModuleWrapper.matches} method instead.

        @param schedulerModule: determine modules that are connected to inputs
        of this instance.
        @return: list of tuples with producer schedulerModules and output
        indices; producer modules have been wrapped in schedulerModules.
        """

        if schedulerModule.view and schedulerModule.viewSegment == 1:
            # if schedulerModule is segment 1 of a view, there can be no
            # producers (by definition)
            return []

        mm = self._devideApp.getModuleManager()
        # producers is a list of (instance, output_idx) tuples
        producers = mm.getProducerModules(schedulerModule.instance)

        sProducers = []
        for pInstance, outputIndex, consumerInputIdx in producers:
            if hasattr(pInstance, 'IS_VIEW') and pInstance.IS_VIEW:
                view = True
                # it's a producer, so segment has to be 1
                viewSegment = 1
                
            else:
                view = False
                viewSegment = -1
                
            sProducers.append(
                (schedulerModuleWrapper(pInstance, view, viewSegment),
                 outputIndex, consumerInputIdx))

        return sProducers
            
    def detectCycles(self, schedulerModules):
        """Given a list of moduleWrappers, detect cycles in the topology
        of the modules.

        @param schedulerModules: list of module instances that has to be
        checked.
        @return: True if cycles detected, False otherwise.
        @todo: check should really be limited to modules in selection.
        """

        def detectCycleMatch(visited, currentModule):
            """Recursive function used to check for cycles in the module
            network starting from initial module currentModule.

            @param visited: list of schedulerModules used during recursion.
            @param currentModule: initial schedulerModule
            @return: True if cycle detected starting from currentModule
            """
            
            consumers = self.getConsumerModules(currentModule)

            for consumer in consumers:
                for v in visited:
                    if consumer.matches(v):
                        return True
                    
                else:
                    # we need to make a copy of visited and send it along
                    # if we don't, changes to visit are shared between
                    # different branches of the recursion; we only want
                    # it to aggregate per recursion branch 
                    visited_copy = {}
                    visited_copy.update(visited)
                    visited_copy[consumer] = 1
                    
                    if detectCycleMatch(visited_copy, consumer):
                        return True

            # the recursion ends when there are no consumers and 
            return False
            

        for schedulerModule in schedulerModules:
            if detectCycleMatch({schedulerModule : 1},
                                schedulerModule):
                return True


        return False

    def topoSort(self, schedulerModules):
        """Perform topological sort on list of modules.

        Given a list of module instances, this will perform a
        topological sort that can be used to determine the execution
        order of the give modules.  The modules are checked beforehand
        for cycles.  If any cycles are found, an exception is raised.

        @param schedulerModules: list of module instance to be sorted
        @return: modules in topological order; in this case the instances DO
        match the input instances.
        @todo: separate topologically independent trees
        """
        
        def isFinalVertex(schedulerModule, currentList):
            """Determines whether schedulerModule is a final vertex relative
            to the currentList.
            
            A final vertex is a vertex/module with no consumers in the
            currentList.
            
            @param schedulerModule: module whose finalness is determined
            @param currentList: list relative to which the finalness is
            determined.
            @return: True if final, False if not.
            """
            
            # find consumers
            consumers = self.getConsumerModules(schedulerModule)
            # now check if any one of these consumers is present in currentList
            for consumer in consumers:
                for cm in currentList:
                    if consumer.matches(cm):
                        return False
                    
            return True
            

        if self.detectCycles(schedulerModules):
            raise cyclesDetectedException(
                'Cycles detected in network.  Unable to schedule.')
            
        # keep on finding final vertices, move to final list
        scheduleList = [] # this will be the actual schedules list
        tempList = schedulerModules[:] # copy of list so we can futz around
        
        while tempList:
            finalVertices = [sm for sm in tempList 
                             if isFinalVertex(sm, tempList)]
                             
            scheduleList.extend(finalVertices)
            for fv in finalVertices:
                tempList.remove(fv)
        
        
        scheduleList.reverse()
        return scheduleList

    def executeModules(self, schedulerModules):
        """Execute the modules in schedulerModules in topological order.

        For each module, all output is transferred from its consumers and then
        it's executed.  I'm still thinking about the implications of doing
        this the other way round, i.e. each module is executed and its output
        is transferred.

        @param schedulerModules: list of modules that should be executed in
        order.
        @raise cyclesDetectedException: This exception is raised if any
        cycles are detected in the modules that have to be executed.

        @todo: add start_module parameter, execution skips all modules before
        this module in the topologically sorted execution list.
        
        """
        
        if self.detectCycles(schedulerModules):
            raise cyclesDetectedException(
                'Cycles detected in selected network modules.  '
                'Unable to execute.')

        # this will also check for cycles...
        schedList = self.topoSort(schedulerModules)
        mm = self._devideApp.getModuleManager()
        
        for sm in schedList:
            # find all producer modules
            producers = self.getProducerModules(sm)
            # transfer relevant data
            for pmodule, output_index, input_index in producers:
                print 'checking for transfer'
                if mm.shouldTransferOutput(pmodule.instance, output_index,
                                           sm.instance, input_index):
                    print 'transferring output: %s:%d to %s:%d' % \
                          (pmodule.instance.__class__.__name__,
                           output_index,
                           sm.instance.__class__.__name__,
                           input_index)
                    mm.transferOutput(pmodule.instance, output_index,
                                          sm.instance, input_index)

            # here we can code exeptions that block execution
            # for example, the final segment of a view should never
            # be executed.  it's output is always ready (a result of
            # interaction)
            blockExecution = False
            if sm.view and sm.viewSegment == 1:
                blockExecution = True
                    
            # finally: execute module if its not blocked and the
            # moduleManager thinks it's necessary
            if not blockExecution and mm.shouldExecuteModule(sm.instance):
                print 'executing %s' % (sm.instance.__class__.__name__,)
                mm.executeModule(sm.instance)
                

