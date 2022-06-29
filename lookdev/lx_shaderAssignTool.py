# Simple tool for copying shader assignments without opening hypershade/node editor.
# Alan Yang 06.29.22

import maya.cmds as mc
import functools


def createUI(pWindowTitle):

	windowID = 'myWindowID'
	
	if mc.window(windowID, exists=True):
		mc.deleteUI(windowID)
	
	mc.window( windowID,title=pWindowTitle,sizeable=False,resizeToFitChildren=True)
	mc.window( windowID,edit=True, width=280,height=50)
	
	mc.rowColumnLayout( numberOfColumns=3, columnWidth=[ (1,50) ] )
	
	mc.separator( h=10, style='none')
	mc.button(label='Select Shading Group', command=selectShadingGroup )
	mc.separator( h=10, style='none')
	mc.separator( h=10, style='none')
	mc.button(label='Assign Shader From First Object', command=assignShaderFromFirstSelected )
	mc.separator( h=10, style='none')
	
	mc.showWindow()

# copy shader assignments from first selected object
def assignShaderFromFirstSelected(self):

	selected = mc.ls(dag=1,o=1, s=1, sl=1)
	driverShapeSelected = selected[0]

	drivenShapesList = selected
	drivenShapesList.remove(driverShapeSelected)

	shadingGrp = mc.listConnections(driverShapeSelected,type='shadingEngine')[0]

	mc.sets(drivenShapesList,forceElement=shadingGrp)

# select shading group of object
def selectShadingGroup(self):

	selected = mc.ls(dag=1,o=1, s=1, sl=1)
	driverShapeSelected = selected[0]

	shadingGrp = mc.listConnections(driverShapeSelected,type='shadingEngine')[0]
	print(shadingGrp)
	mc.select(shadingGrp, ne=1)

def run(*args):
	createUI('Shader Assign Tool')
