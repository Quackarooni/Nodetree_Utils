from operator import ge
import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, IntProperty
import itertools
from pathlib import Path

def get_nodes(context):
    tree = context.space_data.node_tree
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree
    return tree.nodes

def fetch_user_preferences():
    ADD_ON_PATH = Path(__file__).parent.name
    return bpy.context.preferences.addons[ADD_ON_PATH].preferences

class deframe_nodes():
    def __init__(self, nodes):
        self.parent_dict = {}
        for node in nodes:
            if node.parent is not None:
                self.parent_dict[node] = node.parent
            node.parent = None
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for node, parent in self.parent_dict.items():
            node.parent = parent

class NodeUtilsBase:
    bl_label = "Nodeutils Baseclass"
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ("ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree")
        is_existing = space.node_tree is not None
        is_node_editor = space.type == 'NODE_EDITOR'
        is_valid = space.tree_type in valid_trees
        return all((is_existing, is_node_editor, is_valid))


class NODEUTILS_OT_SELECT_BY_TYPE(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Select By Type"
    bl_idname = "nd_utils.select_by_type"
    bl_description = "Select by specific node type"

    select_target: EnumProperty(name='select_target', items=(
        ('NODES', 'NODES', ''), ('REROUTES', 'REROUTES', ''), ('FRAMES', 'FRAMES', ''),))
    @classmethod
    def description(self, context, props):
        return f"Targets {props.select_target.lower()} for selection"

    def execute(self, context):
        prefs = fetch_user_preferences()
        selection_mode = context.window_manager.nd_utils_props.selection_mode
        nodes = get_nodes(context)
        selected_nodes = set(node for node in nodes if node.select)

        if self.select_target == 'NODES':
            def check_condition(node_type):
                return node_type not in ('REROUTE', 'FRAME')     
        elif self.select_target == 'REROUTES':
            def check_condition(node_type):
                return node_type == 'REROUTE'
        elif self.select_target == 'FRAMES':
            def check_condition(node_type):
                return node_type == 'FRAME'
        
        nodes_of_spec_type = set(node for node in nodes if check_condition(node.bl_static_type))
        
        if selection_mode == 'New':
            nodes_to_select = nodes_of_spec_type
        elif selection_mode == 'Add':
            nodes_to_select = selected_nodes.union(nodes_of_spec_type)
        elif selection_mode == 'Subtract':
            nodes_to_select = selected_nodes.difference(nodes_of_spec_type)
        elif selection_mode == 'Intersection':
            nodes_to_select = selected_nodes.intersection(nodes_of_spec_type)
        elif selection_mode == 'Invert':
            nodes_to_select = selected_nodes.symmetric_difference(nodes_of_spec_type)
        else:
            return {'CANCELLED'}

        if prefs.ignore_empty_selections:
            if (selection_mode == "New" or selection_mode == "Intersection") and not nodes_to_select:
                self.report({'INFO'}, f'No {self.select_target.lower()} found. Ignoring selection.')
                return {'CANCELLED'}
        will_selection_be_identical = nodes_to_select == selected_nodes
        if will_selection_be_identical:
            return {'CANCELLED'}

        for node in nodes:
            node.select = False
        for node in nodes_to_select:
            node.select = True

        return {'FINISHED'}


class NODEUTILS_OT_NORMALIZE_NODE_WIDTH(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Normalize Node Width"
    bl_idname = "nd_utils.normalize_node_width"
    bl_description = "Sets uniform width for selected nodes"

    normalize_type: EnumProperty(name='normalize_type', items=(
        ('MAX', 'MAX', ''), ('MIN', 'MIN', ''), ('AVERAGE', 'AVERAGE', ''),))
    desc_dict = {'MAX':'maximum','MIN':'minimum','AVERAGE':'average',}

    @classmethod
    def description(self, context, props):
        return f"Sets width to selected nodes according to their {self.desc_dict[props.normalize_type]}"

    def execute(self, context):
        prefs = fetch_user_preferences()
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type != 'FRAME' and node.bl_static_type != 'REROUTE'))
        if len(selected_nodes) <= 1:
            return {'CANCELLED'}

        width_init = (node.dimensions.x for node in selected_nodes)
        node_widths = set(width_init)if prefs.use_unique else tuple(width_init)

        if self.normalize_type == 'AVERAGE':
            width_to_set = sum(node_widths)/len(node_widths)
        else:
            width_to_set = min(node_widths) if self.normalize_type == 'MIN' else max(node_widths)

        if all(width_to_set == node.width for node in selected_nodes):
            return {'CANCELLED'}

        for node in selected_nodes:
            node.width = width_to_set
        return {'FINISHED'}


