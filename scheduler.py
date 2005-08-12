# scheduler.py copyright 2005 Charl P. Botha <http://cpbotha.net/>
# $Id: scheduler.py,v 1.1.2.3 2005/08/12 16:25:25 cpbotha Exp $

class schedulerModuleWrapper:
    """Wrapper class that adapts module instance to scheduler-usable
    object.  We can use this to handle exceptions, such as the viewer
    split.

    @author: Charl P. Botha <http://cpbotha.net/>
    """
    
    def __init__(self, instance = None, view = False, viewSegment = -1):
        self.instance = instance
        self.view = view
        self.viewSegment = viewSegment

    def matches(self, otherModule):
        eq = self.instance == otherModule.instance and \
             self.view == otherModule.view and \
             self.viewSegment == otherModule.viewSegment

        return eq
        

class scheduler:
    """Coordinates event-driven network execution.

    @author: Charl P. Botha <http://cpbotha.net/>
    """

    def __init__(self, devideApp):
        """Initialise scheduler instance.

        @param moduleManager: an instance of the modulemanager class that
        we'll use to communicate with modules.
        """
        
        self._devideApp = devideApp

    def modulesToSchedulerModules(self, moduleInstances):
        """Preprocess module instance list before cycle detection or
        topological sorting to take care of exceptions.

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
        """Return moduleInstance consumers as a list of module instances
        wrapped with the scedulerModuleWrapper.

        @param moduleInstance: return modules that are connected to outputs
        of this instance.
        @return: list of schedulerModuleWrappers.
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
                
            
    def detectCycles(self, schedulerModules):
        """Given a list of moduleWrappers, detect cycles in the topology
        of the modules.

        @param moduleInstances: list of module instances that has to be
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
        """Given a list of module instances, this will perform a topological
        sort that can be used to determine the execution order of the
        give modules.

        @param schedulerModules: list of module instance to be sorted
        @return: modules in topological order.
        """

        if self.detectCycles(schedulerModules):
            # TODO: implement schedulerException class
            raise RuntimeError
            
