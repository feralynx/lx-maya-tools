# USAGE:
# Enter alembic paths into fields to check model changes
# First you must click Load Meshes to load in the models and log their data
# Then you can run Compare Meshes to spit out information in the Maya console.
# Look in script editor for details
# You must be properly set in a maya project

import maya.cmds as mc
import maya.OpenMaya as om
import pymel.core as pm

import os
import os.path
import re

import functools
from functools import partial

from datetime import datetime




# GUI
def createUI(pWindowTitle):

    windowID = 'ayModCompareWindow'
    
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    
    mc.window( windowID,title=pWindowTitle,sizeable=True,resizeToFitChildren=False)
    mc.window( windowID,edit=True, width=600,h=380)
    
    # set styles
    title_style = "font-size:18px; font-family:Corbel; font-weight:600; color: #AED6F1"
    general_style = "font-size:14px; font-family:Corbel; font-weight:600; color: #AEB6BF"
    red_warning_style = "font-size:14px; font-family:Corbel; font-weight:600; color: #F5B7B1"
    white_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #FDEBD0"
    
    # General info
    mc.frameLayout(labelVisible=0)
    mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,600) ] )
    mc.text(label_style("Model Compare Tool",title_style),al='left')
    mc.separator( h=10, style='none')
    mc.text(label_style("Resulting information is currently logged to the Script Editor.",white_warning_style),al='left')
    mc.separator( h=10, style='none')
    
    # Extra settings
    mc.frameLayout(label='Model Paths - Clean geo only - Alembic recommended')
    mc.rowColumnLayout(numberOfColumns=2, columnWidth=[100,500])
    mc.text(label_style("A (Old):",red_warning_style),al='left')
    fa = mc.textField(ed=True, fi="file_path_here", fn="smallObliqueLabelFont", width=500)
    mc.text(label_style("B (New):",red_warning_style),al='left')
    fb = mc.textField(ed=True, fi="file_path_here", fn="smallObliqueLabelFont", width=500)
    mc.setParent("..")

    # Execute button
    mc.frameLayout(labelVisible=0)
    mc.rowColumnLayout (numberOfColumns=1,columnWidth=[ (1,600) ] )
    mc.separator( h=20, style='none')
    mc.button(label='Load Meshes', bgc=(0.5,0.55,0.8), ebg=1, command = partial(loadMeshes, fa, fb) )
    mc.separator( h=10, style='none')
    mc.button(label='Compare Meshes', bgc=(0.5,0.8,0.6), ebg=1, command = partial(compareMeshes, fa, fb) )
    mc.separator( h=30, style='none')
    autoShader = mc.checkBox(l='Assign shader to blendshaped objects', v=0)
    autoSet = mc.checkBox(l='Add blendshaped objects to a Maya set', v=0)
    mc.separator( h=5, style='none')
    mc.button(label='Mass Blendshape (B -> A)', bgc=(0.9,0.5,0.4), ebg=1, command = partial(blendAll, fa, fb, autoShader, autoSet) )
    mc.separator( h=10, style='none')
    mc.button(label='Assign Shaders (A -> B) EXPERIMENTAL', bgc=(0.8,0.6,0.45), ebg=1, command = partial(copyShaders, fa, fb) )
    
    mc.setParent("..")
    
    mc.showWindow()


    
# label CSS for GUI
def label_style (value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)



### ############### ###
### UTILITY CLASSES ###
### ############### ###


