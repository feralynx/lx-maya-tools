# Simple GUI utility for adding Arnold Subdivision attributes
# Alan Yang 06.29.2022

from functools import partial

import maya.cmds as mc
import pymel.core as pmc


# GUI
def createUI(pWindowTitle):

    windowID = 'lxArnoldSubdivs'
    
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    
    mc.window( windowID,title=pWindowTitle,sizeable=False,resizeToFitChildren=True)
    mc.window( windowID,edit=True, width=300,h=400)
    
    # set styles
    title_style = "font-size:20px; font-family:Corbel; font-weight:600; color: #AED6F1"
    general_style = "font-size:14px; font-family:Corbel; font-weight:600; color: #AEB6BF"
    red_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #F5B7B1"
    white_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #FDEBD0"
    
    
    # General info
    mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,450) ] )
    mc.text(label_style("Select objects to add Arnold subdiv settings to.",title_style),al='left')
    mc.separator( h=20, style='none')
    mc.text(label_style("Does not work if you have non-unique names.",general_style),al='left')
    mc.separator( h=30, style='none')
    
    # Subdiv settings
    mc.text(label_style('Smoothing type',red_warning_style),align="left")
    mc.separator( h=5, style='none')
    subdiv_type = mc.radioCollection()
    subdiv_type_catclark = mc.radioButton(label='catclark')
    subdiv_type_linear = mc.radioButton(label='linear')
    subdiv_type = mc.radioCollection(subdiv_type,edit=True,select=subdiv_type_catclark)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text(label_style('Subdiv iterations',red_warning_style),align="left")
    mc.separator( h=5, style='none')
    subdiv_iterations = mc.intField(ed=True, step=1, minValue=0, maxValue=10, value=2)
    mc.separator( h=5, style='none')
    autoSmooth = mc.checkBox(l='Auto set subdiv level from viewport smoothing', v=0)
    mc.separator( h=5, style='none')
    autoSubdPrv = mc.checkBox(l='Preview subd wireframe if viewport smoothed', v=1)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text(label_style('Adaptive error',red_warning_style),align="left")
    mc.separator( h=5, style='none')
    adaptive_error = mc.floatField(ed=True, minValue=0, maxValue=10, value=2)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.text(label_style('UV smoothing',red_warning_style),align="left")
    mc.separator( h=5, style='none')
    uv_smoothing = mc.radioCollection()
    uv_smoothing_pinBorders = mc.radioButton(label='pin_borders')
    uv_smoothing_pinCorners = mc.radioButton(label='pin_corners')
    uv_smoothing_linear = mc.radioButton(label='linear')
    uv_smoothing = mc.radioCollection(uv_smoothing,edit=True,select=uv_smoothing_pinBorders)
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.separator( h=10, style='none')
    mc.button(label='Apply subdivision settings', command=partial(apply,subdiv_type,subdiv_iterations,adaptive_error,uv_smoothing,autoSmooth,autoSubdPrv) )
    mc.separator( h=10, style='none')
    
    mc.showWindow()

    
    
    
# label CSS for GUI
def label_style (value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)
    
    
    
    
#recursively find shapes underneath selected DAG object    
def recursShape(s):
    relDAG = mc.listRelatives(s,pa=True)
    
    if(relDAG):
        shapesList = []
        for r in relDAG:
            if(mc.nodeType(r)=='mesh'):
                shapesList.append(r)
            else:
                shapesList.append(recursShape(r))
        return shapesList
    
    # the selected node is a shape node
    elif(mc.nodeType(s)=='mesh'):
        return s
    # this is a bottom level node and is not a shape node, set a flag to ignore subdiv
    else:
        return 'rec__null__'

        
        
        
#flatten a list recursively
def flatList(l, listAll):
    for i in l:
        if isinstance(i,list):
            flatList(i,listAll)
        else:
            listAll.append(i)
    
    
    
# apply subdivision settings
def apply(subdiv_type, subdiv_iterations, adaptive_error, uv_smoothing, autoSmooth, autoSubdPrv, *args):

    v_subdiv_type_radioCol = mc.radioCollection(subdiv_type,query=True,sl=True)
    v_subdiv_type = mc.radioButton(v_subdiv_type_radioCol,query=True,label=True)
    
    v_subdiv_iterations = mc.intField(subdiv_iterations,query=True,v=True)
    
    v_autoSmooth = mc.checkBox(autoSmooth,query=True,v=True)
    v_autoSubdPrv = mc.checkBox(autoSubdPrv,query=True,v=True)
    
    v_adaptive_error = mc.floatField(adaptive_error,query=True,v=True)
    
    v_uv_smoothing_radioCol = mc.radioCollection(uv_smoothing,query=True,sl=True)
    v_uv_smoothing = mc.radioButton(v_uv_smoothing_radioCol,query=True,label=True)
    
    print("Setting "+v_subdiv_type+" at iterations "+str(v_subdiv_iterations)+" with adaptive error of "+str(v_adaptive_error)+" and uv smoothing type of "+v_uv_smoothing)
    
    
    sel = mc.ls(sl=1)
    
    if sel:
        recShapes = []
        
        
        #recursively find all shapes under selected
        for obj in sel:
            r = recursShape(obj)
            recShapes.append(r)

        finalShapes= []
        flatList(recShapes,finalShapes)
        
        validity = 0
        
        #set subdivs
        for obj in finalShapes:
            if (obj!='rec__null__'):
                validity = 1
                
                #smooth mesh preview settings
                mc.setAttr(obj+".useSmoothPreviewForRender",0)
                mc.setAttr(obj+".displaySubdComps",v_autoSubdPrv)
                
                #subdiv type
                if(v_subdiv_type=='catclark'):
                    mc.setAttr(obj+".aiSubdivType",1)
                elif(v_subdiv_type=='linear'):
                    mc.setAttr(obj+".aiSubdivType",2)
                
                #uv smooth type
                if(v_uv_smoothing=='pin_borders'):
                    mc.setAttr(obj+".aiSubdivUvSmoothing",1)
                elif(v_uv_smoothing=='pin_corners'):
                    mc.setAttr(obj+".aiSubdivUvSmoothing",0)
                elif(v_uv_smoothing=='linear'):
                    mc.setAttr(obj+".aiSubdivUvSmoothing",2)
                    
                #subdiv iteration level
                if(v_autoSmooth==1 and mc.getAttr(obj+'.displaySmoothMesh')==2):
                    v_subdiv_iterations = mc.getAttr(obj+'.smoothLevel')
                mc.setAttr(obj+".aiSubdivIterations",v_subdiv_iterations)
                    
                mc.setAttr(obj+".aiSubdivPixelError",v_adaptive_error)
        
        if (validity == 0):
            mc.error("No valid shapes selected.")
        else:
            mc.warning("Subdivs applied.")
     
    else:
        mc.error("Nothing selected.")


def run(*args):
    createUI('LX Arnold Subdivs')
