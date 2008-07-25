# $Id$

# workaround to use adodbapi and other modules not
# included with DeVIDE
#import sys 
#sys.path = sys.path + ['', 'H:\\bld\\bin\\Wrapping\\CSwig\\Python\\RelWithDebInfo', 'H:\\opt\\python23\\Lib\\site-packages\\adodbapi', 'C:\\WINNT\\System32\\python23.zip', 'H:\\', 'H:\\opt\\python23\\DLLs', 'H:\\opt\\python23\\lib', 'H:\\opt\\python23\\lib\\plat-win', 'H:\\opt\\python23\\lib\\lib-tk', 'H:\\opt\\python23', 'H:\\opt\\python23\\Lib\\site-packages\\win32', 'H:\\opt\\python23\\Lib\\site-packages\\win32\\lib', 'H:\\opt\\python23\\Lib\\site-packages\\Pythonwin', 'H:\\opt\\python23\\lib\\site-packages\\adodbapi']

from module_base import ModuleBase
from moduleMixins import scriptedConfigModuleMixin
import moduleUtils
import vtk
import fixitk as itk
import wx
from datetime import date
from adodbapi import *
from modules.Insight.typeModules.transformStackClass import transformStackClass

class reconstructionRDR(scriptedConfigModuleMixin, ModuleBase):
	"""Fetches a transform stack from an MS Access database

	$Revision: 1.1 $
	"""
	
	def __init__(self, module_manager):
	# call the parent constructor
		ModuleBase.__init__(self, module_manager)

		# this is our output
		self._transformStack = transformStackClass( self )

#		moduleUtils.setupVTKObjectProgress(self, self._reader,
#		                                   'Fetching transformStack from database...')

		self._config.databaseFile = ""
		self._config.reconstructionName = "--- select a value ---"

		configList = [
			('Database:', 'databaseFile', 'base:str', 'filebrowser',
			'Database from which to fetch a reconstruction''s transformStack.',
			{'fileMode' : wx.OPEN,
			'fileMask' :
			'MDB files (*.mdb)|*.mdb|All files (*.*)|*.*'}),
			('Reconstruction:', 'reconstructionName', 'base:str', 'choice',
			'Specific reconstruction to use.', ("--- select a value ---",) ) ] 

		scriptedConfigModuleMixin.__init__(self, configList)

		self._viewFrame = self._createViewFrame({'Module (self)' : self})

		self.config_to_logic()
		self.syncViewWithLogic()

	def close(self):
		# we play it safe... (the graph_editor/module_manager should have
		# disconnected us by now)
		# for inputIdx in range(len(self.get_input_descriptions())):
		#    self.set_input(inputIdx, None)

		# this will take care of all display thingies
		scriptedConfigModuleMixin.close(self)

		ModuleBase.close(self)
		
		# get rid of our reference
		# del self._reader

	def get_input_descriptions(self):
		return ()

	def set_input(self, idx, inputStream):
		raise Exception

	def get_output_descriptions(self):
		return ('2D Transform Stack',)

	def get_output(self, idx):
		return self._transformStack

	def logic_to_config(self):
		#self._config.filePrefix = self._reader.GetFilePrefix()
		#self._config.filePattern = self._reader.GetFilePattern()
		#self._config.firstSlice = self._reader.GetFileNameSliceOffset()
		#e = self._reader.GetDataExtent()
		#self._config.lastSlice = self._config.firstSlice + e[5] - e[4]
		#self._config.spacing = self._reader.GetDataSpacing()
		#self._config.fileLowerLeft = bool(self._reader.GetFileLowerLeft())
		pass

	def config_to_logic(self):
		# get choice widget binding
		choiceBind = self._widgets[self._configList[1][0:5]]
		# abuse
		choiceBind.Clear()
		choiceBind.Append( "--- select a value ---" )
		reconstructionName = "--- select a value ---"
		
		# attempt to append a list at once
		if len( self._config.databaseFile ):			
			for e in self._getAvailableReconstructions(): 
				choiceBind.Append( e )

	def execute_module(self):
		if len( self._config.databaseFile ):
			self._fetchTransformStack()

		
	def _getAvailableReconstructions( self ):
		# connect to the database
		connectString = r"Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" + self._config.databaseFile + ";"
		
		try:
			connection = adodbapi.connect( connectString )
		except adodbapi.Error:
			raise IOError, "Could not open database."
		
		cursor = connection.cursor()
		cursor.execute( "SELECT name FROM reconstruction ORDER BY run_date" )
		
		reconstruction_list = cursor.fetchall()

		cursor.close()
		connection.close()

		# cast list of 1-tuples to list
		return [ e[ 0 ] for e in reconstruction_list ]

	def _fetchTransformStack( self ):
		# connect to the database
		connectString = r"Provider=Microsoft.Jet.OLEDB.4.0;Data Source=" + self._config.databaseFile + ";"

		try:
			connection = adodbapi.connect( connectString )
		except adodbapi.Error:
			raise IOError, "Could not open database."
		
		# try to figure out reconstruction ID from recontruction name
		print "NAME: " + self._config.reconstructionName
		cursor = connection.cursor()
		cursor.execute( "SELECT id FROM reconstruction WHERE name=?", [ self._config.reconstructionName ] )
		
		row = cursor.fetchone()
		if row == None:
			raise IOError, "Reconstruction not found."

		print "reconstructionID: %i" % row[ 0 ]
		
		# build transformStack
		cursor.execute( "SELECT angle, centerx, centery, tx, ty FROM centeredRigid2DTransform WHERE reconstruction_id=? ORDER BY seq_nr", [ row[ 0 ] ] )
		for row in cursor.fetchall():
			trfm = itk.itkCenteredRigid2DTransform_New()

			params = trfm.GetParameters()
			for i in range(0,5):
				params.SetElement( i, row[ i ] )
			trfm.SetParameters( params )

			self._transformStack.append( trfm )

		cursor.close()
		connection.close()
