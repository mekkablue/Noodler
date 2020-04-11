# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
#
#	Filter with dialog Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Filter%20with%20Dialog
#
#	For help on the use of Interface Builder:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

MAGICNUMBER = 4.0 * ( 2.0**0.5 - 1.0 ) / 3.0

class Noodler(FilterWithDialog):
	
	# Definitions of IBOutlets
	dialog = objc.IBOutlet()
	noodleThicknessField = objc.IBOutlet()
	extremesAndInflectionsCheckbox = objc.IBOutlet()
	removeOverlapCheckbox = objc.IBOutlet()
	
	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Noodler',
			'de': u'Nudler',
			'fr': u'Nouilleur',
			'es': u'Fileteador',
			'zh': u'🍜等线圆体',
		})
		self.actionButtonLabel = Glyphs.localize({
			'en': u'Noodle',
			'de': u'Nudeln',
			'fr': u'Nouiller',
			'es': u'Expandir',
			'zh': u'变萌',
		})
		# Load dialog from .nib (without .extension)
		self.loadNib('IBdialog', __file__)
	
	# On dialog show
	@objc.python_method
	def start(self):
		# Set default setting if not present:
		Glyphs.registerDefault('com.mekkablue.Noodler.noodleThickness', "20.0")
		Glyphs.registerDefault('com.mekkablue.Noodler.extremesAndInflections', True)
		Glyphs.registerDefault('com.mekkablue.Noodler.removeOverlap', True)
		# Set values of UI elements:
		self.noodleThicknessField.setStringValue_( Glyphs.defaults['com.mekkablue.Noodler.noodleThickness'] )
		self.extremesAndInflectionsCheckbox.setObjectValue_( int(Glyphs.defaults['com.mekkablue.Noodler.extremesAndInflections']) )
		self.removeOverlapCheckbox.setObjectValue_( int(Glyphs.defaults['com.mekkablue.Noodler.removeOverlap']) )
		# Set focus to text field
		self.noodleThicknessField.becomeFirstResponder()
		
	# Action triggered by UI
	@objc.IBAction
	def setNoodleThickness_( self, sender ):
		# Store value coming in from dialog
		Glyphs.defaults['com.mekkablue.Noodler.noodleThickness'] = sender.stringValue()
		# Trigger redraw
		self.update()

	@objc.IBAction
	def setExtremesAndInflections_( self, sender ):
		Glyphs.defaults['com.mekkablue.Noodler.extremesAndInflections'] = bool(sender.objectValue())
		self.update()

	@objc.IBAction
	def setRemoveOverlap_( self, sender ):
		Glyphs.defaults['com.mekkablue.Noodler.removeOverlap'] = bool(sender.objectValue())
		self.update()
	
	# Actual filter
	@objc.python_method
	def filter(self, Layer, inEditView, customParameters):
		
		# Called on font export, get value from customParameters:
		if customParameters:
			# fallback values:
			noodleThicknessString = "20.0"
			extremesAndInflections = True
			removeOverlap = True
			# overwrite with values from parameters:
			try:
				noodleThicknessString = customParameters[0]
				extremesAndInflections = customParameters[1]
				removeOverlap = customParameters[2]
			except:
				# probably exceeded customParameters
				pass
		
		# Called through UI, use stored values:
		else:
			noodleThicknessString = Glyphs.defaults['com.mekkablue.Noodler.noodleThickness']
			extremesAndInflections = bool(Glyphs.defaults['com.mekkablue.Noodler.extremesAndInflections'])
			removeOverlap = bool(Glyphs.defaults['com.mekkablue.Noodler.removeOverlap'])
		
		noodleThicknesses = self.listOfFloats( noodleThicknessString )
		
		if noodleThicknesses:
			Font = Layer.parent.parent
			
			# Virtual layer for checking whether a circle should be added:
			thinnestLayer = Layer.copy()
			smallestRadius = min(noodleThicknesses) * 0.5
			thinnestLayer.addExtremePoints()
			thinnestLayer.addInflectionPoints()
			self.expandMonoline( thinnestLayer, smallestRadius )
			thisLayerBezierPath = self.bezierPathComp(thinnestLayer)
			
			# create a noodle for each noodle value:
			collectionOfNoodledLayers = []
			for noodleThickness in noodleThicknesses:
				if float(noodleThickness) != 0.0:
					thisLayer = self.noodleLayer( Layer, noodleThickness, extremesAndInflections, removeOverlap, thisLayerBezierPath )
					collectionOfNoodledLayers.append( thisLayer )

			# clean out Layer:
			for pathIndex in range(len(Layer.paths))[::-1]:
				Layer.removePathAtIndex_( pathIndex )

			# add all noodles to the path:
			for noodledLayer in collectionOfNoodledLayers:
				for noodledPath in noodledLayer.paths:
					Layer.addPath_( noodledPath )

			# correct path direction to get the black/white right:
			Layer.correctPathDirection()
	
	@objc.python_method
	def generateCustomParameter( self ):
		return "%s; %s; %i; %i" % (
			self.__class__.__name__,
			Glyphs.defaults['com.mekkablue.Noodler.noodleThickness'],
			Glyphs.defaults['com.mekkablue.Noodler.extremesAndInflections'],
			Glyphs.defaults['com.mekkablue.Noodler.removeOverlap'],
			)

	@objc.python_method
	def isARealEnd( self, thisPoint, thisLayerBezierPath ):
		for xDiff in [-1.0,1.0]:
			for yDiff in [-1.0,1.0]:
				testPoint = NSPoint( thisPoint.x + xDiff, thisPoint.y + yDiff )
				if not thisLayerBezierPath.containsPoint_( testPoint ):
					return True
		return False
	
	@objc.python_method
	def expandMonoline( self, Layer, noodleRadius ):
		try:
			offsetCurveFilter = NSClassFromString("GlyphsFilterOffsetCurve")
			offsetCurveFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_error_shadow_( Layer, noodleRadius, noodleRadius, True, False, 0.5, None,None)
		except Exception as e:
			self.logToConsole( "expandMonoline: %s\n%s" % (str(e), traceback.format_exc()) )
	
	@objc.python_method
	def noodleLayer( self, thisLayer, noodleThickness, extremesAndInflections, removeOverlap, noodleBezierPath ):
		# Catch a crash:
		if noodleThickness == 0.0:
			noodleThickness = 1.0

		Layer = thisLayer.copy()
		
		if Layer.paths:
			noodleRadius = noodleThickness * 0.5
			
			# Collect circle positions:
			circleCenters = []
			for thisPath in Layer.paths:
				numOfNodesInPath = len(thisPath.nodes)
				if thisPath.closed == False and numOfNodesInPath > 1:
					firstPoint = thisPath.nodes[0].position
					secondPoint = thisPath.nodes[1].position
					circleCenters.append( [firstPoint, secondPoint] )

					lastPoint = thisPath.nodes[ numOfNodesInPath-1 ].position
					lastButOnePoint = thisPath.nodes[ numOfNodesInPath-2 ].position
					circleCenters.append( [lastPoint, lastButOnePoint] )

			# Add extremes and inflections:
			if extremesAndInflections:
				Layer.addExtremePoints()
				Layer.addInflectionPoints()
				
			# Expand monoline:
			self.expandMonoline( Layer, noodleRadius )

			# Add circle endings:
			for thisNodePair in circleCenters:
				circleCenter = thisNodePair[0]
				if self.isARealEnd( circleCenter, noodleBezierPath ):
					circleAtThisPosition = self.drawCircle( circleCenter, noodleRadius )
					try:
						# GLYPHS 3:
						Layer.shapes.append( circleAtThisPosition )
					except:
						# GLYPHS 2:
						Layer.paths.append( circleAtThisPosition )

			# Remove overlaps:
			if removeOverlap:
				if Layer.bounds.origin.x + Layer.bounds.size.width > 8190.0:
					centerX = Layer.bounds.origin.x + Layer.bounds.size.width * 0.5
					if centerX < 0.0:
						print("Warning: glyph '%s' too wide for overlap removal!" % Layer.parent.name)
					else:
						leftShiftMatrix = self.transform(shiftX=-centerX).transformStruct()
						rightShiftMatrix = self.transform(shiftX=centerX).transformStruct()
						Layer.applyTransform(leftShiftMatrix)
						Layer.removeOverlap()
						Layer.applyTransform(rightShiftMatrix)
				else:	
					Layer.removeOverlap()

			# Round Corners:
			roundCornerFilter = NSClassFromString("GlyphsFilterRoundCorner")
			roundCornerFilter.roundLayer_radius_checkSelection_visualCorrect_grid_( Layer, noodleRadius, False, True, False )
		
		# Tidy up paths:
		Layer.cleanUpPaths()
		
		return Layer
	
	@objc.python_method
	def bezierPathComp( self, thisLayer ):
		layerBezierPath = NSBezierPath.bezierPath()
		layerBezierPath.appendBezierPath_( thisLayer.bezierPath ) # v2.3+
		for thisComponent in thisLayer.components:
			try:
				layerBezierPath.appendBezierPath_( thisComponent.bezierPath )
			except:
				layerBezierPath.appendBezierPath_( thisComponent.bezierPath() )
		return layerBezierPath

	@objc.python_method
	def listOfFloats( self, commaSeparatedString ):
		floatList = []
		for thisItem in str(commaSeparatedString).split(","):
			floatList.append( float( thisItem.strip() ) )
		return floatList
	
	@objc.python_method
	def transform( self, shiftX=0.0, shiftY=0.0, rotate=0.0, skew=0.0, scale=1.0 ):
		myTransform = NSAffineTransform.transform()
		if rotate:
			myTransform.rotateByDegrees_(rotate)
		if scale != 1.0:
			myTransform.scaleBy_(scale)
		if not (shiftX == 0.0 and shiftY == 0.0):
			myTransform.translateXBy_yBy_(shiftX,shiftY)
		if skew:
			skewStruct = NSAffineTransformStruct()
			skewStruct.m11 = 1.0
			skewStruct.m22 = 1.0
			skewStruct.m21 = math.tan(math.radians(skew))
			skewTransform = NSAffineTransform.transform()
			skewTransform.setTransformStruct_(skewStruct)
			myTransform.appendTransform_(skewTransform)
		return myTransform
	
	@objc.python_method
	def angle( self, firstPoint, secondPoint ):
		"""
		Returns the angle (in degrees) of the straight line between firstPoint and secondPoint,
		0 degrees being the second point to the right of first point.
		firstPoint, secondPoint: must be NSPoint or GSNode
		"""
		xDiff = secondPoint.x - firstPoint.x
		yDiff = secondPoint.y - firstPoint.y
		return math.degrees(math.atan2(yDiff,xDiff))

	@objc.python_method
	def drawCircle( self, position, radius ):
		handle = MAGICNUMBER * radius
		x = position.x
		y = position.y
		links = x-radius
		rechts = x+radius
		oben = y+radius
		unten = y-radius
		
		# Prepare circle coordinates:
		myCoordinates = (
			( NSPoint( x-handle, oben ),   NSPoint( links, y+handle ),  NSPoint( links, y )  ),
			( NSPoint( links, y-handle ),  NSPoint( x-handle, unten ),  NSPoint( x, unten )  ),
			( NSPoint( x+handle, unten ),  NSPoint( rechts, y-handle ), NSPoint( rechts, y ) ),
			( NSPoint( rechts, y+handle ), NSPoint( x+handle, oben ),   NSPoint( x, oben )   ),
		)
		
		# Draw circle:
		myCircle = GSPath()
		for thisSetOfNodes in myCoordinates: 
			if len(thisSetOfNodes) == 1:
				newNode = GSNode()
				newNode.type = LINE
				newNode.position = thisSetOfNodes[0]
				myCircle.nodes.append( newNode )
				
			elif len(thisSetOfNodes) == 3:
				for thisHandlePosition in thisSetOfNodes[:2]:
					newHandle = GSNode()
					newHandle.type = OFFCURVE
					newHandle.position = thisHandlePosition
					myCircle.nodes.append( newHandle )
					
				newNode = GSNode()
				newNode.type = CURVE
				newNode.position = thisSetOfNodes[2]
				myCircle.nodes.append( newNode )
		
		# Close path:
		myCircle.closed = True
		
		return myCircle

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
