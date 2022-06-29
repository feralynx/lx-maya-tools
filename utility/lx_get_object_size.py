# Return average bounding box length of object based on object-space bbox.
# Alan Yang 06.29.22

from maya import OpenMaya as om
from maya import cmds


def run(selection, *args):

    # Check if selection exists in scene and get OM path
    selectionList = om.MSelectionList()
    if not cmds.objExists(selection[0]):
        raise RuntimeError('Object does not exist: {}'.format(selection[0]))
        return

    om.MGlobal.getSelectionListByName(selection[0], selectionList)
    selectedPath = om.MDagPath()
    selectionList.getDagPath(0, selectedPath)

    # Get the transformation matrix of the selected object.
    transform = om.MFnTransform(selectedPath)
    m = transform.transformationMatrix()

    # Get the shape directly below the selected transform.
    selectedPath.extendToShape()
    fnMesh = om.MFnMesh(selectedPath)
    bounds = fnMesh.boundingBox()

    # Transform bbox by object matrix
    bbmin = bounds.min() * m
    bbmax = bounds.max() * m

    # Calculate dimensions of bbox
    dimension = [
        abs(bbmin.x - bbmax.x),
        abs(bbmin.y - bbmax.y),
        abs(bbmin.z - bbmax.z)]

    # Return average length of bbox side
    return (dimension[0] + dimension[1] + dimension[2])/3
