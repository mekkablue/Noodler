#!/usr/bin/env python
# encoding: utf-8

import objc
from Foundation import *
from AppKit import *
import sys, os, re, math

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp
GLYPHSAPPVERSION = NSBundle.bundleForClass_(GSMenu).infoDictionary().objectForKey_("CFBundleShortVersionString")

GSLINE = 1
GSCURVE = 35
GSOFFCURVE = 65
MAGICNUMBER = 4.0 * ( 2.0**0.5 - 1.0 ) / 3.0

class Noodler ( GSFilterPlugin ):
	noodleThicknessField = objc.IBOutlet()
	extremesAndInflectionsField = objc.IBOutlet()
	removeOverlapField = objc.IBOutlet()
	
	def init( self ):
		try:
			NSBundle.loadNibNamed_owner_( "NoodlerDialog", self )
			return self
		except Exception as e:
			self.logToConsole( "init: %s" % str(e) )
	
	def interfaceVersion( self ):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )
	
	def title( self ):
		"""
		This is the name as it appears in the menu
		and in the title of the dialog window.
		"""
		try:
			return "Noodler"
		except Exception as e:
			self.logToConsole( "title: %s" % str(e) )
	
	def actionName( self ):
		"""
		This is the title of the button in the settings dialog.
		Use something descriptive like 'Move', 'Rotate', or at least 'Apply'.
		"""
		try:
			return "Noodle"
		except Exception as e:
			self.logToConsole( "actionName: %s" % str(e) )
	
	def keyEquivalent( self ):
		""" 
		The key together with Cmd+Shift will be the shortcut for the filter.
		Return None if you do not want to set a shortcut.
		Users can set their own shortcuts in System Prefs.
		"""
		try:
			return None
		except Exception as e:
			self.logToConsole( "keyEquivalent: %s" % str(e) )
	
	def setup( self ):
		try:
			"""
			Prepares and pre-fills the dialog fields.
			"""
			super( Noodler, self ).setup()
			FontMaster = self.valueForKey_( "fontMaster" )
			
			self.noodleThickness = self.setDefaultListValue( "noodleThickness", [10.0,20.0], FontMaster )
			stringList = []
			for thisItem in self.noodleThickness:
				stringList.append( str(thisItem) )
			self.noodleThicknessField.setStringValue_( ", ".join(stringList) )
			
			self.extremesAndInflections = self.setDefaultBooleanValue( "noodleExtremesAndInflections", True, FontMaster )
			self.extremesAndInflectionsField.setObjectValue_( int( self.extremesAndInflections ) )

			self.removeOverlap = self.setDefaultBooleanValue( "noodleRemoveOverlap", True, FontMaster )
			self.removeOverlapField.setObjectValue_( int( self.removeOverlap ) )
			
			self.process_( None )
			return None
		except Exception as e:
			self.logToConsole( "setup: %s" % str(e) )
			# if something goes wrong, you can return an NSError object with details
	
	def setDefaultFloatValue( self, userDataKey, defaultValue, FontMaster ):
		"""
		Returns either the stored or default value for the given userDataKey.
		Assumes a floating point value. For use in self.setup().
		"""
		try:
			if userDataKey in FontMaster.userData:
				return FontMaster.userData[userDataKey].floatValue()
			else:
				return defaultValue
		except Exception as e:
			self.logToConsole( "setDefaultFloatValue: %s" % str(e) )
			
	def setDefaultBooleanValue( self, userDataKey, defaultValue, FontMaster ):
		"""
		Returns either the stored or default value for the given userDataKey.
		Assumes a boolean value. For use in self.setup().
		"""
		try:
			if userDataKey in FontMaster.userData:
				return bool( FontMaster.userData[userDataKey] )
			else:
				return defaultValue
		except Exception as e:
			self.logToConsole( "setDefaultBooleanValue: %s" % str(e) )
			
	def setDefaultListValue( self, userDataKey, defaultValue, FontMaster ):
		"""
		Returns either the stored or default value for the given userDataKey.
		Assumes a boolean value. For use in self.setup().
		"""
		try:
			if userDataKey in FontMaster.userData:
				userDataText = FontMaster.userData[userDataKey]
				userDataList = self.listOfFloats( userDataText )
				if userDataList == None:
					userDataList = []
				return userDataList
			else:
				return defaultValue
		except Exception as e:
			self.logToConsole( "setDefaultListValue: %s" % str(e) )
			
	def setDefaultIntegerValue( self, userDataKey, defaultValue, FontMaster ):
		"""
		Returns either the stored or default value for the given userDataKey.
		Assumes an integer value. For use in self.setup().
		"""
		try:
			if userDataKey in FontMaster.userData:
				return FontMaster.userData[userDataKey].integerValue()
			else:
				return defaultValue
		except Exception as e:
			self.logToConsole( "setDefaultIntegerValue: %s" % str(e) )
	
	@objc.IBAction
	def setNoodleThickness_( self, sender ):
		"""
		Called whenever the corresponding dialog field is changed.
		Gets the contents of the field and puts it into a class variable.
		Add methods like this for each option in the dialog.
		Important: the method name must end with an underscore, e.g., setValue_(),
		otherwise the dialog action will not be able to connect to it.
		"""
		try:
			noodleThicknessString = sender.stringValue()
			noodleThicknessList = []
			for thisNoodleThickness in noodleThicknessString.split(","):
				noodleThicknessList.append( float(thisNoodleThickness) )
			
			if noodleThicknessList != self.noodleThickness:
				self.noodleThickness = noodleThicknessList
				self.process_( None )
		except Exception as e:
			self.logToConsole( "setNoodleThickness_: %s" % str(e) )
	
	@objc.IBAction
	def setExtremesAndInflections_( self, sender ):
		try:
			extremesAndInflections = bool( sender.objectValue() )
			if extremesAndInflections != self.extremesAndInflections:
				self.extremesAndInflections = extremesAndInflections
				self.process_( None )
		except Exception as e:
			self.logToConsole( "setExtremesAndInflections_: %s" % str(e) )
	
	@objc.IBAction
	def setRemoveOverlap_( self, sender ):
		try:
			removeOverlap = bool( sender.objectValue() )
			if removeOverlap != self.removeOverlap:
				self.removeOverlap = removeOverlap
				self.process_( None )
		except Exception as e:
			self.logToConsole( "setRemoveOverlap_: %s" % str(e) )
	
	def isARealEnd( self, thisPoint, thisLayerBezierPath ):
		try:
			for xDiff in [-1.0,1.0]:
				for yDiff in [-1.0,1.0]:
					testPoint = NSPoint( thisPoint.x + xDiff, thisPoint.y + yDiff )
					if not thisLayerBezierPath.containsPoint_( testPoint ):
						return True
			return False
		except Exception as e:
			self.logToConsole( "isARealEnd: %s" % str(e) )
	
	def expandMonoline( self, Layer, noodleRadius ):
		try:
			offsetCurveFilter = NSClassFromString("GlyphsFilterOffsetCurve")
			if GLYPHSAPPVERSION.startswith("1."):
				offsetCurveFilter.offsetLayer_offsetX_offsetY_makeStroke_position_error_shadow_( Layer, noodleRadius, noodleRadius, True, 0.5, None, None )
			else:
				offsetCurveFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_error_shadow_( Layer, noodleRadius, noodleRadius, True, False, 0.5, None,None)
		except Exception as e:
			self.logToConsole( "expandMonoline: %s" % str(e) )
	
	def noodleLayer( self, thisLayer, noodleThickness, extremesAndInflections, removeOverlap, noodleBezierPath ):
		try:
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
					self.addExtremesToPathsInLayer( Layer )
					self.addInflectionNodesInLayer( Layer )
					
				# Expand monoline:
				self.expandMonoline( Layer, noodleRadius )

				# Add circle endings:
				for thisNodePair in circleCenters:
					circleCenter = thisNodePair[0]
					if self.isARealEnd( circleCenter, noodleBezierPath ):
						circleAtThisPosition = self.drawCircle( circleCenter, noodleRadius )
						if not self.extremesAndInflections:
							angle = self.angle( circleCenter, thisNodePair[1] )
							for thisNode in circleAtThisPosition.nodes:
								thisNode.position = self.rotate( thisNode.position, angle, circleCenter )
						Layer.paths.append( circleAtThisPosition )

				# Remove overlaps:
				if removeOverlap != False:
					removeOverlapFilter = NSClassFromString("GlyphsFilterRemoveOverlap").alloc().init()
					removeOverlapFilter.removeOverlapFromLayer_gridSize_checkSelection_error_( Layer, 0.0, False, None )

				# Round Corners:
				roundCornerFilter = NSClassFromString("GlyphsFilterRoundCorner")
				roundCornerFilter.roundLayer_radius_checkSelection_visualCorrect_grid_( Layer, noodleRadius, False, True, False )
			
			# Tidy up paths:
			Layer.cleanUpPaths()
			
			return Layer
		except Exception as e:
			self.logToConsole( "noodleLayer: %s" % str(e) )

	def bezierPathComp( self, thisLayer ):
		"""Compatibility method for bezierPath before v2.3."""
		layerBezierPath = NSBezierPath.bezierPath()
		try:
			layerBezierPath.appendBezierPath_( thisLayer.bezierPath() ) # until v2.2
		except Exception as e:
			layerBezierPath.appendBezierPath_( thisLayer.bezierPath ) # v2.3+
		
		for thisComponent in thisLayer.components:
			layerBezierPath.appendBezierPath_( thisComponent.bezierPath() )
		
		return layerBezierPath

	
	def processLayerWithValues( self, Layer, noodleThicknesses, extremesAndInflections, removeOverlap ):
		"""
		This is where your code for processing each layer goes.
		This method is the one eventually called by either the Custom Parameter or Dialog UI.
		Don't call your class variables here, just add a method argument for each Dialog option.
		"""
		try:
			if noodleThicknesses:
				Font = Layer.parent.parent
				
				# Virtual layer for checking whether a circle should be added:
				thinnestLayer = Layer.copy()
				smallestRadius = min(noodleThicknesses) * 0.5
				self.addExtremesToPathsInLayer( thinnestLayer )
				self.addInflectionNodesInLayer( thinnestLayer )
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
		except Exception as e:
			self.logToConsole( "processLayerWithValues: %s" % str(e) )
	
	def customParameterString( self ):
		"""Return the custom parameter string for the gear menu."""
		try:
			listOfNoodles = ["%.1f" % x for x in list(self.noodleThickness)]
			stringOfNoodleThicknesses = ", ".join(listOfNoodles)
			thisParameter = "Noodler; %s; %i; %i" % ( stringOfNoodleThicknesses.replace(" ",""), int(self.extremesAndInflections), int(self.removeOverlap) )
			return thisParameter
		except Exception as e:
			self.logToConsole( "customParameterString: %s" % str(e) )
	
	def listOfFloats( self, commaSeparatedString ):
		try:
			floatList = []
			for thisItem in str(commaSeparatedString).split(","):
				floatList.append( float( thisItem.strip() ) )
			return floatList
		except Exception as e:
			self.logToConsole( "listOfFloats: %s" % str(e) )
	
	def rotate( self, position, angle=180.0, origin=NSPoint(0.0,0.0) ):
		"""Rotates x/y around x_orig/y_orig by angle and returns result as [x,y]."""
		x = position.x
		y = position.y
		x_orig = origin.x
		y_orig = origin.y
		new_angle = ( angle / 180.0 ) * math.pi
		new_x = ( x - x_orig ) * math.cos( new_angle ) - ( y - y_orig ) * math.sin( new_angle ) + x_orig
		new_y = ( x - x_orig ) * math.sin( new_angle ) + ( y - y_orig ) * math.cos( new_angle ) + y_orig
		return NSPoint( new_x, new_y )

	def angle( self, firstPoint, secondPoint ):
		xDiff = firstPoint.x - secondPoint.x
		yDiff = firstPoint.y - secondPoint.y
		tangens = yDiff / xDiff
		angle = math.atan( tangens ) * 180.0 / math.pi
		return angle
	
	def addExtremesToPathsInLayer( self, thisLayer ):
		"""Adds extrema to all paths in thisLayer."""
		try:
			for thisPath in thisLayer.paths:
				thisPath.addExtremes_(False)
		except Exception as e:
			self.logToConsole( "addExtremesToPathsInLayer: %s" % str(e) )
	
	def addInflectionNodesInLayer( self, thisLayer ):
		"""
		Adds inflection nodes to all paths in thisLayer.
		"""
		try:
			for ip in range( len( thisLayer.paths )):
				thisPath = thisLayer.paths[ip]
				numberOfNodes = len( thisPath.nodes )

				for i in range(numberOfNodes-1, -1, -1):
					node = thisPath.nodes[i]
					if node.type == 35: #CURVE
						nl = [ thisPath.nodes[ (x+numberOfNodes)%numberOfNodes ] for x in range( i-3, i+1 ) ]
						inflections = self.computeInflection( nl[0], nl[1], nl[2], nl[3] )
						if len(inflections) == 1:
							inflectionTime = inflections[0]
							thisPath.insertNodeWithPathTime_( i + inflectionTime )
		except Exception as e:
			self.logToConsole( "addInflectionNodesInLayer: %s" % str(e) )

	def computeInflection( self, p1, p2, p3, p4 ):
		"""
		For a given curve p1, p2, p3, p4,
		t for the first inflection point is calculated and returned.
		"""
		try:
			Result = []
			ax = p2.x - p1.x
			ay = p2.y - p1.y
			bx = p3.x - p2.x - ax
			by = p3.y - p2.y - ay
			cx = p4.x - p3.x - ax - bx - bx
			cy = p4.y - p3.y - ay - by - by
			c0 = ( ax * by ) - ( ay * bx )
			c1 = ( ax * cy ) - ( ay * cx )
			c2 = ( bx * cy ) - ( by * cx )
	
			if abs(c2) > 0.00001:
				discr = ( c1 ** 2 ) - ( 4 * c0 * c2)
				c2 *= 2
				if abs(discr) < 0.000001:
					root = -c1 / c2
					if (root > 0.001) and (root < 0.99):
						Result.append(root)
				elif discr > 0:
					discr = discr ** 0.5
					root = ( -c1 - discr ) / c2
					if (root > 0.001) and (root < 0.99):
						Result.append(root)
			
					root = ( -c1 + discr ) / c2
					if (root > 0.001) and (root < 0.99):
						Result.append(root)
			elif c1 != 0.0:
				root = - c0 / c1
				if (root > 0.001) and (root < 0.99):
					Result.append(root)

			return Result
		except Exception as e:
			self.logToConsole( "computeInflection: %s" % str(e) )
	
	def drawCircle( self, position, radius ):
		try:
			handle = MAGICNUMBER * radius
			x = position.x
			y = position.y
			links = x-radius
			rechts = x+radius
			oben = y+radius
			unten = y-radius
			
			# Prepare circle coordinates:
			myCoordinates = [
				[ NSPoint( x-handle, oben ), NSPoint( links, y+handle ), NSPoint( links, y ) ],
				[ NSPoint( links, y-handle ), NSPoint( x-handle, unten ), NSPoint( x, unten ) ],
				[ NSPoint( x+handle, unten ), NSPoint( rechts, y-handle ), NSPoint( rechts, y ) ],
				[ NSPoint( rechts, y+handle ), NSPoint( x+handle, oben ), NSPoint( x, oben ) ]
			]
			
			# Draw circle:
			myCircle = GSPath()
			for thisSetOfNodes in myCoordinates:
				if len(thisSetOfNodes) == 1:
					newNode = GSNode()
					newNode.type = GSLINE
					newNode.position = thisSetOfNodes[0]
					myCircle.nodes.append( newNode )
					
				elif len(thisSetOfNodes) == 3:
					for thisHandlePosition in thisSetOfNodes[:2]:
						newHandle = GSNode()
						newHandle.type = GSOFFCURVE
						newHandle.position = thisHandlePosition
						myCircle.nodes.append( newHandle )
						
					newNode = GSNode()
					newNode.type = GSCURVE
					newNode.position = thisSetOfNodes[2]
					myCircle.nodes.append( newNode )
			
			# Close path:
			myCircle.closed = True
			
			return myCircle
		except Exception as e:
			self.logToConsole( "drawCircle: %s" % str(e) )

	def processFont_withArguments_( self, Font, Arguments ):
		"""
		Invoked when called as Custom Parameter in an instance at export.
		The Arguments come from the custom parameter in the instance settings. 
		Item 0 in Arguments is the class-name. The consecutive items should be your filter options.
		"""
		try:
			# Set default values for potential arguments (values), just in case:
			noodleThickness = 10.0
			
			# set glyphList to all glyphs
			glyphList = Font.glyphs
			
			# Override defaults with actual values from custom parameter:
			if len( Arguments ) > 1:
				
				# change glyphList to include or exclude glyphs
				if "exclude:" in Arguments[-1]:
					excludeList = [ n.strip() for n in Arguments.pop(-1).replace("exclude:","").strip().split(",") ]
					glyphList = [ g for g in glyphList if not g.name in excludeList ]
				elif "include:" in Arguments[-1]:
					includeList = [ n.strip() for n in Arguments.pop(-1).replace("include:","").strip().split(",") ]
					glyphList = [ Font.glyphs[n] for n in includeList ]
			
				# Override defaults with actual values from custom parameter:
				if len( Arguments ) >= 2 and not "clude:" in Arguments[1]:
					self.noodleThickness = self.listOfFloats(Arguments[1])
					
				if len( Arguments ) >= 3 and not "clude:" in Arguments[2]:
					self.extremesAndInflections = bool( Arguments[2] )
				else:
					self.extremesAndInflections = True

				if len( Arguments ) >= 4 and not "clude:" in Arguments[3]:
					self.removeOverlap = bool( Arguments[3] )
				else:
					self.removeOverlap = True

			# With these values, call your code on every glyph:
			FontMasterId = Font.fontMasterAtIndex_(0).id
			for Glyph in glyphList:
				Layer = Glyph.layerForKey_( FontMasterId )
				self.processLayerWithValues( Layer, self.noodleThickness, self.extremesAndInflections, self.removeOverlap )
		except Exception as e:
			self.logToConsole( "processFont_withArguments_: %s" % str(e) )
	
	def selectionOnLayer( self, thisLayer ):
		"""Compatibility mathod for app versions prior to 2.2."""
		try:
			try:
				return thisLayer.selection()
			except:
				return thisLayer.selection
		except Exception as e:
			self.logToConsole( "selectionOnLayer: %s" % str(e) )
			
	
	def process_( self, sender ):
		"""
		This method gets called when the user invokes the Dialog.
		"""
		try:
			# Create Preview in Edit View, and save & show original in ShadowLayers:
			ShadowLayers = self.valueForKey_( "shadowLayers" )
			Layers = self.valueForKey_( "layers" )
			checkSelection = True
			for k in range(len( ShadowLayers )):
				ShadowLayer = ShadowLayers[k]
				Layer = Layers[k]
				Layer.setPaths_( NSMutableArray.alloc().initWithArray_copyItems_( ShadowLayer.pyobjc_instanceMethods.paths(), True ) )
				Layer.setSelection_( NSMutableArray.array() )
				
				shadowLayerSelection = self.selectionOnLayer(ShadowLayer)
				if len(shadowLayerSelection) > 0 and checkSelection:
					for i in range(len( ShadowLayer.paths )):
						currShadowPath = ShadowLayer.paths[i]
						currLayerPath = Layer.paths[i]
						for j in range(len(currShadowPath.nodes)):
							currShadowNode = currShadowPath.nodes[j]
							if currShadowNode in self.selectionOnLayer(ShadowLayer):
								Layer.addSelection_( currLayerPath.nodes[j] )
								
				self.processLayerWithValues( Layer, self.noodleThickness, self.extremesAndInflections, self.removeOverlap ) # add your class variables here
			Layer.clearSelection()
		
			# Safe the values in the FontMaster. But could be saved in UserDefaults, too.
			FontMaster = self.valueForKey_( "fontMaster" )
			noodleList = []
			for thisNoodleValue in self.noodleThickness:
				noodleList.append( str(thisNoodleValue) )
			FontMaster.userData[ "noodleThickness" ] = ", ".join(noodleList)
			FontMaster.userData[ "noodleExtremesAndInflections" ] = int(self.extremesAndInflections)
			FontMaster.userData[ "noodleRemoveOverlap" ] = int(self.removeOverlap)
			
			# call the superclass to trigger the immediate redraw:
			super( Noodler, self ).process_( sender )
		except Exception as e:
			self.logToConsole( "process_: %s" % str(e) )
	
	def logToConsole( self, message ):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "Filter %s:\n%s" % ( self.title(), message )
		print myLog
		NSLog( myLog )
