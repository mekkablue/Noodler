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

"""
	Using Interface Builder (IB):
	
	Your code communicates with the UI through
	- IBOutlets (.py->GUI): values available to a UI element (e.g. a string for a text field)
	- IBActions (GUI->.py): methods in this class, triggered by buttons or other UI elements
	
	In order to make the Interface Builder items work, follow these steps:
	1. Make sure you have your IBOutlets (other than _theView)
	   defined as class variables at the beginning of this controller class.
	2. Immediately *before* the def statement of a method that is supposed to be triggered
	   by a UI action (e.g., setMyValue_() triggered by the My Value field), put:
		@objc.IBAction
	   Make sure the method name ends with an underscore, e.g. setValue_(),
	   otherwise the action will not be able to send its value to the class method.
	3. Open the .xib file in XCode, and add and arrange interface elements.
	4. Add this .py file via File > Add Files..., Xcode will recognize IBOutlets and IBACtions
	5. In the left sidebar, choose Placeholders > File's Owner,
	   in the right sidebar, open the Identity inspector (3rd icon),
	   and put the name of this controller class in the Custom Class > Class field
	6. IBOutlets: Ctrl-drag from the File's Owner to a UI element (e.g. text field),
	   and choose which outlet shall be linked to the UI element
	7. IBActions: Ctrl-drag from a UI element (e.g. button) to the File’s Owner in the left sidebar,
	   and choose the class method the UI element is supposed to trigger.
	   If you want a stepping field (change the value with up/downarrow),
	   then select the Entry Field, and set Identity Inspector > Custom Class to:
		GSSteppingTextField
	   ... and Attributes Inspector (top right, 4th icon) > Control > State to:
		Continuous
	8. Compile the .xib file to a .nib file with this Terminal command:
		ibtool xxx.xib --compile xxx.nib
	   (Replace xxx by the name of your xib/nib)
	   Please note: Every time the .xib is changed, it has to be recompiled to a .nib.
	   Check Console.app for error messages to see if everything went right.
"""

class Noodler ( GSFilterPlugin ):
	"""
	All 'myValue' and 'myValueField' references are just an example.
	They correspond to the 'My Value' field in the .xib file.
	Replace and add your own class variables.
	"""
	noodleThicknessField = objc.IBOutlet()
	extremesAndInflectionsField = objc.IBOutlet()
	
	def init( self ):
		"""
		Do all initializing here.
		This is a good place to call random.seed() if you want to use randomisation.
		In that case, don't forget to import random at the top of this file.
		"""
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
			
			# These 2 lines look for saved values (the last ones entered),
			# 15.0 is a sample default value.
			# Do this for each value field in your dialog:
			self.noodleThickness = self.setDefaultFloatValue( "noodleThickness", 15.0, FontMaster )
			self.noodleThicknessField.setFloatValue_( self.noodleThickness )
			
			self.extremesAndInflections = self.setDefaultBooleanValue( "extremesAndInflections", True, FontMaster )
			self.extremesAndInflectionsField.setObjectValue_( int( self.extremesAndInflections ) )
			
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
			noodleThickness = sender.floatValue()
			if noodleThickness != self.noodleThickness:
				self.noodleThickness = noodleThickness
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
	
	def isARealEnd( self, thisPoint, thisLayer ):
		try:
			thisLayerBezierPath = thisLayer.bezierPath()
			for xDiff in [-1.0,1.0]:
				for yDiff in [-1.0,1.0]:
					testPoint = NSPoint( thisPoint.x + xDiff, thisPoint.y + yDiff )
					if not thisLayerBezierPath.containsPoint_( testPoint ):
						return True
			return False
		except Exception as e:
			self.logToConsole( "isARealEnd: %s" % str(e) )
			
	
	def processLayerWithValues( self, Layer, noodleThickness, extremesAndInflections ):
		"""
		This is where your code for processing each layer goes.
		This method is the one eventually called by either the Custom Parameter or Dialog UI.
		Don't call your class variables here, just add a method argument for each Dialog option.
		"""
		try:
			Font = Layer.parent.parent
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
			offsetCurveFilter = NSClassFromString("GlyphsFilterOffsetCurve")
			if GLYPHSAPPVERSION.startswith("1."):
				offsetCurveFilter.offsetLayer_offsetX_offsetY_makeStroke_position_error_shadow_( Layer, noodleRadius, noodleRadius, True, 0.5, None, None )
			else:
				offsetCurveFilter.offsetLayer_offsetX_offsetY_makeStroke_autoStroke_position_error_shadow_( Layer, noodleRadius, noodleRadius, True, False, 0.5, None,None)
			
			# Add circle endings:
			for thisNodePair in circleCenters:
				circleCenter = thisNodePair[0]
				if self.isARealEnd( circleCenter, Layer ):
					circleAtThisPosition = self.drawCircle( circleCenter, noodleRadius )
					if not self.extremesAndInflections:
						angle = self.angle( circleCenter, thisNodePair[1] )
						for thisNode in circleAtThisPosition.nodes:
							thisNode.position = self.rotate( thisNode.position, angle, circleCenter )
					Layer.paths.append( circleAtThisPosition )
				
			# Remove overlaps:
			removeOverlapFilter = NSClassFromString("GlyphsFilterRemoveOverlap").alloc().init()
			removeOverlapFilter.runFilterWithLayer_error_( Layer, None )
			
			# Round Corners:
			roundCornerFilter = NSClassFromString("GlyphsFilterRoundCorner").alloc().init()
			roundCornerFilter.setRadius_( noodleRadius )
			roundCornerFilter.roundLayer_( Layer )
			
			# Tidy up paths:
			Layer.cleanUpPaths()
					
		except Exception as e:
			self.logToConsole( "processLayerWithValues: %s" % str(e) )
	
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
					self.noodleThickness = Arguments[1].floatValue()
					
				if len( Arguments ) >= 3 and not "clude:" in Arguments[2]:
					self.extremesAndInflections = bool( Arguments[2] )
				
			# With these values, call your code on every glyph:
			FontMasterId = Font.fontMasterAtIndex_(0).id
			for Glyph in glyphList:
				Layer = Glyph.layerForKey_( FontMasterId )
				self.processLayerWithValues( Layer, self.noodleThickness, self.extremesAndInflections )
		except Exception as e:
			self.logToConsole( "processFont_withArguments_: %s" % str(e) )
	
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
				if len(ShadowLayer.selection()) > 0 and checkSelection:
					for i in range(len( ShadowLayer.paths )):
						currShadowPath = ShadowLayer.paths[i]
						currLayerPath = Layer.paths[i]
						for j in range(len(currShadowPath.nodes)):
							currShadowNode = currShadowPath.nodes[j]
							if ShadowLayer.selection().containsObject_( currShadowNode ):
								Layer.addSelection_( currLayerPath.nodes[j] )
								
				self.processLayerWithValues( Layer, self.noodleThickness, self.extremesAndInflections ) # add your class variables here
			Layer.clearSelection()
		
			# Safe the values in the FontMaster. But could be saved in UserDefaults, too.
			FontMaster = self.valueForKey_( "fontMaster" )
			FontMaster.userData[ "noodleThickness" ] = NSNumber.numberWithInteger_( self.noodleThickness )
			
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
