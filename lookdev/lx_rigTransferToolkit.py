import maya.cmds as mc
import functools
from functools import partial


# GUI
def createUI(pWindowTitle):

    windowID = 'rigTransferToolkitGUI'
    
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    
    mc.window( windowID,title=pWindowTitle,sizeable=False,resizeToFitChildren=True)
    mc.window( windowID,edit=True, width=475,height=50)
    
    singleLayout = mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,450) ], cal=[ (1, 'left') ], cs=[ (1, 25)] )
    mc.separator( h=20, style='none', p=singleLayout)

    # UV Transfer Tool
    mc.text("Copy UVs from first mesh selected to second, preserving rigging.", p=singleLayout)
    mc.separator( h=7, style='none', p=singleLayout)
    double_layout = mc.rowColumnLayout(numberOfColumns=2,
                            columnWidth=[(1, 90), (2, 325)], cal=[ (1, 'center'), (2, 'center') ], p=singleLayout)
    uvTransfer_addToSet = mc.checkBox(l='Add to layer ', v=1, p=double_layout)
    mc.button(label='UV Rig Transfer', command=partial(uvRigTransfer, uvTransfer_addToSet), p=double_layout)
    mc.separator(h=20, style='none', p=double_layout)
    mc.separator(h=25, style='none', p=double_layout)

    # Select Rig Shader
    singleLayout1 = mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,300) ], cal=[ (1, 'center') ], p=singleLayout )
    mc.button(label='Select surface shader of mesh', command=partial(selectRigShader), p=singleLayout1)
    mc.separator(h=30, style='none', p=singleLayout1)

    # Material Assign Tool
    singleLayout2 = mc.rowColumnLayout( numberOfColumns=1, columnWidth=[ (1,450) ], cal=[ (1, 'left') ], p=singleLayout )
    mc.text("Copy material assignment from first selected to second.", p=singleLayout2)
    mc.separator( h=7, style='none', p=singleLayout2)
    double_layout2 = mc.rowColumnLayout(numberOfColumns=2,
                            columnWidth=[(1, 150), (2, 265)], cal=[ (1, 'center'), (2, 'center') ], p=singleLayout2)
    transferArnoldAttrs = mc.checkBox(l='Transfer Arnold Attrs ', v=1, p=double_layout2)
    mc.button(label='Material transfer', command=partial(assignShaderFromFirstSelected, transferArnoldAttrs), p=double_layout2)
    mc.separator(h=20, style='none', p=double_layout2)
    mc.separator(h=20, style='none', p=double_layout2)
    # mc.button(label='2. Disconnect all cache inputs', p=singleLayout, command =
    #                 partial(disconnectAllCache) )
    # mc.separator(h=10, style='none', p=singleLayout)

    # mc.button(label='3. Unlock transform node attributes', p=singleLayout, command =
    #                 partial(unlockAll) )
    # mc.separator(h=10, style='none', p=singleLayout)
    mc.showWindow()


# Try to transfer UVs to rigged mesh, from a selected regular mesh. 1 to 1, not multiple sel
def uvRigTransfer(addToSet, *args):
    sel = mc.ls(sl=1, type='transform')
    if not sel:
        mc.warning("Select a source and target mesh(es).")
        return
    if len(sel)!=2:
        mc.warning("Select two objects.")
        return

    addToSet = mc.checkBox(addToSet, q=True,v=True)

    # Get source mesh shape and target meshOrig shape
    source = None
    target = None
    try:
        source = mc.listRelatives(sel[0], c=1, f=1, typ='mesh')[0]
        for s in mc.listRelatives(sel[1], c=1, f=1, typ='mesh'):
            if 'ShapeOrig' in s:
                target = s
                break
        if not target: raise TypeError
    except TypeError:
        mc.error('Error finding a meshShape in one of your selections.')
        return
    if source is None or target is None:
        mc.error('Error finding a meshShape in one of your selections.')
        return

    # Check for matching topology
    sourceInfo = mc.polyEvaluate(source, v=1, f=1, e=1, fmt=1)
    targetInfo = mc.polyEvaluate(target, v=1, f=1, e=1, fmt=1)

    # CURRENTLY DOESN'T WORK, polyCompare seems not to respect flags
    # topoMatch = mc.polyCompare(source, target, v=False, e=False, fd=True,
    #                            uv=False, iuv=False, c=False, ic=False, un=False) currently doesn't respect flags?
    #uvMatch = mc.polyCompare(source, target, v=0, e=0, fd=0, uv=1, iuv=1, c=0, ic=0, un=0) doesn't currently work
    # print('source: '+sourceInfo)
    # print('target: '+targetInfo)
    # print('topoMatch: '+str(topoMatch) )
    # if uvMatch==0:
    #     mc.warning("UVs already match, aborting...")
    #     return
    
    if not sourceInfo == targetInfo:
        mc.warning("Polycount doesn't match between the objects.")
        return
    
    # CURRENTLY DOESN'T WORK / PROBABLY WOULD NEED OM/OM2
    # if not topoMatch==0:
    #     mc.warning("Topology doesn't match between the objects.")
    #     return

    # Transfer UVs
    try:
        mc.setAttr('{}.intermediateObject'.format(target), 0)
        mc.transferAttributes(source, target, uvs=2, spa=5,
                pos=0, nml=0, col=0, sm=3)
        mc.delete(target, ch=True)
        mc.setAttr('{}.intermediateObject'.format(target), 1)
        print("Transferred uvs from {0} to {1}".format(source, target))
        mc.warning("Sucessfully transferred UVs.")
    except Exception as ex:
        mc.error("Error transferring UVs. See Script Editor.")
        mc.print("Error transferring UVs:\n   {0}-{1}".format(type(ex).__name__, ex) )
        return

    # Add to display layer if it is an option
    if addToSet:
        targetParents = mc.listRelatives(target, f=1, p=1, ni=1, typ='transform')
        if targetParents: mc.select(targetParents[0], r=1)
        else:
            mc.warning("Could not add to display layer because no parent was found.")
            return
        
        displayLayers = mc.ls(typ='displayLayer') # Add to existing one if exists
        targetLayer = [layer for layer in displayLayers if layer=='uvTransferLayer']
        if targetLayer:
            targetLayer = targetLayer[0]
            mc.editDisplayLayerMembers(targetLayer, targetParents[0])
        
        else: # Make new one
            targetLayer = mc.createDisplayLayer(name='uvTransferLayer')
        
        mc.setAttr('{}.color'.format(targetLayer), 6)
        mc.select(sel, r=1)


