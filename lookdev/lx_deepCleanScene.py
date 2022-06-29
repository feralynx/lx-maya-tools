# Deep clean lookdev scene
# Alan Yang 06.29.22

import os
import traceback
from functools import partial

import maya.cmds as mc
import maya.mel as mel


# GUI
def createUI(pWindowTitle):

    windowID = 'aydeepCleanSceneUI'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, resizeToFitChildren=True)
    mc.window(windowID, edit=True, width=300)

    mc.rowColumnLayout(numberOfColumns=1)
    mc.button(label='Delete All History', command=partial(delete_history))
    mc.button(label='Delete Unused Nodes (Basic)', command=partial(delete_unused_nodes))
    mc.button(label='Delete Unused Nodes (Aggressive)', command=partial(delete_unused_nodes_aggressive))
    mc.button(label='Freeze All Transformations', command=partial(freeze_all_transforms))
    mc.button(label='Delete/import Non-Referenced Namespaces', command=partial(gtu_delete_namespaces))
    mc.button(label='Remove all References', command=partial(gtu_remove_references))
    mc.button(label='Unlock all Nodes', command=partial(unlock_all_nodes))
    mc.button(label='Select Non-Unique Names', command=partial(gtu_select_non_unique_objects))
    mc.showWindow()


def delete_history(*args):
    try:
        mel.eval('DeleteAllHistory')
        print('All scene history was deleted.')
    except Exception as e:
        print('Could not delete scene history: ' + str(e))


def delete_unused_nodes(*args):
    try:
        mel.eval('MLdeleteUnused')
        print('Deleted unused nodes.')
    except Exception as e:
        print('Could not delete unused nodes: ' + str(e))


def freeze_all_transforms(*args):
    all_transforms = mc.ls(type='transform')
    for node in all_transforms:
        try:
            if not mc.referenceQuery(node, isNodeReferenced=True):
                if mc.lockNode(node, lock=True):
                    mc.lockNode(node, lock=False)
                mc.makeIdentity(node, t=1, r=1, s=1, apply=True)
            print('Froze transforms on ' + node)
        except Exception as e:
            print('Could not freeze transforms: ' + node + ' -- ' + str(e))
            pass


def unlock_all_nodes(*args):
    all_nodes = mc.ls()
    all_nodes = mc.ls()
    for node in all_nodes:
        if not mc.referenceQuery(node, isNodeReferenced=True):
                mc.lockNode(node, lock=False)
                print('Unlocked ' + node)


# Delete/import all non-ref namespaces - From GT Tools https://github.com/TrevisanGMW/gt-tools
def gtu_delete_namespaces(*args):
    '''Deletes all namespaces in the scene'''
    function_name = 'GTU Delete All Namespaces'
    mc.undoInfo(openChunk=True, chunkName=function_name)
    try:
        default_namespaces = ['UI', 'shared']

        def num_children(namespace):
            '''Used as a sort key, this will sort namespaces by how many children they have.'''
            return namespace.count(':')

        namespaces = [namespace for namespace in mc.namespaceInfo(lon=True, r=True) if namespace not in default_namespaces]

        # Reverse List
        namespaces.sort(key=num_children, reverse=True) # So it does the children first

        print(namespaces)

        for namespace in namespaces:
            if namespace not in default_namespaces:
                mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')
    except Exception as e:
        mc.warning(str(e))
    finally:
        mc.undoInfo(closeChunk=True, chunkName=function_name)