class NODEUTILS_OT_BATCH_LABEL(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Batch Label"
    bl_idname = "nd_utils.batch_label"
    bl_description = "Renames all selected nodes according to specified label"

    label: StringProperty(name='', default='')
  
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if tuple(node for node in get_nodes(context) if node.select):
            row.label(icon='NODE')
            row.prop(self, "label")
        else:
            row.label(icon='ERROR')
            row.label(text='No nodes selected')           

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if node.select)

        for node in selected_nodes:
            node.label = self.label

        self.label = ''
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

class NODEUTILS_OT_SET_WIDTH(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Set Node Width"
    bl_idname = "nd_utils.set_node_width"
    bl_description = "Resizes all selected nodes according to specified width"

    width: IntProperty(name='', default=30, min=30)
    last_resized_nodes = []
  
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if tuple(node for node in get_nodes(context) if node.select):
            row.label(icon='NODE')
            row.prop(self, "width")
        else:
            row.label(icon='ERROR')
            row.label(text='No nodes selected')           

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if node.select)
        for node in selected_nodes:
            node.width = self.width

        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

#Somewhat inspired by: https://github.com/valcohen/tidy_group_inputs
class NODEUTILS_OT_SET_COLOR(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Set Node Color"
    bl_idname = "nd_utils.set_node_color"
    bl_description = "Assigns specified color to all selected nodes."

    color_opmode: EnumProperty(name='color_opmode', items=(
        ('SET_COLOR', 'SET_COLOR', ''), ('CLEAR_COLOR', 'CLEAR_COLOR', ''),))

    @classmethod
    def description(self, context, props):
        if props.color_opmode == 'SET_COLOR':
            return "Sets specified custom color for all selected nodes"
        else:
            return "Resets custom color for all selected nodes"

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if node.select)
        old_status = tuple(node.use_custom_color for node in selected_nodes)
        custom_color = fetch_user_preferences().custom_color
        will_colors_be_identical = all(node.color == custom_color for node in selected_nodes)

        if self.color_opmode == 'SET_COLOR':
            for node in selected_nodes:
                node.use_custom_color = True
                node.color = custom_color
        elif self.color_opmode == 'CLEAR_COLOR':
            for node in selected_nodes:
                node.use_custom_color = False
                node.color = (0.608, 0.608, 0.608)
        
        new_status = tuple(node.use_custom_color for node in selected_nodes)
        if (old_status == new_status) and will_colors_be_identical:
            return {'CANCELLED'}
        return {'FINISHED'}


class NODEUTILS_OT_LABEL_REROUTES(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Label Reroutes"
    bl_idname = "nd_utils.label_reroutes"
    bl_description = "Labels selected reroutes based on their input/output"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}
  
    check_by: EnumProperty(name='check_by', items=(
        ('INPUT', 'INPUT', ''), ('OUTPUT', 'OUTPUT', ''),))

    @classmethod
    def description(self, context, props):
        if props.check_by == "INPUT":
            msg_end = "input"
        else:
            msg_end = f"most recently connected {props.check_by.lower()}"

        return f"Labels selected reroutes based on their {msg_end} link"

    def check_parent_label(self, node, level=0):
        if level >= 100:
            return ['RECURSION ERROR']
        for socket in node.inputs:
            if node.label != '' or len(socket.links) == 0 or not node.select:
                return node.label

            link = socket.links[0]
            if (link.from_node.bl_static_type != 'REROUTE'):
                return link.from_socket.name
            
            label = link.from_node.label
            if label != '':
                return label
            return self.check_parent_label(link.from_node, level=level+1)

    def check_child_label(self, node, level=0):
        if level >= 100:
            return ['RECURSION ERROR']
        for socket in node.outputs:
            if node.label != '' or len(socket.links) == 0 or not node.select:
                return node.label

            link = socket.links[-1]
            if (link.to_node.bl_static_type != 'REROUTE'):
                return link.to_socket.name
            
            label = link.to_node.label
            if label != '':
                return label
            return self.check_child_label(link.to_node, level=level+1)


    def execute(self, context):
        use_inputs = (self.check_by == "INPUT")

        init_reroutes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type == 'REROUTE'))
        reroutes = sorted(init_reroutes, key=lambda n: n.location.x, reverse=(not use_inputs))
        if not reroutes:
            return {'CANCELLED'}

        old_labels = [reroute.label for reroute in reroutes]
        new_labels = []
        for reroute in reroutes:
            if use_inputs:
                new_label = self.check_parent_label(reroute)
            else:
                new_label = self.check_child_label(reroute)

            if new_label == ['RECURSION ERROR']:
                self.report({'ERROR'}, "RECURSION_ERROR: Exceeded recursion limit. \nTry again with a smaller selection, or make sure input-to-output goes left-to-right.")
                return {'CANCELLED'}
            reroute.label = new_label
            new_labels.append(new_label)

        if (old_labels == new_labels):
            return {'CANCELLED'}
        return {'FINISHED'}


