# Chip off mesh of each uv shell of selected object.
# Alan Yang 06.29.22

import maya.api.OpenMaya as om2
import maya.cmds as mc

from collections import defaultdict


# GUI
def createUI(pWindowTitle):

    windowID = 'lxSeparateByUVShells'
    if mc.window(windowID, exists=True):
        mc.deleteUI(windowID)
    mc.window(windowID, title=pWindowTitle, sizeable=True, resizeToFitChildren=True)
    mc.window(windowID, edit=True, width=200, h=200)

    # set styles
    # title_style = "font-size:20px; font-family:Corbel; font-weight:600; color: #AED6F1"
    red_warning_style = "font-size:16px; font-family:Corbel; font-weight:600; color: #F5B7B1"
    general_style = "font-size:13px; font-family:Corbel; font-weight:400; color: #AEB6BF"
    # white_warning_style = "font-size:18px; font-family:Corbel; font-weight:600; color: #FDEBD0"
    mc.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200)])
    # Apply crease presets
    mc.text(label_style('WARNING: Can be slow on big meshes.', red_warning_style), align="left")
    mc.separator(h=5, style='none')
    mc.button(label='Run', command=lambda x: main(), bgc=(1.0, 0.3, 0.3))

    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


# Return a nested list of format [[uvs in shell1], [uv in shell2] ....]
def get_uv_shells(shape):
    uv_set = mc.polyUVSet(shape, q=1, allUVSets=True)[0]  # Currently only operates on primary uv set on mesh

    # API boilerplate
    sel = om2.MSelectionList()
    sel.add(shape)
    dagPath = sel.getDagPath(0)
    dagPath.extendToShape()
    mesh = mc.ls(dagPath.fullPathName(), l=1, o=1)[0]
    mesh = mesh.rsplit('|', 1)[0]
    fnMesh = om2.MFnMesh(dagPath)

    # Get uv shell ids
    uvCount, uvShellArray = fnMesh.getUvShellsIds(uv_set)

    # Iter through all uv shells and append to list in a format that mayapy commands understand
    uvShells = defaultdict(list)
    for i, shellId in enumerate(uvShellArray):
        uv = '{0}.map[{1}]'.format(mesh, i)
        uvShells[shellId].append(uv)

    return uvShells.values()


def main():
    scene_selection = mc.ls(sl=1, typ='transform')

    if not scene_selection:
        mc.error('Select a mesh (transform node).')
        return

    scene_mesh = mc.listRelatives(scene_selection[0], c=1, s=1)

    if not scene_mesh:
        mc.error('No valid shape nodes found in selection.')
        return

    scene_mesh = scene_mesh[0]
    uv_shell_list = get_uv_shells(scene_mesh)

    if not uv_shell_list:
        mc.error('No valid UVs in default map1 set.')
        return

    # Iterate through uv shell list
    orig_mesh = scene_selection[0].encode('ascii', 'ignore')
    shells_parent = mc.createNode('transform')
    shells_parent = mc.rename(shells_parent, orig_mesh + '_shells_grp')
    for i, shell in enumerate(uv_shell_list):
        dupe = mc.duplicate(scene_mesh)
        shell_iter = []
        dupe_mesh = dupe[0].encode('ascii', 'ignore')

        # Replace original shell list with name of duplicated mesh
        for uv in shell:
            if orig_mesh in uv:
                shell_iter.append(uv.replace(orig_mesh, dupe_mesh))

        # Convert selection to faces, invert selection, delete
        shell_faces = mc.polyListComponentConversion(shell_iter, tf=1)
        mc.select(mc.polyListComponentConversion(dupe, tf=1))
        mc.select(shell_faces, d=1)
        mc.delete()

        # Rename and parent
        dupe = mc.rename(dupe, orig_mesh + '_shell_{:02d}'.format(i))
        mc.parent(dupe, shells_parent)


def run(*args):
    createUI('LX Separate By UV Shells')
