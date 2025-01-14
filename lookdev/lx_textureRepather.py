# Manual Texture Repath Tool 2.0 - Alan Yang

# This is a tool for copying and repathing textures to a new directory. Works with standard textures and UDIMs.
# Because it is very direct please save before using.
# This is meant to work with either standard textures or UDIM textures.
# 1. Select file nodes to repath.
# 2. Type in new directory.
# 3. Run script.

import maya.cmds as mc
import os
import functools
from functools import partial
import maya.app.general.fileTexturePathResolver as ftpr
import json
import tempfile

# GUI

def createUI(pWindowTitle):

    windowID = 'myWindowID1995'
    
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    
    mc.window( windowID,title=pWindowTitle,sizeable=False,resizeToFitChildren=True)
    mc.window( windowID,edit=True, width=500,height=50)
    
    singleLayout = mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,500) ] )
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


    # get best found default path to fill in the newPath text field
    savedDataDict = getSavedData()
    newPath_default = savedDataDict['newPath']
    if newPath_default is None: newPath_default = getAssetDefaultPath()
    newPath = mc.textField("newPath", text=newPath_default)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')

    # find/replace in texture filenames
    find_replace = mc.checkBox(l='Execute find/replace ', v=savedDataDict['find_replace'])
    mc.separator( h=10, style='none')
    double_layout = mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 50), (2, 175)])
    find = mc.text('Find: ', align="left", p=double_layout)
    source_tag_field = mc.textField("source_tag_field",
                    ed=True, text=savedDataDict['source_tag_field'], fn="boldLabelFont", p=double_layout)
    mc.separator(h=10, style='none', p=double_layout)
    mc.separator(h=10, style='none', p=double_layout)
    replace = mc.text('Replace: ', align="left", p=double_layout)
    target_tag_field = mc.textField("target_tag_field",
                    ed=True, text=savedDataDict['target_tag_field'], fn="boldLabelFont", p=double_layout)
    
    # dry run option (debug/noeffect)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    dry_run = mc.checkBox(l='Dry run (no effect) ', v=False, p=singleLayout)

    # run command button, and refresh settings in GUI button
    mc.separator(h=15, style='none', p=singleLayout)
    mc.button(label='Refresh settings to default', command =
                    partial(refreshGUI), p=singleLayout )
    mc.separator(h=15, style='none', p=singleLayout)
    mc.button(label='Run', p=singleLayout, command =
                    partial(repathTextures, find_replace, dry_run),
                    bgc = [0.25, 0.9, 0.4] )
    mc.separator(h=20, style='none', p=singleLayout)
    mc.showWindow()


def refreshGUI(*args):
    path = getAssetDefaultPath()
    writeSavedData(path, 0, '', '')
    createUI( 'Manual Texture Repath Tool 2.0' )


def getAssetDefaultPath(*args):
    fNameLong = mc.file(sn=1, q=1)
    # print("fNameLong", fNameLong)
    fNameSplit = fNameLong.split("/")
    rootPath = "/" + os.path.join(*fNameSplit[:-5])
    # print("rootPath", rootPath)

    textureWorkspace = rootPath + "/texture/work/"
    if os.path.isdir(textureWorkspace):
        workspaces = os.listdir(textureWorkspace)
        workspace_priority_list = ['images', 'photoshop', 'substancepainter', 'mari']
        for folder in workspace_priority_list:
            if not folder in workspaces: continue
            return textureWorkspace + folder
    
    sourceImages = rootPath + "/shade/work/maya/sourceimages"
    if os.path.isdir(sourceImages): return sourceImages

    return rootPath


# Retrieve saved json data in the gui's fields
def getSavedData(*args):
    tempDir = tempfile.gettempdir()
    #print("tempDir: {0}, {1}".format(tempDir, os.path.exists(tempDir)) )
    
    tempFile = tempDir+"/manualTextureRepathToolData.json"

    defaultDict = {'newPath': None,
                    'find_replace': False,
                    'source_tag_field': '',
                    'target_tag_field': ''}

    if not os.path.exists(tempFile):
        return defaultDict
    
    try:
        with open(tempFile) as f:
            jsonData = json.loads( f.read() )
    except Exception as ex:
        print(ex)
        return defaultDict
    
    return(jsonData)