# Remove all references - From GT Tools https://github.com/TrevisanGMW/gt-tools
def gtu_remove_references(*args):
    try:
        errors = ''
        refs = mc.ls(rf=True)
        for i in refs:
            try:
                r_file = mc.referenceQuery(i, f=True)
                mc.file(r_file, removeReference=True)
            except Exception as e:
                errors += str(e) + '(' + r_file + ')\n'
    except Exception:
        mc.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        mc.warning('Not all references were removed. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)


# Select objects with non-unique short names - From GT Tools https://github.com/TrevisanGMW/gt-tools
def gtu_select_non_unique_objects(*args):

    def get_short_name(obj):
        if obj == '':
            return ''
        split_path = obj.split('|')
        if len(split_path) >= 1:
            short_name = split_path[len(split_path)-1]
        return short_name

    all_transforms = mc.ls(type='transform')
    short_names = []
    non_unique_transforms = []
    for obj in all_transforms: # Get all Short Names
        short_names.append(get_short_name(obj))

    for obj in all_transforms:
        short_name = get_short_name(obj)
        if short_names.count(short_name) > 1:
            non_unique_transforms.append(obj)

    mc.select(non_unique_transforms, r=True)

    if len(non_unique_transforms) > 0:
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(len(non_unique_transforms)) + '</span> non-unique objects were selected.'
    else:
        message = 'All objects seem to have unique names in this scene.'
    mc.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


def delete_unused_nodes_aggressive(*args):
    try:
        # Run maya optionize scene command
        optimize_scene_options = [
            "nurbsSrfOption",
            "nurbsCrvOption",
            "unusedNurbsSrfOption",
            "deformerOption",
            "unusedSkinInfsOption",
            "poseOption",
            "clipOption",
            "expressionOption",
            "groupIDnOption",
            "animationCurveOption",
            "shaderOption",
            "cachedOption",
            "transformOption",
            "displayLayerOption",
            "renderLayerOption",
            "setsOption",
            "partitionOption",
            "locatorOption",
            "ptConOption",
            "pbOption",
            "snapshotOption",
            "unitConversionOption",
            "referencedOption",
            "brushOption",
            "unknownNodesOption",
            "shadingNetworksOption",
        ]
        for option in optimize_scene_options:
            mc.optionVar(iv=(option, 1))
        os.environ["MAYA_TESTING_CLEANUP"] = "1"
        try:
            mel.eval('OptimizeSceneOptions')
            mel.eval('hideOptionBox')
            mel.eval("performCleanUpScene")
        except Exception as e:
            print('Failed to run Maya Optimize Scene ' + str(e))
        del os.environ["MAYA_TESTING_CLEANUP"]

        # Delete unknown plugins
        oldplugins = mc.unknownPlugin(q=True, list=True)
        if oldplugins:
            for plugin in oldplugins:
                try:
                    mc.unknownPlugin(plugin, remove=True)
                    print('Removed {}.'.format(plugin))
                except Exception:
                    print('Remove failed {}.'.format(plugin))
                    pass

        # Delete Turtle nodes
        turtleNodes = mc.ls('Turtle*')
        if turtleNodes:
            for node in turtleNodes:
                try:
                    mc.lockNode(node, lock=False)
                    mc.delete(node)
                    print('Deleted ' + node)
                except Exception:
                    print('Failed to remove ' + node)
                    pass
            try:
                mc.unloadPlugin('Turtle.mll', f=True)
                print('Unloaded Turtle plugin.')
            except Exception:
                print('Could not unload Turtle.')
                pass

        # Delete bad node types for modeling
        bad_types = ('unknown', 'unknownDag', 'ExocortexAlembicXform', 'ExocortexAlembicPolyMeshDeform',
                     'ExocortexAlembicFile', 'ExocortexAlembicTimeControl', 'groupId',
                     'ngSkinLayerData', 'ngSkinLayerDisplay', 'blendColors', 'multiplyDivide',
                     'plusMinusAverage', 'pointEmitter', 'instancer', 'nucleus', 'nParticle',
                     'spring', 'particle', 'nRigid', 'nCloth', 'pfxHair', 'hairSystem', 'dynamicConstraint',
                     'joint', 'animCurveTA', 'animCurveTL', 'animCurveTU', 'animCurveTT')
        for type in bad_types:
            bad_nodes = mc.ls(type=type)
            if bad_nodes:
                for node in bad_nodes:
                    try:
                        if not mc.referenceQuery(node, isNodeReferenced=True):
                            mc.lockNode(node, lock=False)
                            mc.delete(node)
                            print('Deleted ' + node)
                    except Exception as e:
                        print('Could not delete ' + node + ' -- ' + str(e))
                        pass

        # Delete bad patterns
        bad_patterns = ('aiAOV', 'Orig', 'animBot', 'dof', 'dynController', 'art3dPaintLastPaintBrush',
                        'defaultFurGlobals', 'defaultStrokeGlobals', 'scene', 'ScriptNode', 'aTools',
                        'kingNurbs', 'Exocortex', 'ngSkinTools', 'defaultHardwareRenderGlobals',
                        'BlendUTIL', 'DivideUTIL', 'CondUTIL', 'MultiUTIL', 'AddUTIL', 'SubUTIL', 'MASH')
        for pat in bad_patterns:
            bad_nodes = mc.ls('*' + pat + '*')
            if bad_nodes:
                for node in bad_nodes:
                    try:
                        if not mc.referenceQuery(node, isNodeReferenced=True):
                            mc.lockNode(node, lock=False)
                            mc.delete(node)
                            print('Deleted ' + node)
                    except Exception as e:
                        print('Could not delete ' + node + ' -- ' + str(e))
                        pass

        print('Deleted unused nodes AGGRESSIVELY.')
    except Exception as e:
        print('Could not delete unused nodes aggressively: ' + str(e))
        print(traceback.format_exc())


def run(*args):
    createUI('LX Deep Clean Scene')