# Mesh Class for storing and writing mesh information
# 1. store: Reads and stores mesh data to disk
# 2. reference: create maya reference of filepath
# 3. dataFolder: makes data folder if necessary within project set
# 4. meshInfo: Retrieve previously stored mesh information and return it
class Mesh(object):
    def __init__(self, nspace, path):
        self.nspace = nspace
        _p = path
        _p = _p.replace(os.sep, '/')
        _p = _p.replace('"', '')
        self.path = _p
        
    def store(self):
        mc.select(self.nspace+":*")
        meshList = mc.ls(sl=True, type='mesh')
        storeLoc = self.dataFolder()

        s = " :: "
        with open(storeLoc + "/" + self.nspace + "_modelData" + ".txt", 'wt') as disk_file:
            disk_file.write("_FILENAME_" +s+ self.path+"\n")
            for _ in meshList:
                # print("debug "+_+"\n")
                m = _.split(":")
                
                sel = om.MSelectionList()
                sel.add(_)
                path = om.MDagPath()
                sel.getDagPath(0, path)
                mesh = om.MFnMesh(path)
                poly = mesh.numPolygons() # polycount

                
                disk_file.write("_MESHNAME_" + s+ m[1]+ s+ str(poly)+"\n")
   
   
    def reference(self):
        mc.file(self.path, r=True, ns=self.nspace)
                
            
    def dataFolder(self):
        _fPath = mc.file(sn=1,q=1)
        _fPathSplit = _fPath.split("/")
        _fPathSplit.remove(_fPathSplit[len(_fPathSplit)-1])
        _fPathSplit.remove(_fPathSplit[len(_fPathSplit)-1])
        
        _dataPath = ''
        for i in _fPathSplit:
            _dataPath += i+"/"
        _dataPath += 'data'
        
        _fNameLong = mc.file(sn=1,q=1,shn=1)
        _fNameSplit = _fNameLong.split(".")
        _fName = _fNameSplit[0]
        
        storePath = _dataPath + "/" + _fName
        
        if not os.path.exists(storePath):
            os.mkdir(storePath)   
        
        return storePath
        
        
    def meshInfo(self):
        storeLoc = self.dataFolder()
        # dataFiles = [f for f in os.listdir(storeLoc) if os.path.isdir(storeLoc)] DEBUG
        data = storeLoc + "/" + self.nspace + "_modelData.txt"
        
        with open(data, 'r') as f:
            dataList = [line.strip() for line in f] # every line into a list
            
        fName = dataList[0] 
        fName.replace("_FILENAME_ :: ","")
        dataList.pop(0)
        
        meshCount = len(dataList)
            
        mList = []
          
        for l in dataList:
            sub = l.split(" :: ")
            sub.pop(0)
            mList.append(sub)
        
        return [fName, meshCount, mList]




# Supervisor class for parsing and comparing mesh information
# 1. meshCountCompare: Compare mesh count
# 2. nameCompare: Compare mesh names (Currently just shape nodes)
# 3. compList: Return pruned comparative lists of matching size, removing non-shared elements
# 4. polyCompare: Compare poly count changes between meshes named the same between versions
class Supervisor(object):
    def __init__(self, meshA, meshB, *args):
        self.meshA = meshA
        self.meshB = meshB
        
        self.mListA = self.meshA.meshInfo()
        self.mListB = self.meshB.meshInfo()
        
        self.dListA = sorted(self.mListA[2])
        self.dListB = sorted(self.mListB[2])


    def meshCountCompare(self):
        a = self.mListA[1]
        b = self.mListB[1]
        diff = a - b
        return [diff,a,b]
        
        
    def nameCompare(self):
        meshListA = []
        meshListB = []

        for m in self.dListA:
            meshListA.append(m[0])
        for m in self.dListB:
            meshListB.append(m[0])
        
        misListA = []
        misListB = []
        for m in meshListA:
            if m not in meshListB:
                misListA.append(m)
                for x in self.dListA:
                    if m == x[0]:
                        self.dListA.remove(x)
        for m in meshListB:
            if m not in meshListA:
                misListB.append(m)
                for x in self.dListB:
                    if m == x[0]:
                        self.dListB.remove(x)
        
        return [misListA,misListB]
        
        
    def compList(self):
        meshListA = []
        meshListB = []

        for m in self.dListA:
            meshListA.append(m[0])
        for m in self.dListB:
            meshListB.append(m[0])
        
        misListA = []
        misListB = []
        for m in meshListA:
            if m not in meshListB:
                misListA.append(m)
                for x in self.dListA:
                    if m == x[0]:
                        self.dListA.remove(x)
        for m in meshListB:
            if m not in meshListA:
                misListB.append(m)
                for x in self.dListB:
                    if m == x[0]:
                        self.dListB.remove(x)
        
        return [self.dListA,self.dListB]
        
    
    def polyCompare(self):
        misList = []
        for c, m in enumerate(self.dListB):
            d = int(m[1]) - int(self.dListA[c][1]) # poly count difference
            meshA = "fileA:" + str( self.dListA[c][0] )
            meshB = "fileB:" + str( self.dListB[c][0] )
            pc = mc.polyCompare(meshA, meshB, v=1, e=1, fd=1) # polyCompare for good measure
            
            if d != 0 or pc != 0:
                misList.append([m[0], d, pc])
                
        if not misList:
            return [["_CLEAR_",0,0]]
        return [misList]
        
            
    
    

