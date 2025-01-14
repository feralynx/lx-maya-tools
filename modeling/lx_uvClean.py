import maya.cmds as mc
from functools import partial


# GUI
def createUI(pWindowTitle):
    windowID = 'lx_uvCleanUI'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, width=1, height=1, resizeToFitChildren=True)

    red_warning_style = "font-size:12px; font-family:Corbel; font-weight:600; color: #F5B7B1"

    mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 300)])
    mc.separator(h=20, style='none')

    mc.text(label_style('Sets default uvset to map1 on selected objects and deletes all other sets.', red_warning_style), align="left")
    mc.text(label_style('Copies uvset to map1 if set to not map1.', red_warning_style), align="left")
    mc.separator(h=20, style='none')

    mc.button(label='Execute', command=partial(uvClean))
    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


#Recursively find shapes underneath selected DAG object    
def recursShape(s):
    relDAG = mc.listRelatives(s,pa=True)
    
    if(relDAG):
        shapesList = []
        for r in relDAG:
            if(mc.nodeType(r)=='mesh'):
                print(r)
                shapesList.append(r)
            else:
                shapesList.append(recursShape(r))
        return shapesList
    
    # the selected node is a shape node
    elif(mc.nodeType(s)=='mesh'):
        return s
    else:
        return None


#Flatten a list recursively
def flatList(l, listAll):
    for i in l:
        if isinstance(i,list):
            flatList(i,listAll)
        else:
            listAll.append(i)


# Clean UVs
def uvClean(*args):
    sel = mc.ls(sl=1)

    print("UVClean Log: \n\n")

    for o in sel:
        # Get a list of all mesh shapes under selection
        sListRaw = recursShape(o)
        if sListRaw is None:
            print("....No shape relatives found")
            return
        sList = []
        flatList(sListRaw, sList)
        
        # Loop through all shapes
        for s in sList:
            uvList = mc.polyUVSet(s, q=True, allUVSets=True)

            if len(uvList) > 1: #There is more than one UV set

                if uvList[0] != "map1": #The active UV set is not map1
                    #Does map1 exist already? We need to rename it so we can rename the active UV set to map1
                    if "map1" in uvList: 
                        i = uvList.index("map1")
                        print(uvList)
                        mc.polyUVSet(s, rename=True, newUVSet="ayCLEAN_TEMP_NAME", uvSet=uvList[i]) #Temp name

                    mc.polyUVSet(s, rename=True, newUVSet="map1", uvSet=uvList[0]) #Rename active uvset to map1
                    print("....Renamed default uv set name from "+uvList[0]+" to default map1")
                
                uvList = mc.polyUVSet(s, q=True, allUVSets=True)
                for uvSet in uvList:
                    if uvSet != "map1": #Any non-"map1" named set should now be deleted.
                        mc.polyUVSet(s, delete=True, uvSet=uvSet)

            else: #There is only one UV set
                if uvList[0]!="map1": #The active UV set is not named map1
                    mc.polyUVSet(s, rename=True, newUVSet="map1", uvSet=uvList[0])
                    print("....Renamed default uv set name from "+uvList[0]+" to default map1")
                else:
                    print("....Nothing to do")

        mc.delete(o, ch=True) # Delete history on xform


def run(*args):
    createUI('LX UV Clean')


run()