# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

"""
"""

import mutex

#########################################################################
class SchedulerException(Exception):
    pass
    
class CyclesDetectedException(SchedulerException):
    pass

#########################################################################
class SchedulerModuleWrapper:
    """Wrapper class that adapts module instance to scheduler-usable
    object.  
    
    We can use this to handle exceptions, such as the viewer
    split.  Module instances are wrapped on an ad hoc basis, so you CAN'T
    use equality testing or 'in' tests to check for matches.  Use the
    L{matches} method.

    @ivar instance: the module instance, e.g. instance of child of ModuleBase
    @ivar input_independent_part: part of module that is not input dependent,
    e.g. in the case of purely interaction-dependent outputs
    @ivar input_independent_outputs: list of outputs that are input-dependent.
    This has to be set for both dependent and independent parts of a module.

    @todo: functionality in this class has been reduced to such an
    extent that we should throw it OUT in favour of just working with
    (meta_module, part) tuples.  These we CAN use for hashing and
    equality tests.
    
    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, meta_module, part):
        self.meta_module = meta_module
        self.part = part

    def matches(self, otherModule):
        """Checks if two schedulerModules are equivalent.
        
        Module instances are wrapped with this class on an ad hoc basis,
        so you can not check for equivalency with the equality or 'in'
        operators for example.  Use this method instead.
        
        @param otherModule: module with which equivalency should be tested.
        @return: True if equivalent, False otherwise.
        """
        eq = self.meta_module == otherModule.meta_module and \
             self.part == otherModule.part

        return eq
        
#########################################################################
class Scheduler:
    """Coordinates event-driven network execution.

    DeVIDE currently supports two main scheduling modes: event-driven
    and demand-driven.  [1] contains a concise overview of the
    scheduling approach, but we'll go into some more detail in this
    in-code documentation.

    Event-driven scheduling:
    This is the default scheduling mode - the network is analysed and
    all modules are iterated through in topological order.  For each
    module, its inputs are transferred from its producer modules if
    necessary (i.e. a producer module has been executed since the
    previous transfer, or this (consumer) module has been newly
    connected (in which case the producer module's output t-time to
    this module is set to 0)).  All transfers are timestamped.  In
    event-driven mode, after every transfer, the streaming transfer
    timestamp for that connection is set to 0 so that subsequent
    hybrid scheduling runs will re-transfer all relevant data.  If the
    module has been modified, or inputs have been transferred to it
    (in which case it is also explicitly modified), its
    execute_module() method is then called.

    Hybrid scheduling:
    This mode of scheduling has to be explicitly invoked by the user.
    All modules with a streaming_execute_module() are considered
    streamable.  The largest subsets of streamable modules are found
    (see [1] for details on this algorithm).  All modules are iterated
    through in topological order and execution continues as for
    event-driven scheduling, except when a streamable module is
    encountered.  In that case, we use a different set of
    streaming_transfer_times to check whether we should transfer its
    producers' output data pointers (WITHOUT disconnect workaround).
    In every case that we do a transfer, the usual transfer timestamps
    are set to 0 so that any subsequent event-driven scheduling will
    re-transfer.  For each re-transfer, the module will be modified,
    thus also causing a re-execute when we change to event-driven mode.
    Only if the current streamable module is at one of the end points
    of the streamable subset and its execute_timestamp is
    older than the normal modification time-stamp, is its
    streaming_execute_module() method called and the
    streaming_execute_timestamp touched.

    Timestamps:
    There are four collections of timestamps:
    1. per module modified_time (initvalue 0)
    2. per module execute_time (initvalue 0)
    3. per output connection transfer_time
    4. per module streaming touch time (initvalue 0)

    When a module's configuration is changed by the user (the user
    somehow interacts with the module), the module's modified_time is
    set to current_time.

    When a module execution is scheduled:
    * For each supplying connection, the data is transferred if
      transfer_time(connection) < execute_time(producer_module), or in
      the hybrid case, if transfer_time(connection) <
      touch_time(producer_module)
    * If data is transferred to a module, that module's modified_time
      is set to current_time.
    * The module is then executed if modified_time > execute_time.
    * If the module is executed, execute_time is set to current_time.

    Notes:
    * there are two sets of transfer_time timestamps,
      one set each for event-driven and hybrid
    * there is only ONE set of modified times and of execute_times
    * See the timestamp description above, as well as the descriptions
      for hybrid and event-driven to see how the scheduler makes sure
      that switching between execution models automatically results in
      re-execution of modules that are adaptively scheduled.
    * in the case that illegal cycles are found, network execution is
      aborted.

    [1] C.P. Botha and F.H. Post, "Hybrid Scheduling in the DeVIDE
    Dataflow Visualisation Environment", accepted for SimVis 2008

    This should be a singleton, as we're using a mutex to protect per-
    process network execution.

    @author: Charl P. Botha <http://cpbotha.net/>
    """

    _execute_mutex = mutex.mutex()

    def __init__(self, devideApp):
        """Initialise scheduler instance.

        @param devideApp: an instance of the devideApplication that we'll use
        to communicate with the outside world.

        """
        
        self._devideApp = devideApp

    def meta_modules_to_scheduler_modules(self, meta_modules):
        """Preprocess module instance list before cycle detection or
        topological sorting to take care of exceptions.
        
        Note that the modules are wrapped anew by this method, so equality
        tests with previously existing scheduleModules will not work.  You have
        to use the L{SchedulerModuleWrapper.matches()} method.

        @param module_instances: list of raw module instances
        @return: list with SchedulerModuleWrappers
        """
        
        # replace every view module with two segments: final and initial
        SchedulerModuleWrappers = []
        for mModule in meta_modules:
            # wrap every part separately
            for part in range(mModule.numParts):
                SchedulerModuleWrappers.append(
                    SchedulerModuleWrapper(mModule, part))

        return SchedulerModuleWrappers

    def getConsumerModules(self, schedulerModule):
        """Return consumers of schedulerModule as a list of schedulerModules.
        
        The consumers that are returned have been wrapped on an ad hoc basis,
        so you can't trust normal equality or 'in' tests.  Use the 
        L{SchedulerModuleWrapper.matches} method instead.

        @param schedulerModule: determine modules that are connected to outputs
        of this instance.
        @param part: Only return modules that are dependent on this part.
        @return: list of consumer schedulerModules, ad hoc wrappings.
        """


        # get the producer meta module
        p_meta_module = schedulerModule.meta_module

        # only consumers that are dependent on p_part are relevant
        p_part = schedulerModule.part

        # consumers is a list of (outputIdx, consumerMetaModule,
        # consumerInputIdx) tuples
        mm = self._devideApp.get_module_manager()        
        consumers = mm.getConsumers(p_meta_module)
        
        sConsumers = []
        for outputIdx, consumerMetaModule, consumerInputIdx in consumers:
            if p_meta_module.getPartForOutput(outputIdx) == p_part:

                # now see which part of the consumerMetaModule is dependent
                cPart = consumerMetaModule.getPartForInput(consumerInputIdx)
                
                sConsumers.append(
                    SchedulerModuleWrapper(consumerMetaModule, cPart))

        return sConsumers

    def getProducerModules(self, schedulerModule):
        """Return producer modules and indices that supply schedulerModule
        with data.

        The producers that are returned have been wrapped on an ad hoc basis,
        so you can't trust normal equality or 'in' tests. Use the
        L{SchedulerModuleWrapper.matches} method instead.

        @param schedulerModule: determine modules that are connected to inputs
        of this instance.
        @return: list of tuples with (producer schedulerModule, output
        index, consumer input index). 
        """

        # get the consumer meta module
        c_meta_module = schedulerModule.meta_module
        # only producers that supply this part are relevant
        c_part = schedulerModule.part
        
        # producers is a list of (producerMetaModule, output_idx, inputIdx)
        # tuples
        mm = self._devideApp.get_module_manager()        
        producers = mm.getProducers(c_meta_module)

        sProducers = []
        for p_meta_module, outputIndex, consumerInputIdx in producers:

            if c_meta_module.getPartForInput(consumerInputIdx) == c_part:

                # find part of producer meta module that is actually
                # producing for schedulerModule
                p_part = p_meta_module.getPartForOutput(outputIndex)
                
                sProducers.append(
                    (SchedulerModuleWrapper(p_meta_module, p_part),
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
            raise CyclesDetectedException(
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

    def execute_modules(self, schedulerModules):
        """Execute the modules in schedulerModules in topological order.

        For each module, all output is transferred from its consumers and then
        it's executed.  I'm still thinking about the implications of doing
        this the other way round, i.e. each module is executed and its output
        is transferred.

        Called by SchedulerProxy.execute_modules().

        @param schedulerModules: list of modules that should be executed in
        order.
        @raise CyclesDetectedException: This exception is raised if any
        cycles are detected in the modules that have to be executed.

        @todo: add start_module parameter, execution skips all modules before
        this module in the topologically sorted execution list.
        
        """
        

        # stop concurrent calls of execute_modules.
        if not Scheduler._execute_mutex.testandset():
            return

        # first remove all blocked modules from the list, before we do any
        # kind of analysis.
        blocked_module_indices = []
        for i in range(len(schedulerModules)):
            if schedulerModules[i].meta_module.blocked:
                blocked_module_indices.append(i)

        blocked_module_indices.reverse()

        for i in blocked_module_indices:
            del(schedulerModules[i])
          

        # finally start with execution.
        try:
            if self.detectCycles(schedulerModules):
                raise CyclesDetectedException(
                    'Cycles detected in selected network modules.  '
                    'Unable to execute.')

            # this will also check for cycles...
            schedList = self.topoSort(schedulerModules)
            mm = self._devideApp.get_module_manager()

            for sm in schedList:
                print "### sched:", sm.meta_module.instance.__class__.__name__
                # find all producer modules
                producers = self.getProducerModules(sm)
                # transfer relevant data
                for pmodule, output_index, input_index in producers:
                    if mm.shouldTransferOutput(
                        pmodule.meta_module, output_index,
                        sm.meta_module, input_index):

                        print 'transferring output: %s:%d to %s:%d' % \
                              (pmodule.meta_module.instance.__class__.__name__,
                               output_index,
                               sm.meta_module.instance.__class__.__name__,
                               input_index)

                        mm.transferOutput(pmodule.meta_module, output_index,
                                          sm.meta_module, input_index)

                # finally: execute module if
                # ModuleManager thinks it's necessary
                if mm.shouldExecuteModule(sm.meta_module, sm.part):
                    print 'executing part %d of %s' % \
                          (sm.part, sm.meta_module.instance.__class__.__name__)

                    mm.execute_module(sm.meta_module, sm.part)

        finally:
            # in whichever way execution terminates, we have to unlock the
            # mutex.
            Scheduler._execute_mutex.unlock()
                
#########################################################################
class EventDrivenScheduler(Scheduler):
    pass

#########################################################################
class HybridScheduler(Scheduler):

    def execute_modules(self, schedulerModules):
        """Execute the modules in schedulerModules according to hybrid
        scheduling strategy.  See documentation in Scheduler class and
        the paper [1] for a complete description.

        @param schedulerModules: list of modules that should be executed in
        order.
        @raise CyclesDetectedException: This exception is raised if any
        cycles are detected in the modules that have to be executed.

        @todo: add start_module parameter, execution skips all modules before
        this module in the topologically sorted execution list.
        
        """
        

        # stop concurrent calls of execute_modules.
        if not Scheduler._execute_mutex.testandset():
            return

        # first remove all blocked modules from the list, before we do any
        # kind of analysis.
        blocked_module_indices = []
        for i in range(len(schedulerModules)):
            if schedulerModules[i].meta_module.blocked:
                blocked_module_indices.append(i)

        blocked_module_indices.reverse()

        for i in blocked_module_indices:
            del(schedulerModules[i])
          

        # finally start with execution.
        try:
            if self.detectCycles(schedulerModules):
                raise CyclesDetectedException(
                    'Cycles detected in selected network modules.  '
                    'Unable to execute.')

            # this will also check for cycles...
            schedList = self.topoSort(schedulerModules)
            mm = self._devideApp.get_module_manager()

            # find largest streamable subsets
            streamables_dict, streamable_subsets = \
                    self.find_streamable_subsets(schedulerModules)

            for sm in schedList:
                smt = (sm.meta_module, sm.part)
                if smt in streamables_dict:
                    streaming_module = True
                    print "### streaming ",
                else:
                    streaming_module = False
                    print "### ",

                print "sched:", sm.meta_module.instance.__class__.__name__
                # find all producer modules
                producers = self.getProducerModules(sm)
                # transfer relevant data
                for pmodule, output_index, input_index in producers:
                    pmt = (pmodule.meta_module, pmodule.part)
                    if streaming_module and pmt in streamables_dict:
                        streaming_transfer = True
                    else:
                        streaming_transfer = False


                    if mm.shouldTransferOutput(
                            pmodule.meta_module, output_index, 
                            sm.meta_module, input_index,
                            streaming_transfer):

                        if streaming_transfer:
                            print 'streaming ',

                        print 'transferring output: %s:%d to %s:%d' % \
                              (pmodule.meta_module.instance.__class__.__name__,
                               output_index,
                               sm.meta_module.instance.__class__.__name__,
                               input_index)

                        mm.transferOutput(pmodule.meta_module, output_index,
                                          sm.meta_module, input_index,
                                          streaming_transfer)

                # finally: execute module if
                # ModuleManager thinks it's necessary
                if streaming_module: 
                    if streamables_dict[smt] == 2:
                        # terminating module in streamable subset
                        if mm.shouldExecuteModule(sm.meta_module, sm.part):
                            print 'streaming executing part %d of %s' % \
                                  (sm.part, \
                                   sm.meta_module.instance.__class__.__name__)
                            
                            mm.execute_module(sm.meta_module, sm.part,
                                    streaming=True)
                            # if the module has been
                            # streaming_executed, it has also been
                            # touched.
                            sm.meta_module.streaming_touch_timestamp_module(sm.part)

                    # make sure we touch the module even if we don't
                    # execute it.  this is used in the transfer
                    # caching
                    elif sm.meta_module.should_touch(sm.part):
                        sm.meta_module.streaming_touch_timestamp_module(sm.part)


                else:
                    # this is not a streaming module, normal semantics
                    if mm.shouldExecuteModule(sm.meta_module, sm.part):
                        print 'executing part %d of %s' % \
                              (sm.part, \
                               sm.meta_module.instance.__class__.__name__)
                        
                        mm.execute_module(sm.meta_module, sm.part)
                                

        finally:
            # in whichever way execution terminates, we have to unlock the
            # mutex.
            Scheduler._execute_mutex.unlock()

    def find_streamable_subsets(self, scheduler_modules):
        """
        Algorithm for finding streamable subsets in a network.  Also
        see Algorithm 2 in the paper [1].

        @param scheduler_modules: topologically sorted list of
        SchedulerModuleWrapper instances (S).

        @return: dictionary of streamable MetaModule bindings (V_ss)
        mapping to 1 (non-terminating) or 2 (terminating) and list of
        streamable subsets, each an array (M_ss).

        """

        # get all streaming modules from S and keep topological
        # ordering (S_s == streaming_scheduler_modules)
        streamable_modules = []
        streamable_modules_dict = {}
        for sm in scheduler_modules:
            if hasattr(sm.meta_module.instance,
                    'streaming_execute_module'):
                streamable_modules.append((sm.meta_module, sm.part))
                # we want to use this to check for streamability later
                streamable_modules_dict[(sm.meta_module, sm.part)] = 1

        # now the fun begins:
        streamables_dict = {} # this is V_ss
        streamable_subsets = [] # M_ss

        def handle_new_streamable(smt, streamable_subset):
            """Recursive method to do depth-first search for largest
            streamable subset.

            This is actually the infamous line 9 in the article.

            @param: smt is a streamable module tuple (meta_module,
            part)
            """
            # get all consumers of sm
            # getConsumerModules returns ad hoc wrappings!
            sm = SchedulerModuleWrapper(smt[0], smt[1])
            consumers = self.getConsumerModules(sm)

            # if there are no consumers, per def a terminating module
            if len(consumers) == 0:
                terminating = True
            else:
                # check if ANY of the the consumers is non-streamable
                # in which case sm is also terminating
                terminating = False
                for c in consumers:
                    if (c.meta_module,c.part) not in \
                            streamable_modules_dict:
                        terminating = True
                        break

            if terminating:
                # set sm as the terminating module
                streamables_dict[smt] = 2
            else:
                # add all consumers to streamable_subset M
                ctuples = [(i.meta_module, i.part) for i in consumers]
                streamable_subset.append(ctuples)
                # also add them all to V_ss
                streamables_dict.fromkeys(ctuples, 1)
                for c in consumers:
                    handle_new_streamable((c.meta_module, c.part), 
                            streamable_subset)



        # smt is a streamable module tuple (meta_module, part)
        for smt in streamable_modules:
            if not smt in streamables_dict:
                # this is a NEW streamable module!
                # create new streamable subset
                streamable_subset = [smt]
                streamables_dict[smt] = 1
                # handle this new streamable
                handle_new_streamable(smt, streamable_subset)

                # handle_new_streamable recursion is done, add 
                # this subset list of subsets
                streamable_subsets.append(streamable_subset)

        return streamables_dict, streamable_subsets


#########################################################################
class SchedulerProxy:
    """Proxy class for all schedulers.

    Each scheduler mode is represented by a different class, but we
    want to use a common instance to access functionality, hence this
    proxy.
    """


    EVENT_DRIVEN_MODE = 0
    HYBRID_MODE = 1

    def __init__(self, devide_app):
        self.event_driven_scheduler = EventDrivenScheduler(devide_app)
        self.hybrid_scheduler = HybridScheduler(devide_app)
        # default mode
        self.mode = SchedulerProxy.EVENT_DRIVEN_MODE

    def get_scheduler(self):
        """Return the correct scheduler instance, dependent on the
        current mode.
        """
        s = [self.event_driven_scheduler, self.hybrid_scheduler][self.mode]
        return s

    def execute_modules(self, scheduler_modules):
        """Thunks through to the correct scheduler instance's
        execute_modules.

        This is called by NetworkManager.execute_network()
        """

        self.get_scheduler().execute_modules(scheduler_modules)

    def meta_modules_to_scheduler_modules(self, meta_modules):
        return self.get_scheduler().meta_modules_to_scheduler_modules(meta_modules)

    