### ####################################### ###
### PRIMARY BUTTON COMMANDS CALLED FROM GUI ###
### ####################################### ###


# Load meshes into scene and store data.
def loadMeshes(pathA, pathB, *args):
    _pA = mc.textField(pathA, query=True, text=True) 
    _pB = mc.textField(pathB, query=True, text=True)
    
    _l = [_pA, _pB]
    for _ in _l:
        if ".abc" not in _: # must use abc (for now)
            mc.confirmDialog( title='Error', message="Valid alembic paths not found.", defaultButton='OK',cancelButton='OK',button=['OK'],icn="critical")
            return
            
    fileA = Mesh("fileA", _pA)
    fileA.reference()
    fileA.store()
    
    fileB = Mesh("fileB", _pB)
    fileB.reference()
    fileB.store()



# Retrieve data and compare.
def compareMeshes(pathA, pathB, *args):
    _pA = mc.textField(pathA, query=True, text=True) 
    _pB = mc.textField(pathB, query=True, text=True)
    
    _l = ["fileA","fileB"]
    for _ in _l:
        try:
            mc.select(_+":*") # quick check if meshes are loaded (refine later)
        except:
            mc.confirmDialog( title='Error', message="Meshes were not loaded first or no longer properly exist in scene in expected namespaces.", defaultButton='OK',cancelButton='OK',button=['OK'],icn="critical")
            return
            
    now = datetime.now()
    dt_string = now.strftime("%d\%m\%Y %H:%M:%S")
    
    print("\n\n\n##################################\n")
    print("##       MODEL COMPARE LOG      ##\n")
    print("##       "+dt_string+ "    ##\n")
    print("##################################\n\n")
    print("##################################\n\n")
    print("MESH A:  "+ _pA +"\n")
    print("MESH B:  "+ _pB +"\n")
    print("##################################\n")
    
    
    #initialize Supervisor object to spit out comparison data
    supe = Supervisor( Mesh("fileA", _pA), Mesh("fileB", _pB) )
    
    
    # Mesh Count Check
    count = supe.meshCountCompare()
    print("\n\n\n####     MESH COUNT CHECK     ####\n\n")
    print("Mesh count difference: " + str(count[0]) + "\n")
    print("Meshes in A: " + str(count[1]) + "\n")
    print("Meshes in B: " + str(count[2]) + "\n")
    
    
    # Mesh Name Check
    print("\n\n\n####     MESH NAMES CHECK     ####\n")
    mNames = supe.nameCompare()
    print("\nA-only meshes: \n")
    for m in mNames[0]:
        print(str(m) + "\n")
    print("\n\nB-only meshes: \n")
    for m in mNames[1]:
        print(str(m) + "\n")
        
        
    # Topology Check
    print("\n\n\n####     TOPOLOGY CHECK     ####\n")
    polyDif = supe.polyCompare()
    polyDif = polyDif[0]
    
    if polyDif[0] == "_CLEAR_":
        print("No poly count changes between same-named meshes.\n")
        
    else:
        print("\nMesh changes B - A: \n")
        
        for m in polyDif:
            topoParse = {
                0: " Cmds check cleared... somewhow. ",
                1: " Vert check fail. ",
                2: " Edge check fail. ",
                3: " Vert and edge check fail. ",
                4: " Face topology fail. ",
                5: " Vert and face topology fail. ",
                7: " Vert, edge, and face topology fail. ",
            }
            _t = topoParse.get(m[2], " Cmds topology fail. ")
        
            print(str(m[0]) + ":  Change of " + str(m[1]) + " polygons.  //  "+ _t + "\n")