# Write saved data from gui to json
def writeSavedData(newPath, find_replace, source_tag_field, target_tag_field, *args):
    tempDir = tempfile.gettempdir()
    tempFile = tempDir+"/manualTextureRepathToolData.json"

    json_data = {}
    json_data['newPath'] = newPath
    json_data['find_replace'] = find_replace
    json_data['source_tag_field'] = source_tag_field
    json_data['target_tag_field'] = target_tag_field

    json_string = json.loads( json.dumps(json_data) )
    json_output = json.dumps(json_string, indent=4)

    try:
        with open(tempFile, 'w') as outFile:
            outFile.write(json_output)
        return True
        
    except Exception as ex:
        print(ex)
        return False


# Texture repath function
def repathTextures(find_replace, dry_run, *args):
    
    #Query path from text field
    #newPath = mc.textField("path",query=True,text=True)
    newPath = mc.textField("newPath", q=True, text=True)
    if newPath[-1] == "/":
        newPath = newPath[:-1]

    find_replace = mc.checkBox(find_replace, q=True,v=True)
    source_tag_field = mc.textField("source_tag_field", q=True, text=True)
    target_tag_field = mc.textField("target_tag_field", q=True, text=True)
    dry_run = mc.checkBox(dry_run, q=True, v=True)

    if not os.path.isdir(newPath):
        mc.confirmDialog(
            message="New path entered does not exist on disk, please make it first.", button='OK')
        return

    #Selected file nodes
    selFile = mc.ls(sl=1)
    if not selFile:
        mc.confirmDialog(message="No file nodes were selected.", button='OK')
        return
    

    #Function for copying old file to new file, called in the loops.
    def copyTexture(fileNode, oldFile, newFile, dry_run):
        try:
            if os.path.exists(file):
                print("    Texture already exists in destination, skipping...")
                return False
            elif dry_run:
                with open(newFile, 'w') as f:
                    f.write("texture write check")
                    f.close()
                os.remove(newFile)
            else:
                mc.sysFile(oldFile, copy=newFile)
                mc.setAttr("%s.fileTextureName" %fileNode, newFile,type="string")
            print("    Copied texture.")

        except Exception as ex:
            print("    Could not copy...\n    {}".format(ex) )
            return False
        return True
    

    #Run through each file we have selected to repath.
    successfulFiles = []
    failedFiles = []
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
                print("Tile name: "+tileName)

                #execute find/replace. Need to leave extension and UDIM out of the name first.
                if find_replace:
                    tileName_split = tileName.split(".")

                    tileName_noExtOrUDIM = tileName_split[:-2]
                    if len(tileName_noExtOrUDIM) > 1:
                        tileName_noExtOrUDIM = '.'.join(tileName_noExtOrUDIM)
                    else: tileName_noExtOrUDIM = tileName_noExtOrUDIM[0]
                    tileName_udimAndExt = ''.join( ["." + s for s in tileName_split[-2:] ] )
                    
                    tileName = tileName_noExtOrUDIM.replace(source_tag_field, target_tag_field) + tileName_udimAndExt

                #copy texture 
                newName = (newPath+"/"+tileName)
                print("New name: "+newName)
                copy = copyTexture(file, tile_path, newName, dry_run)

                if copy: successfulFiles.append(tileName)
                else: failedFiles.append(tileName)
        
        #Regular non-UDIM texture found.
        if not files_UDIM:
            #get file path and replace backslashes
            fileName_raw = fullPath.split("/")[-1]
            fileName = fileName_raw.replace(os.sep, '/')
            print("File name: "+fileName+"\n")
            
            #execute find/replace
            if find_replace:
                fileName = fileName.replace(source_tag_field, target_tag_field)

            #copy texture 
            newName = (newPath+"/"+fileName)
            print("New name: "+newName)
            copy = copyTexture(file, fileName, newName, dry_run)

            if copy: successfulFiles.append(tileName)
            else: failedFiles.append(tileName)

        #rename file node name to match new one
        if dry_run: continue
        if not newName: continue

        #Try to rename the file node based on the new file name if possible
        try:
            newFileNodeName = newName.split("/")[-1].split(".")[0] 
            mc.rename(file, newFileNodeName )
        except Exception as ex:
            print("Could not rename {0}\n    {1}-{2}".format(file, type(ex).__name__, ex))
            
        print("\n")

    writeSavedData(newPath, find_replace, source_tag_field, target_tag_field)

    if dry_run:
        mc.confirmDialog(
        message="Dry run:\n{0} files would be successfully repathed.\n{1} files would have failed.\nSee details in Script Editor."
            .format(len(successfulFiles), len(failedFiles) ))
        return

    mc.confirmDialog(
        message="{0} files successfully repathed.\n{1} files failed.\nSee details in Script Editor."
            .format(len(successfulFiles), len(failedFiles) ))


createUI( 'LX Manual Texture Repath Tool 2.0' )