# Duplicate a shading network in a clean way with a few basic options.
# Alan Yang 06.29.22

from functools import partial
import maya.cmds as mc


# Init GUI
def create_gui(debug=False):

    # Init window
    windowID = 'lxduplicateShaderGUI'
    if mc.window(windowID, exists=1):
        mc.deleteUI(windowID)
    mc.window(windowID, title='LX Duplicate Shaders', width=1, height=1, sizeable=1, resizeToFitChildren=1)

    # Set CSS text styles
    general_style = "font-size:medium; font-family:'Segoe UI', system-ui, sans-serif; font-weight:bold; color: #AEB6BF"

    # Init form tab layout
    main_form = mc.rowColumnLayout(numberOfColumns=1)

    # ---------------------------------------- #
    # ---------------------------------------- #
    # ---------------------------------------- #
    # Main Tab

    # General info
    mc.separator(h=5, style='none', p=main_form)
    make_sphere_tag = mc.checkBox(l='Make dummy sphere', v=1, p=main_form)
    mc.separator(h=25, style='none', p=main_form)

    # Material name entry
    double_layout = mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 50), (2, 175)], p=main_form)
    mc.text(label_style('find: ', general_style), align="left", p=double_layout)
    source_tag_field = mc.textField(ed=True, text='', fn="boldLabelFont", p=double_layout)
    mc.separator(h=10, style='none', p=double_layout)
    mc.separator(h=10, style='none', p=double_layout)
    mc.text(label_style('replace: ', general_style), align="left", p=double_layout)
    target_tag_field = mc.textField(ed=True, text='', fn="boldLabelFont", p=double_layout)
    mc.separator(h=15, style='none', p=double_layout)
    mc.separator(h=15, style='none', p=double_layout)

    main_layout = mc.rowColumnLayout(
        numberOfColumns=3,
        columnWidth=[(1, 25), (2, 200), (3, 50)],
        p=main_form)
    script_button(
        duplicate_shader, 'Duplicate Shader', 'green', main_layout,
        'Shaded.png',
        'Click the button to duplicate the selected shading network. Make sure you are selecting a shadingEngine.',
        source_tag_field, target_tag_field, make_sphere_tag)

    mc.showWindow()


# Label CSS for GUI
def label_style(value, style):
    return '<span style="{0}">{1}</span>'.format(style, value)


# Simple function to standardize some boilerplate code for maya buttons meant
# for calling external scripts in ptmk_scripts
def script_button(function, label, color, parent, image_path='toolSettings.png',
                  help='No documentation has been provided for this tool', *args):
    button_colors = {
        'grey': (0.5, 0.5, 0.5),
        'green': (0.545, 0.788, 0.309),
        'blue': (0.309, 0.458, 0.788),
        'orange': (0.788, 0.596, 0.309),
        'red': (0.835, 0.349, 0.345)
    }
    mc.image(image=image_path)
    mc.button(
        l=label,
        command=partial(function, *args),
        al='left', bgc=button_colors.get(color, (0.5, 0.5, 0.5)), p=parent)
    mc.iconTextButton(
        image1='info.png',
        command=lambda *args: mc.confirmDialog(title=label + ' help', message=help, button='OK'))


# Get valid shading nodes and return them as a tuple given a list of Maya nodes.
def get_shader_nodes(node_list):
    sg = None
    mtl = None
    vp = None
    for node in node_list:
        type = mc.nodeType(node)
        if type == 'shadingEngine':
            sg = node
            break
    if sg:
        for node in mc.listConnections(sg, d=0):
            type = mc.nodeType(node)
            if 'ai' in type:
                mtl = node
            elif any(vp in type for vp in ('lambert', 'blinn', 'phong', 'surfaceShader')):
                vp = node
    return (sg, mtl, vp)


# Duplicate an input shading network with a clean way with name replacement.
# Optionally create a dummy shader to assign to.
def duplicate_shader(
        input_tag,
        output_tag,
        make_sphere,
        debug=False,
        *args):

    # get shader nodes of selected network
    scene_sel = mc.ls(sl=1, l=1, dag=0)
    old_nodes = get_shader_nodes(scene_sel)
    if not old_nodes[0]:
        mc.error('No shading group selected.')

    # duplicate network and get new nodes
    new_network = mc.duplicate(old_nodes[0], ic=0, rc=1, un=1)
    new_nodes = get_shader_nodes(new_network)

    # rename new nodes to replace input_tag with output_tag
    renamed_nodes = []
    name_tags = (mc.textField(input_tag, q=1, tx=1), mc.textField(output_tag, q=1, tx=1))
    for i, node in enumerate(new_nodes):
        if node is None or old_nodes[i] is None:
            continue
        else:
            try:
                renamed_nodes.append(mc.rename(node, old_nodes[i].replace(name_tags[0], name_tags[1])))
            except IndexError:
                print('Index error for renaming ' + node + ' at index ' + str(i))

    # debug print
    if debug:
        print('Old nodes: ', old_nodes)
        print('New nodes: ', new_nodes)
        print('Renamed nodes: ', renamed_nodes)

    # Make dummy sphere for shader
    if mc.checkBox(make_sphere, q=1, v=1):
        dummy_sphere = mc.sphere(name=renamed_nodes[0] + '_shader', po=1)
        mc.sets(dummy_sphere, edit=True, forceElement=renamed_nodes[0])
        mc.warning('Shader duplicated and assigned to ' + str(dummy_sphere))
        mc.select(dummy_sphere)

    # If dummy sphere option is off select the shading group.
    else:
        mc.warning('Shader duplicated: ' + renamed_nodes)
        mc.select(renamed_nodes[0])


def run(*args):
    create_gui()

