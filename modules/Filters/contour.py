from modules.Filters.sharedModules.contourFLTBase import contourFLTBase

class contour(contourFLTBase):

    def __init__(self, moduleManager):
        contourFLTBase.__init__(self, moduleManager, 'contourFilter')

