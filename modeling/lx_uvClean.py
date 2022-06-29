import maya.cmds as mc
from functools import partial


def createUI(pWindowTitle):
    windowID = 'lx_uvCleanUI'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, width=1, height=1, resizeToFitChildren=True)

    red_warning_style = "font-size:12px; font-family:Corbel; font-weight:600; color: #F5B7B1"

    mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 300)])
    mc.separator(h=20, style='none')

    mc.text(label_style('Sets default uvset to map1 on selected objects.', red_warning_style), align="left")
    mc.text(label_style('Copies uvset to map1 if set to not map1.', red_warning_style), align="left")
    mc.separator(h=20, style='none')

    mc.button(label='Execute', command=partial(uvClean))
    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


def uvClean(*args):
    sel = mc.ls(sl=1)

    print("UVClean Log: \n\n")

    for o in sel:
        sList = mc.listRelatives(o, s=True)
        print(sList)

        if sList is not None:
            print("Operating on "+o)
            s = sList[0]
            mc.select(s)
            mc.polyUVSet(currentUVSet=True, uvSet="map1")
            uvList = mc.polyUVSet(q=True, allUVSets=True)

            if len(uvList) > 1:

                if uvList[0] != "map1":
                    if "map1" in uvList:
                        i = uvList.index("map1")
                        mc.polyUVSet(rename=True, newUVSet="ayCLEAN_TEMP_NAME", uvSet=uvList[i])
                    mc.polyUVSet(rename=True, newUVSet="map1", uvSet=uvList[0])
                    print("....Renamed default uv set name from "+uvList[0]+" to default map1")

                uvList.remove("map1")
                print("....Copied uv set "+uvList[0]+" to default map1")
                mc.polyCopyUV(uvSetName="map1", uvSetNameInput=uvList[0])
                for uvs in uvList:
                    mc.polyUVSet(delete=True, uvSet=uvs)

            else:
                if uvList[0]!="map1":
                    mc.polyUVSet(rename=True, newUVSet="map1", uvSet=uvList[0])
                    print("....Renamed default uv set name from "+uvList[0]+" to default map1")
                else:
                    print("....Nothing to do")

            mc.delete(o, ch=True)

        else:
            print("....No shape relatives found")


def run(*args):
    createUI('LX UV Clean')
