# delete all Arnold Nodes from scene and then run delete unused nodes afterwards for cleanup

import maya.cmds as mc


def removeAllArnoldNodes(verbose=True, removeDisplacement=True):
    aiNodeTypes = mc.pluginInfo("mtoa", q=1, dependNode=1)
    if removeDisplacement: aiNodeTypes.append('displacementShader')

    count = 0
    for nodeType in aiNodeTypes:
        nodes = mc.ls(type=nodeType, rn=False)
        if not nodes:
            print("No nodes of type {}".format(nodeType))
            continue
        
        try:
            mc.delete(nodes)
            count += len(nodes)
            print("Deleted: " + str(nodes))
        except Exception as ex:
            print("Could not delete nodes of type {0}.\n   {1}".format(nodeType, ex))
            continue

    mc.confirmDialog(message="Deleted {} nodes.".format( str(count) ), button="OK")

removeAllArnoldNodes(True, True)