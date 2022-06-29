# Simple GUI utility for dealing with polygonal selection constraints for cleanup and modeling purposes.
# Alan Yang 06.29.22

import maya.cmds as mc
from functools import partial


# GUI
def createUI(pWindowTitle):

    windowID = 'lx_selectionUtility_Window'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, resizeToFitChildren=True)
    mc.window(windowID, edit=True, width=200)

    # set styles
    # title_style = "font-size:20px; font-family:Corbel; font-weight:600; color: #AED6F1"
    red_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #F5B7B1"
    general_style = "font-size:13px; font-family:Corbel; font-weight:400; color: #AEB6BF"
    # info_style = "font-size:12px; font-family:Corbel; font-weight:4; color: #FDEBD0"

    form = mc.formLayout()
    tabs = mc.tabLayout(innerMarginWidth=5, innerMarginHeight=5, p=form)

    # Angle selection
    angleLayout = mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200)], p=tabs)
    mc.text(label_style('Normal Angle', red_warning_style), align="left", p=angleLayout)
    mc.separator(h=5, style='none', p=angleLayout)
    angleLayoutSub = mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 65)], p=angleLayout)
    mc.text(label_style('Input Angle', general_style), align="left", p=angleLayoutSub)
    angle_field = mc.floatField(ed=True, minValue=0, maxValue=360, value=60.0, p=angleLayoutSub)
    mc.text(label_style('Tolerance', general_style), align="left", p=angleLayoutSub)
    angleWidth_field = mc.floatField(ed=True, minValue=0, maxValue=360, value=30.0, p=angleLayoutSub)
    mc.button(label='Select', command=partial(angleSelect, angle_field, angleWidth_field), bgc=(0.7, 1.0, 0.7), p=angleLayout)

    # Hard edge selection
    hardEdgeLayout = mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200)], p=tabs)
    mc.text(label_style('Edge Hardness', red_warning_style), align="left", p=hardEdgeLayout)
    mc.separator(h=5, style='none', p=hardEdgeLayout)
    mc.button(label='Select Hard', command=partial(hardSelect, 1), bgc=(0.7, 1.0, 0.7), p=hardEdgeLayout)
    mc.button(label='Select Soft', command=partial(hardSelect, 0), bgc=(1.0, 0.7, 0.85), p=hardEdgeLayout)

    mc.tabLayout(tabs, e=1, tabLabel=((angleLayout, 'Angle'), (hardEdgeLayout, 'Hard Edges')))
    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


# Select edges by input angle and width of selection
def angleSelect(angle_field, angleWidth_field, *args):
    origSel = mc.ls(sl=1, l=1)

    if origSel:
        edgeCollection = mc.polyListComponentConversion(origSel, te=1)
        mc.filterExpand(edgeCollection, sm=32, expand=1)

        # Select edges that satisfy angle criteria
        inputAng = mc.floatField(angle_field, q=1, v=1)
        angWidth = mc.floatField(angleWidth_field, q=1, v=1)
        minAng = inputAng - (angWidth/2)
        maxAng = inputAng + (angWidth/2)
        mc.polySelectConstraint(mode=3, type=0x8000, a=1, ab=(minAng, maxAng))

        # Select result and turn off selection constraint.
        result = mc.ls(sl=True) or origSel
        mc.polySelectConstraint(a=0)
        mc.select(result)

    else:
        mc.warning('No valid geometry selected.')


# Select edges by hardness
def hardSelect(hard, *args):
    origSel = mc.ls(sl=1, l=1)

    if origSel:
        edgeCollection = mc.polyListComponentConversion(origSel, te=1)
        mc.filterExpand(edgeCollection, sm=32, expand=1)

        # Select hard or soft edges
        if hard == 1:
            mc.polySelectConstraint(mode=3, type=0x8000, sm=1)
        else:
            mc.polySelectConstraint(mode=3, type=0x8000, sm=2)

        # Select result and turn off selection constraint.
        result = mc.ls(sl=True) or origSel
        mc.polySelectConstraint(sm=0)
        mc.select(result)

    else:
        mc.warning('No valid geometry selected.')


def run(*args):
    createUI('LX Selection Utility')
