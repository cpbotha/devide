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

    def detectCycles(self, moduleInstances):
        """Given a list of module instances, detect cycles in the topology
        of the modules.

        @param moduleInstances: list of module instances that has to be
        checked.
        @return: True if cycles detected, False otherwise.
        @todo: check should really be limited to modules in selection.
        """

        mm = self._devideApp.getModuleManager()
        
        def _detectCycleMatch(visited, currentInstance):
            consumers = mm.getConsumerModules(currentInstance)

            for consumer in consumers:
                if consumer in visited:
                    return True

                else:
                    visited[consumer] = 1
                    if _detectCycleMatch(visited, consumer):
                        return True

            # the recursion ends when there are no consumers and 
            return False
            

        for moduleInstance in moduleInstances:
            if _detectCycleMatch({moduleInstance : 1}, moduleInstance):
                return True


        return False

    def topoSort(self, moduleInstances):
        """Given a list of module instances, this will perform a topological
        sort that can be used to determine the execution order of the
        give modules.

        @param moduleInstances: list of module instance to be sorted
        @return: modules in topological order.
        """

        pass

            

    