# Mass blendshape for a quick visual comparison.
def blendAll(pathA, pathB, autoShader, autoSet, *args):
    _pA = mc.textField(pathA, query=True, text=True) 
    _pB = mc.textField(pathB, query=True, text=True)
    shd = mc.checkBox(autoShader, query=True, v=True)
    aSet = mc.checkBox(autoSet, query=True, v=True)
    
    #initialize Supervisor object
    supe = Supervisor( Mesh("fileA", _pA), Mesh("fileB", _pB) )
    c = supe.compList()
    mA = c[0]
    mB = c[1]
    
    
    if shd==1:
        bldBlinn = pm.shadingNode('blinn', asShader=True)
        pm.setAttr(bldBlinn + '.color', (0.8,0.2,0.2) )
        bldSG = pm.sets (renderable = True, noSurfaceShader = True, empty = True)
        pm.connectAttr('%s.outColor' %bldBlinn, '%s.surfaceShader' %bldSG)
    
    if aSet==1:
        mayaSet = mc.sets(n="modCompare_BlendSet", t="Made by ayModCompare automatically", em=True)
    
    now = datetime.now()
    dt_string = now.strftime("%d\%m\%Y %H:%M:%S")
    
    print("\n\n\n##################################\n")
    print("##       MASSS BLENDSHAPE LOG      ##\n")
    print("##       "+dt_string+ "    ##\n")
    print("##################################\n\n")
    print("##################################\n\n")
    print("MESH A:  "+ _pA +"\n")
    print("MESH B:  "+ _pB +"\n")
    print("##################################\n")
    
    
    for c, m in enumerate(mB):
        try:
            tA = mc.listRelatives("fileA:"+str(mA[c][0]), type='transform', p=True)[0]
            tB = mc.listRelatives("fileB:"+str(m[0]), type='transform', p=True)[0]
            try:
                bld = mc.blendShape(tA, tB, weight=[0,1.0])
                if shd==1:
                    pm.sets(bldSG, edit=True, forceElement=tB)
                if aSet==1:
                    pm.sets(mayaSet, edit=True, forceElement=tB)
            except:
                print("\nError trying to blendshape "+tB)
        except IndexError:
            print("\nError trying to blendshape "+str(m[0]))
            


# copy shader assignments from first selected object
def assignShader(self):

	selected = mc.ls(dag=1,o=1, s=1, sl=1)
	driverShapeSelected = selected[0]

	drivenShapesList = selected
	drivenShapesList.remove(driverShapeSelected)

	shadingGrp = mc.listConnections(driverShapeSelected,type='shadingEngine')[0]

	mc.sets(drivenShapesList,forceElement=shadingGrp)


# Mass assign shaders from A -> (Useful after blendshaping All)
def copyShaders(pathA, pathB, *args):
    _pA = mc.textField(pathA, query=True, text=True) 
    _pB = mc.textField(pathB, query=True, text=True)

    #initialize Supervisor object
    supe = Supervisor( Mesh("fileA", _pA), Mesh("fileB", _pB) )
    c = supe.compList()
    mA = c[0]
    mB = c[1]
    
    
    for c, m in enumerate(mA):
        try:
            tA = "fileA:"+m[0]
            tB = "fileB:"+mB[c][0]
            try:
                shadingGrp = mc.listConnections(tA,type='shadingEngine')[0]
                pm.sets(shadingGrp, edit=True, forceElement=tB)
            except:
                print("\nError trying to assign "+tA)
        except IndexError:
            print("\nError trying to assign "+str(m[0]))
    

createUI('lx_modelCompare')