# Simple GUI utility for dealing with subdivision creasing in Maya.
# Alan Yang 06.29.2022

import maya.cmds as mc
from functools import partial


# GUI
def createUI(pWindowTitle):

    windowID = 'lx_CreaseUtility'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, resizeToFitChildren=True)
    mc.window(windowID, edit=True, width=200, h=200)

    # set styles
    # title_style = "font-size:20px; font-family:Corbel; font-weight:600; color: #AED6F1"
    red_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #F5B7B1"
    general_style = "font-size:13px; font-family:Corbel; font-weight:400; color: #AEB6BF"
    # white_warning_style = "font-size:18px; font-family:Corbel; font-weight:600; color: #FDEBD0"
    mainLayout = mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200)])
    # mc.text(label_style("Edge crease utility", title_style), al='left')
    # mc.separator(h=20, style='none')

    # Apply crease presets
    mc.text(label_style('Presets', red_warning_style), align="left")
    mc.text(label_style('Standard edge crease values.', general_style), align="left")
    mc.separator(h=5, style='none')
    mc.button(label='Remove (0.0)', command=partial(applyCrease, 0.0, 0), bgc=(0, 0, 0 ))
    mc.button(label='25% (0.5)', command=partial(applyCrease, 0.5, 0), bgc=(0.25, 0.25, 0.25))
    mc.button(label='50% (1.0)', command=partial(applyCrease, 1.0, 0), bgc=(0.5, 0.5, 0.5))
    mc.button(label='75% (1.5)', command=partial(applyCrease, 1.5, 0), bgc=(0.75, 0.75, 0.75))
    mc.button(label='100% (2.0)', command=partial(applyCrease, 2.0, 0), bgc=(1.0, 1.0, 1.0))

    # Apply custom crease
    mc.separator(h=10, style='none')
    mc.separator(h=10, style='none')
    mc.text(label_style('Custom', red_warning_style), align="left")
    mc.text(label_style('Specify a custom crease value.', general_style), align="left")
    mc.separator(h=5, style='none')
    mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 100)])
    manual_creaseValue = mc.floatField(ed=True, minValue=0, maxValue=2, value=0.5)
    mc.button(label='Apply', command=partial(applyCrease, manual_creaseValue, 1), bgc=(0.25, 1.0, 0.4))

    # Select creased edges
    mc.setParent(mainLayout)
    mc.separator(h=10, style='none')
    mc.separator(h=10, style='none')
    mc.text(label_style('Select', red_warning_style), align="left")
    mc.text(label_style('Get creases in selected objects.', general_style), align="left")
    mc.separator(h=5, style='none')
    mc.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100)])
    sel_creaseValue = mc.floatField(ed=True, minValue=0, maxValue=2, value=0.0)
    mc.button(label='Custom', command=partial(selectCrease, sel_creaseValue, 1), bgc=(0.9, 1.0, 0.4))
    mc.button(label='All', command=partial(selectCrease, sel_creaseValue, 0), bgc=(0.25, 1.0, 0.4))
    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


# Apply creases
def applyCrease(creaseValue, custom, *args):
    cv = 0
    if custom == 1:
        cv = mc.floatField(creaseValue, q=1, v=1)
    else:
        cv = creaseValue
    sel = mc.ls(sl=True, fl=True)
    for e in sel:
        try:
            mc.polyCrease(e, ch=True, value=cv, vertexValue=0)
        except Exception:
            mc.warning("At least one invalid element is selected. Select edges only.")
            continue


# Select edges with specific crease value, or edges that are creased.
# From https://github.com/JakobJK/creaseEdges/blob/master/creaseEdges.py
def selectCrease(field_creaseValue, useCustom, *args):
    """ Select edges matching a specific crease value """
    sel = mc.ls(sl=True, l=True)

    if sel:
        edgeCollection = mc.polyListComponentConversion(sel, te=True)
        edges = mc.filterExpand(edgeCollection, sm=32, expand=True)
        creaseValue = mc.floatField(field_creaseValue, q=1, v=1)

        creasedEdges = []

        for edge in edges:
            edgeValue = mc.polyCrease(edge, query=True, value=True)
            if useCustom == 0:
                if edgeValue[0] > 0:
                    creasedEdges.append(edge)
            else:
                if edgeValue[0] == creaseValue:
                    creasedEdges.append(edge)
        mc.select(creasedEdges)
    else:
        mc.warning("Invalid selection. Select object(s) for crease evaluation only.")


def run(*args):
    createUI('LX Crease Utility')