class NODEUTILS_OT_RECENTER_NODES(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Recenter Nodes"
    bl_idname = "nd_utils.recenter_nodes"
    bl_description = "Repositions nodetree such that its midpoint is at the origin"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        nodes = tuple(node for node in get_nodes(context))
        if not nodes:
            return {'CANCELLED'}

        with deframe_nodes(nodes):
            for index, node in enumerate(nodes):
                if index == 0:
                    most_left = node.location.x
                    most_right = node.location.x + node.dimensions.x
                    most_top = node.location.y
                    most_bottom = node.location.y + node.dimensions.y
                    continue
                
                most_left = min(most_left, node.location.x)
                most_right = max(most_right, node.location.x + node.dimensions.x)
                most_top = max(most_top, node.location.y)
                most_bottom = min(most_bottom, node.location.y + node.dimensions.y)

            midpoint_x = 0.5*(most_left + most_right)
            midpoint_y = 0.5*(most_top + most_bottom)

            if midpoint_x == 0 and midpoint_y == 0:
                return {'CANCELLED'}

            for node in nodes:
                node.location.x -= midpoint_x
                node.location.y -= midpoint_y

            return {'FINISHED'}

class NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Toggle Unused Sockets"
    bl_idname = "nd_utils.toggle_unused_sockets"
    bl_description = "Toggles the visibility of unconnected node sockets"
    bl_options = {'REGISTER'}

    sockets_to_hide: EnumProperty(name='sockets_to_hide', items=(
        ('INPUT', 'INPUT', ''), ('OUTPUT', 'OUTPUT', ''),))

    @classmethod
    def description(self, context, props):
        return f"Toggles the visibility of unconnected {props.sockets_to_hide.lower()} sockets"

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type != 'FRAME' and node.bl_static_type != 'REROUTE'))
        
        if self.sockets_to_hide == 'INPUT':
            all_sockets = itertools.chain.from_iterable(
                (socket for socket in node.inputs) for node in selected_nodes)
        else:
            all_sockets = itertools.chain.from_iterable(
                (socket for socket in node.outputs) for node in selected_nodes)

        unused_sockets = tuple(socket for socket in all_sockets if socket.enabled and not socket.is_linked)
        if len(unused_sockets) <= 0:
            return {'CANCELLED'}

        toggle_value = any(not socket.hide for socket in unused_sockets)
        for socket in unused_sockets:
            socket.hide = toggle_value
        return {'FINISHED'}

