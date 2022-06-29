# Manual Texture Repath Tool 
# Alan Yang 06.29.22

# This is a dirty direct tool for copying and repathing textures to a new directory. Works with standard textures and UDIMs.
# Because it is very direct and does not potentially detect for every use case please save before using.
# This is meant to work with either standard textures or UDIM textures.
# 1. Select file nodes to repath.
# 2. Type in new directory.
# 3. Run script.

import maya.cmds as mc
import os
import functools
from functools import partial
import maya.app.general.fileTexturePathResolver as ftpr

# GUI

def createUI(pWindowTitle):

    windowID = 'myWindowID1995'
    
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    
    mc.window( windowID,title=pWindowTitle,sizeable=False,resizeToFitChildren=True)
    mc.window( windowID,edit=True, width=500,height=50)
    
    mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,500) ] )
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text("Select file nodes to copy/repath, enter new path, then run the script.")
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text("See the Script Editor for verbose output.")
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text("You can use the File Path Editor to mass select file nodes before using this.")
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text("Enter new path below. Save first!")
    mc.separator( h=10, style='none')
    filePath = mc.textField("path")
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')

    mc.button(label='execute', command = partial(repathTextures, mc.textField("path",query=True,text=True) )  )
    
    mc.showWindow()


# Texture repath function

def repathTextures(newPath,*args):
    
    #Query path from text field
    newPath = mc.textField("path",query=True,text=True)
    print("New Path: "+newPath)
    
    #Selected file nodes
    selFile = mc.ls(sl=1)

    #Run through each file we have selected to repath.
    for file in selFile:

        #get full file path and replace backslashes with slashes
        fullPath_raw = mc.getAttr("%s.fileTextureName" % file)
        fullPath = fullPath_raw.replace(os.sep, '/')
        
        #get UDIM pattern
        pattern = ftpr.getFilePatternString(fullPath,False,3)
        files_UDIM = ftpr.findAllFilesForPattern(pattern,None)

        #Run through each potential UDIM tile we have found.
        
        if files_UDIM:
            print("UDIMs found \n")
            for tile in files_UDIM:
                
                #replace backslashes
                tile_path = tile.replace(os.sep, '/')
                #get file path for tile file name
                tileName = tile_path.split("/")[-1]
                print("Tile name: "+tileName+"\n")
                
                #copy texture
                newName = (newPath+"/"+tileName)
                print("New name: "+newName+"\n")
                mc.sysFile(tile_path,copy=newName)
                
                #repath texture
                mc.setAttr("%s.fileTextureName" %file, newName,type="string")
                
        if not files_UDIM:
            print("No UDIMs found \n")
        
            #get file path and replace backslashes
            fileName_raw = fullPath.split("/")[-1]
            fileName = fileName_raw.replace(os.sep, '/')
            print("File name: "+fileName+"\n")
            
            #copy texture
            newName = (newPath+"/"+fileName)
            print("New name: "+newName+"\n")
            mc.sysFile(file,copy=newName)
                
            #repath texture
            mc.setAttr("%s.fileTextureName" %file, newName,type="string")


def run(*args):
    createUI( 'LX Texture Repather' )