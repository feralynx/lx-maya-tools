# delete all Arnold Nodes from scene and then run delete unused nodes afterwards for cleanup

import maya.cmds as mc
import maya.mel as mel
from functools import partial

def deleteArnoldMats():
    scene_node_types = mc.ls(nt=True)
    for type in scene_node_types:
        if 'ai' not in type:
            continue
        arnold_nodes = mc.ls(type=type)
        if arnold_nodes:
            for node in arnold_nodes:
                try:
                    if not mc.referenceQuery(node, isNodeReferenced=True):
                        if mc.lockNode(node, lock=True):
                            mc.lockNode(node, lock=False)
                        mc.delete(node)
                        print('Deleted ' + node)
                except Exception as e:
                    print('Could not delete ' + node + ' -- ' + e.message)
                    pass
        mel.eval('MLdeleteUnused')


deleteArnoldMats()
