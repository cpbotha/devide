from modules.Filters.sharedModules.contourFLTBase import contourFLTBase

class marchingCubes(contourFLTBase):

    def __init__(self, moduleManager):
        contourFLTBase.__init__(self, moduleManager, 'marchingCubes')