class NODEUTILS_OT_SWITCH_SELECT_TYPE(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Switch Select Type"
    bl_idname = "nd_utils.switch_select_type"
    bl_description = "Switches the select type according to specified option"
    bl_options = {'INTERNAL'}
    
    switch_mode: EnumProperty(name='sockets_to_hide', items=(
        ('SWITCH_TO_FIRST', 'SWITCH_TO_FIRST', ''), 
        ('SWITCH_TO_LAST', 'SWITCH_TO_LAST', ''), 
        ('CYCLE_UP', 'CYCLE_UP', ''), 
        ('CYCLE_DOWN', 'CYCLE_DOWN', ''),))

    def execute(self, context):
        selection_enum = context.window_manager.nd_utils_props
        enum_items = selection_enum.bl_rna.properties['selection_mode'].enum_items
        current_select_mode = selection_enum.selection_mode

        if not self.switch_mode.startswith('CYCLE'):
            if self.switch_mode == 'SWITCH_TO_FIRST':
                new_select_mode = enum_items[0].identifier
            elif self.switch_mode == 'SWITCH_TO_LAST':
                new_select_mode = enum_items[-1].identifier

            selection_enum.selection_mode = new_select_mode
            return {'FINISHED'}

        enum_dict = {}
        for item in enum_items:
            if item.identifier == current_select_mode:
                current_select_id = item.value
            enum_dict[item.value] = item.identifier

        if self.switch_mode == "CYCLE_UP":
            new_select_id = max(current_select_id - 1, 0)
        elif self.switch_mode == "CYCLE_DOWN":
            new_select_id = min(current_select_id + 1, len(enum_items) - 1)
            
        new_select_mode = enum_dict.get(new_select_id)
        selection_enum.selection_mode = new_select_mode
        return {'FINISHED'}

class NODEUTILS_OT_SWITCH_VIEWER_DOMAIN(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Switch Viewer Domain"
    bl_idname = "nd_utils.switch_viewer_domain"
    bl_description = "Updates the domain of Viewer Node in Geometry Nodes"
    bl_options = {'REGISTER'}

    switch_mode: EnumProperty(name='switch_mode', items=(
        ('SWITCH_TO_FIRST', 'SWITCH_TO_FIRST', ''), 
        ('SWITCH_TO_LAST', 'SWITCH_TO_LAST', ''), 
        ('CYCLE_UP', 'CYCLE_UP', ''), 
        ('CYCLE_DOWN', 'CYCLE_DOWN', ''),))

    @staticmethod
    def determine_source_geo(active_node):
        default_domain_list = ('AUTO', 'POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE', 'INSTANCE')

        if active_node.bl_static_type != "VIEWER" or active_node.select == False:
            return default_domain_list

        geometry_socket = active_node.inputs[0]
        if len(geometry_socket.links) == 0:
            return default_domain_list
        
        source_geo = geometry_socket.links[0].from_socket.name

        if source_geo == "Curve":
            return ('AUTO', 'POINT', 'CURVE', 'EDGE', 'FACE', 'CORNER', 'INSTANCE')
        elif source_geo == "Instances":
            return ('AUTO', 'INSTANCE', 'POINT', 'EDGE', 'FACE', 'CORNER', 'CURVE')
        else:
            return default_domain_list
        

    def execute(self, context):
        nodes = get_nodes(context)
        active_node = context.active_node

        domains = self.determine_source_geo(active_node)

        for node in nodes:
            if node.bl_static_type != "VIEWER":
                continue

            current_id = domains.index(node.domain)

            if not self.switch_mode.startswith('CYCLE'):
                if self.switch_mode == 'SWITCH_TO_FIRST':
                    new_id = 0
                elif self.switch_mode == 'SWITCH_TO_LAST':
                    new_id = -1

            if self.switch_mode == "CYCLE_UP":
                new_id = max(current_id - 1, 0)
            elif self.switch_mode == "CYCLE_DOWN":
                new_id = min(current_id + 1, len(domains) - 1)
            
            node.domain = domains[new_id]
                
        return {'FINISHED'}

class NODEUTILS_OT_PIE_MENU_SWITCH_VIEWER_DOMAIN(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Switch Viewer Domain (Pie Menu)"
    bl_idname = "nd_utils.pie_menu_switch_viewer_domain"
    bl_description = "Updates the domain of Viewer Node in Geometry Nodes"
    bl_options = {'REGISTER'}

    domain_type: EnumProperty(name='domains', items=(
        ('AUTO', 'AUTO', ''), 
        ('POINT', 'POINT', ''), 
        ('EDGE', 'EDGE', ''), 
        ('FACE', 'FACE', ''), 
        ('CORNER', 'CORNER', ''), 
        ('CURVE', 'CURVE', ''), 
        ('INSTANCE', 'INSTANCE', ''), 
        ))

    domain_type: EnumProperty(name='domains', items=(
        ('AUTO', 'AUTO', ''), 
        ('POINT', 'POINT', ''), 
        ('EDGE', 'EDGE', ''), 
        ('FACE', 'FACE', ''), 
        ('CORNER', 'CORNER', ''), 
        ('CURVE', 'CURVE', ''), 
        ('INSTANCE', 'INSTANCE', ''), 
        ))

    geometry_type: EnumProperty(name='geometry_type', items=(
        ('MESH', 'MESH', ''), 
        ('CURVE', 'CURVE', ''), 
        ('POINTCLOUD', 'POINTCLOUD', ''), 
        ('INSTANCES', 'INSTANCES', ''), 
        ))

    def execute(self, context):
        nodes = get_nodes(context)

        for node in nodes:
            if node.bl_static_type != "VIEWER":
                continue
            
            node.domain = self.domain_type
        
        area = None
        for area in bpy.context.screen.areas:
            if area.type == 'SPREADSHEET':
                active_area = area.spaces.active
                active_area.geometry_component_type = self.geometry_type
                active_area.attribute_domain = self.domain_type
                
        return {'FINISHED'}

class NODEUTILS_OT_SWITCH_VIEWER_DOMAIN_INVOKE_MENU(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Switch Viewer Node Domain Options"
    bl_idname = "nd_utils.switch_viewer_domain_invoke_menu"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        is_existing = space.node_tree is not None
        is_node_editor = space.type == 'NODE_EDITOR'
        is_valid = space.tree_type == "GeometryNodeTree"

        nodes = get_nodes(context)
        does_viewer_exist = any(node.bl_static_type == "VIEWER" for node in nodes)

        return all((is_existing, is_node_editor, is_valid, does_viewer_exist))

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="ND_UTILS_MT_switch_viewer_domain_options")
        return {'FINISHED'}
        
        

class NODEUTILS_MT_SWITCH_VIEWER_DOMAIN_OPTIONS(bpy.types.Menu, NodeUtilsBase):
    bl_label = "Switch Viewer Domain"
    bl_idname = "ND_UTILS_MT_switch_viewer_domain_options"

    domains = (
        #('AUTO', "Auto", 'COLLAPSEMENU'), 
        ('POINT', 'MESH', "Vertex", 'VERTEXSEL'), 
        ('EDGE', 'MESH', "Edge", 'MOD_EDGESPLIT'), 
        ('FACE', 'MESH', "Face", 'MOD_SOLIDIFY'), 
        ('CORNER', 'MESH', "Face Corner", 'DRIVER_ROTATIONAL_DIFFERENCE'), 
        ('POINT', 'CURVE', "Control Point", 'CURVE_BEZCURVE'), 
        ('CURVE', 'CURVE', "Spline", 'CURVE_DATA'), 
        ('POINT', 'POINTCLOUD', "Point", 'PARTICLE_POINT'), 
        ('INSTANCE', 'INSTANCES', "Instance", 'EMPTY_AXIS'),
        )
    
    @classmethod
    def poll(cls, context):
        space = context.space_data
        is_existing = space.node_tree is not None
        is_node_editor = space.type == 'NODE_EDITOR'
        is_valid = space.tree_type == "GeometryNodeTree"
        return all((is_existing, is_node_editor, is_valid))
        
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        for domain, geo_type, label, icon in self.domains:
            props = pie.operator("nd_utils.pie_menu_switch_viewer_domain", text=f"{label}", icon=icon)
            props.domain_type = domain
            props.geometry_type = geo_type

class NODEUTILS_OT_STRAIGHTEN_REROUTES(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Straigthen Reroutes"
    bl_idname = "nd_utils.straighten_reroutes"
    bl_description = "Aligns reroute with the node socket they're connected with."

    #TODO - ADD BoolProperty to Select Reroutes after straigthening
    #TODO - ADD EnumProperty to adjust whether reroute x_location is Relative or Absolute
    #TODO - ADD Float Property to adjust how much is the x offset in Absolute Mode

    def execute(self, context):
        header_offset = 20
        first_socket_offset = 15
        socket_gaps = 22

        reroutes = tuple(node for node in get_nodes(context) 
            if node.bl_static_type == "REROUTE")

        valid_input_reroutes = []
        valid_output_reroutes = []

        for reroute in reroutes:
            input_link = reroute.inputs[0].links[0]
            output_link = reroute.outputs[0].links[0]

            #print(reroute.label, input_link.from_node.bl_static_type)
            if input_link.from_node.bl_static_type != "REROUTE":
                if input_link.from_socket.enabled:
                    valid_input_reroutes.append(reroute)
                    continue

            elif output_link.to_node.bl_static_type != "REROUTE":
                if output_link.to_socket.enabled:
                    valid_output_reroutes.append(reroute)

        #print(*(node.label for node in valid_input_reroutes))
        #print(*(node.label for node in valid_output_reroutes))
        #valid_reroutes = tuple(reroute for reroute in reroutes
            #if reroute.inputs[0].links[0].from_node.bl_static_type != "REROUTE")

        old_y_locations = []
        new_y_locations = []

        for node in valid_input_reroutes:
            link = node.inputs[0].links[0]
            from_node = link.from_node
            from_socket = link.from_socket

            socket_id = 0
            for outp in from_node.outputs:
                if outp == from_socket:
                    break
                elif outp.enabled and not outp.hide:
                    socket_id += 1

            y_offset = (header_offset + first_socket_offset + socket_id*(socket_gaps))
            old_y_locations.append(round(node.location.y, 2))
            new_y_locations.append(round(from_node.location.y - y_offset, 2)) 

        #TODO FIX A LOT OF THIS, IT DOESN'T EVEN CONSIDER THE SIZES OF UNOCCUPIED INPUTS YET
        for node in valid_output_reroutes:
            link = node.outputs[0].links[0]
            to_node = link.to_node
            to_socket = link.to_socket

            print(to_node.name, node.label)
            output_count = len(tuple(outp for outp in to_node.outputs if outp.enabled and not outp.hide))
            socket_id = max(output_count, 0)
            for inp in to_node.inputs:
                print(inp.name)
                if inp == to_socket:
                    break
                elif inp.enabled and not inp.hide:
                    socket_id += 1
            print()
            if output_count > 0:
                adjust = 2.5
            else:
                adjust = 0

            y_offset = (header_offset + first_socket_offset + socket_id*(socket_gaps))
            old_y_locations.append(round(node.location.y, 2))
            new_y_locations.append(round(to_node.location.y - y_offset - adjust, 2)) 

        if old_y_locations == new_y_locations:
            return {'CANCELLED'}

        valid_reroutes = valid_input_reroutes + valid_output_reroutes
        for node, y in zip(valid_reroutes, new_y_locations):
            node.location.y = y
        return {'FINISHED'}


def refresh_ui(self, context):
    for region in context.area.regions:
        if region.type == "UI":
            region.tag_redraw()
    return None    

class NodetreeUtilsProperties(bpy.types.PropertyGroup):
    selection_mode: EnumProperty(name='Selection Mode', 
        description='Toggles what mode of selection is used.',
        default='New',
        update=refresh_ui, 
        items=(
        ('New', 'New', 'Creates a new selection out of the specified nodes', 'SELECT_SET', 0),
        ('Add', 'Add', 'Adds specified nodes from current selection', 'SELECT_EXTEND', 1), 
        ('Subtract', 'Subtract', 'Removes specified nodes from current selection', 'SELECT_SUBTRACT', 2), 
        ('Intersection', 'Intersection', 'Only selects nodes shared between specified nodes and current selection','SELECT_INTERSECT', 3),
        ('Invert', 'Invert', 'Flip the selection state of the specified nodes','SELECT_DIFFERENCE', 4),
        ))

classes = (
    NodetreeUtilsProperties,
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_SET_COLOR,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS,
    NODEUTILS_OT_SWITCH_SELECT_TYPE,
    NODEUTILS_OT_SWITCH_VIEWER_DOMAIN,
    NODEUTILS_OT_PIE_MENU_SWITCH_VIEWER_DOMAIN,
    NODEUTILS_MT_SWITCH_VIEWER_DOMAIN_OPTIONS,
    NODEUTILS_OT_SWITCH_VIEWER_DOMAIN_INVOKE_MENU,
    NODEUTILS_OT_STRAIGHTEN_REROUTES,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.WindowManager.nd_utils_props = bpy.props.PointerProperty(type=NodetreeUtilsProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.WindowManager.nd_utils_props 