# Select the surfaceShader from the selected rigged mesh
def selectRigShader(*args):
    selected = mc.ls(dag=1, o=1, s=1, sl=1)
    if not selected:
        mc.error('Did not select a valid mesh.')
    
    try:
        driverShapeSelected = selected[0]
        shadingGrps = mc.listConnections(driverShapeSelected,type='shadingEngine')

        mc.select(cl=1)
        for sg in shadingGrps:
            shader = mc.listConnections('{}.surfaceShader'.format(sg))
            if shader: mc.select(shader, add=True)
            
    except Exception as ex:
        mc.error('Could not find a valid surfaceShader for selected mesh.')
        print(type(ex).__name__, ex)


# Copy shader assignments from first selected object to second
def assignShaderFromFirstSelected(transferArnoldAttrs, *args):
    sel = mc.ls(sl=1, l=1, type='transform')
    if not sel:
        mc.warning("Select a source and target mesh(es).")
        return
    if len(sel)!=2:
        mc.warning("Select two objects.")
        return
    
    # Get source mesh shape and targets
    source = None
    target = None
    try:
        meshRelatives = mc.listRelatives(sel[0], c=1, f=1, typ='mesh')[0]
        source = mc.listRelatives(sel[0], c=1, f=1, typ='mesh')[0]
        target = mc.listRelatives(sel[1], c=1, f=1, typ='mesh')
        if not target: raise TypeError
    except Exception as ex:
        mc.error('Error finding a meshShape in one of your selections.')
        print('Error: {}'.format(type(ex).__name__, ex) )
        return
    if source is None or target is None:
        mc.error('Error finding a meshShape in one of your selections.')
        return

    # Transfer arnold attributes
    transferArnoldAttrs = mc.checkBox(transferArnoldAttrs, q=1, v=1)
    aiTransfers = 0
    if transferArnoldAttrs:
        allAttrs = mc.listAttr(source)
        valid_attrs = {}
        renderAttrs = ('primaryVisibility', 'castsShadows')

        # Get valid attrs and add to valid_attrs dict
        for attr in allAttrs:
            for tag in renderAttrs:
                if not tag in attr: break
                try:
                    attr_value = mc.getAttr('{0}.{1}'.format(source, attr) )
                    valid_attrs[attr] = attr_value
                except Exception as ex:
                    print('Error copying attr {0}:\n    {1}-{2}'.format(attr, type(ex).__name__, ex) )
                    pass
                    
            if attr.startswith('ai'):
                try:
                    attr_value = mc.getAttr('{0}.{1}'.format(source, attr) )
                    valid_attrs[attr] = attr_value
                except Exception as ex:
                    print('Error copying attr {0}:\n    {1}-{2}'.format(attr, type(ex).__name__, ex) )
                    pass

        # Copy attrs to target meshes
        for attr in valid_attrs:
            value = valid_attrs.get(attr)
            if not value: continue

            for targetMesh in target:
                try:
                    mc.setAttr('{0}.{1}'.format(targetMesh, attr), value)
                    print('Copied aiAttrs to {}'.format(targetMesh))
                    aiTransfers += 1
                except Exception as ex:
                    print('Could not copy attr {}, skipping.'.format(attr))
                    continue

    # Assign material
    try:
        shadingGrp = mc.listConnections(source, type='shadingEngine')[0]
        mc.sets(target,forceElement=shadingGrp)
    except Exception as ex:
        mc.error('Error assigning material from {0} to {1}'.format(source, target))
        print('Error: {}'.format(type(ex).__name__, ex) )
    else:
        print("Copied material assignments from {0} to {1}".format(source, target))
        mc.warning("Sucessfully transferred material assignments; transferred {} aiAttrs".format( str(aiTransfers) ) )


createUI("Rig Transfer Toolkit")